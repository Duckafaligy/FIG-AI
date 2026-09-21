"""Billing webhook and checkout guard. No network, no real Stripe key.

Every test patches the Stripe settings to dummies, whatever the import order and
whatever is in .env, so nothing in here can reach the live Stripe account even by
accident.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import hashlib
import hmac
import json
import time
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import billing, config
from app.db import get_session
from app.models import Account, Base

SECRET = "whsec_dummy_for_tests"


def dummy_stripe_settings():
    """Patches that replace whatever .env loaded. Returns the started patchers."""
    patchers = [patch.object(config, "STRIPE_SECRET_KEY", "sk_test_dummy_never_used"),
                patch.object(config, "STRIPE_WEBHOOK_SECRET", SECRET),
                patch.object(config, "STRIPE_PRICE_ID", "price_dummy")]
    for p in patchers:
        p.start()
    assert config.STRIPE_SECRET_KEY == "sk_test_dummy_never_used", "tests must never see a real Stripe key"
    return patchers


def event(kind: str, obj: dict) -> tuple[bytes, dict]:
    """A body plus the Stripe-Signature header Stripe would send for it."""
    body = json.dumps({"id": "evt_1", "object": "event", "api_version": "2024-06-20",
                       "created": int(time.time()), "type": kind,
                       "data": {"object": obj}}).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return body, {"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"}


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.patchers = dummy_stripe_settings()
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                    poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="acct", name="Acme", slug="acme", stripe_customer_id="cus_1"))
            db.commit()
        app = FastAPI()
        app.include_router(billing.router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        for p in self.patchers:
            p.stop()

    def send(self, kind, obj, headers=None):
        body, sig = event(kind, obj)
        return self.client.post("/v1/billing/webhook", content=body, headers=headers or sig)

    def sub(self):
        with Session(self.engine) as db:
            return db.get(Account, "acct").stripe_subscription_id

    def sub_obj(self, status, sub_id="sub_1"):
        return {"id": sub_id, "object": "subscription", "customer": "cus_1", "status": status}

    # -- the door ----------------------------------------------------------

    def test_unsigned_and_forged_requests_are_refused(self):
        body, _ = event("customer.subscription.created", self.sub_obj("active"))
        self.assertEqual(self.client.post("/v1/billing/webhook", content=body).status_code, 400)
        forged = {"Stripe-Signature": f"t={int(time.time())},v1={'0' * 64}"}
        self.assertEqual(self.client.post("/v1/billing/webhook", content=body, headers=forged).status_code, 400)
        self.assertIsNone(self.sub())

    def test_a_signed_event_is_accepted(self):
        r = self.send("customer.subscription.created", self.sub_obj("active"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"received": True, "type": "customer.subscription.created"})
        self.assertEqual(self.sub(), "sub_1")

    # -- linking -----------------------------------------------------------

    def test_checkout_completed_links_by_metadata(self):
        self.send("checkout.session.completed", {
            "id": "cs_1", "object": "checkout.session", "mode": "subscription",
            "payment_status": "paid", "subscription": "sub_9",
            "metadata": {"fig_account_id": "acct"}})
        self.assertEqual(self.sub(), "sub_9")

    def test_trial_checkout_with_no_payment_yet_still_links(self):
        self.send("checkout.session.completed", {
            "id": "cs_2", "object": "checkout.session", "mode": "subscription",
            "payment_status": "no_payment_required", "subscription": "sub_t", "customer": "cus_1"})
        self.assertEqual(self.sub(), "sub_t")

    def test_unpaid_or_non_subscription_checkout_links_nothing(self):
        base = {"id": "cs_3", "object": "checkout.session", "subscription": "sub_x",
                "metadata": {"fig_account_id": "acct"}}
        self.send("checkout.session.completed", base | {"mode": "subscription", "payment_status": "unpaid"})
        self.send("checkout.session.completed", base | {"mode": "payment", "payment_status": "paid"})
        self.assertIsNone(self.sub())

    def test_an_unpaid_first_invoice_does_not_grant_access(self):
        self.send("customer.subscription.created", self.sub_obj("incomplete"))
        self.assertIsNone(self.sub())
        self.send("customer.subscription.updated", self.sub_obj("active"))
        self.assertEqual(self.sub(), "sub_1")

    def test_trialing_and_past_due_stay_subscribed(self):
        for status in ("trialing", "past_due"):
            with self.subTest(status=status):
                self.send("customer.subscription.updated", self.sub_obj(status))
                self.assertEqual(self.sub(), "sub_1")

    # -- ending it ---------------------------------------------------------

    def test_deleted_unlinks_and_a_late_update_cannot_relink_it(self):
        self.send("customer.subscription.created", self.sub_obj("active"))
        self.assertEqual(self.sub(), "sub_1")
        self.send("customer.subscription.deleted", self.sub_obj("canceled"))
        self.assertIsNone(self.sub())
        # Stripe may deliver an older event after the deletion. It must not win.
        self.send("customer.subscription.updated", self.sub_obj("canceled"))
        self.assertIsNone(self.sub())

    def test_a_cancelled_status_alone_unlinks_even_without_a_deleted_event(self):
        self.send("customer.subscription.created", self.sub_obj("active"))
        for status in ("canceled", "unpaid", "incomplete_expired"):
            with self.subTest(status=status):
                self.send("customer.subscription.updated", self.sub_obj("active"))
                self.send("customer.subscription.updated", self.sub_obj(status))
                self.assertIsNone(self.sub())

    def test_ending_an_old_subscription_leaves_a_newer_one_alone(self):
        self.send("customer.subscription.created", self.sub_obj("active", "sub_new"))
        self.send("customer.subscription.deleted", self.sub_obj("canceled", "sub_old"))
        self.assertEqual(self.sub(), "sub_new")

    def test_events_for_unknown_customers_change_nothing(self):
        r = self.send("customer.subscription.created",
                      {"id": "sub_z", "object": "subscription", "customer": "cus_nobody", "status": "active"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(self.sub())

    def test_unhandled_event_types_are_acknowledged(self):
        r = self.send("invoice.paid", {"id": "in_1", "object": "invoice", "customer": "cus_1"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(self.sub())


class CheckoutGuardTests(unittest.TestCase):
    def setUp(self):
        self.patchers = dummy_stripe_settings()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_a_subscribed_workspace_cannot_open_a_second_subscription(self):
        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            account = Account(id="acct", name="Acme", slug="acme", stripe_subscription_id="sub_live")
            db.add(account)
            db.commit()
            # The guard fires before any Stripe call, so no key or network is needed.
            with self.assertRaises(HTTPException) as caught:
                billing.start_checkout(db, account)
            self.assertEqual(caught.exception.status_code, 409)
            self.assertIn("portal", caught.exception.detail)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
