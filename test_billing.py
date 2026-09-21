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


class FakeStripe:
    """Just enough of the stripe module for sync_quantity: records every change."""

    def __init__(self, quantity=1, fail=False):
        self.calls, self.quantity, self.fail = [], quantity, fail
        outer = self

        class Subscription:
            @staticmethod
            def retrieve(sub_id):
                if outer.fail:
                    raise RuntimeError("stripe is down")
                return {"items": {"data": [{"id": "si_1", "quantity": outer.quantity}]}}

            @staticmethod
            def modify(sub_id, **kw):
                outer.calls.append((sub_id, kw))
                outer.quantity = kw["items"][0]["quantity"]
        self.Subscription = Subscription

    def quantities(self):
        return [kw["items"][0]["quantity"] for _, kw in self.calls]


class QuantitySyncTests(unittest.TestCase):
    """The subscription is billed per active site, so adding or removing a site
    has to move its quantity. Before this nothing did: a customer who added ten
    sites after subscribing was never billed for them, and one who removed sites
    was never credited."""

    def setUp(self):
        from unittest.mock import patch as _patch
        self.patchers = dummy_stripe_settings()
        self.patchers.append(_patch.object(config, "BILLING_ENABLED", True))
        self.patchers[-1].start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a", stripe_subscription_id="sub_1", site_floor=0))
            db.commit()

        from app.webapp import router as workspace
        app = FastAPI()
        app.include_router(workspace)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        for target, value in (
                ("app.webapp.current_account", lambda request, db: db.get(Account, "a")),
                ("app.webapp.public_hostname", lambda raw: raw.strip().lower())):
            p = patch(target, side_effect=value)
            p.start()
            self.patchers.append(p)
        self.fake = FakeStripe(quantity=1)
        p = patch.object(billing, "_stripe", return_value=self.fake)
        p.start()
        self.patchers.append(p)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        for p in self.patchers:
            p.stop()

    def add(self, host):
        return self.client.post("/api/projects", json={"hostname": host})

    def test_adding_sites_raises_the_subscription_quantity(self):
        self.assertEqual(self.add("one.example").status_code, 200)
        self.assertEqual(self.add("two.example").status_code, 200)
        self.assertEqual(self.add("three.example").status_code, 200)
        self.assertEqual(self.fake.quantities(), [2, 3])      # 1 was already in step
        self.assertEqual(self.fake.quantity, 3)

    def test_removing_a_site_lowers_it_again(self):
        ids = [self.add(h).json()["id"] for h in ("one.example", "two.example", "three.example")]
        self.assertEqual(self.fake.quantity, 3)
        self.assertEqual(self.client.delete("/api/projects/" + ids[0]).status_code, 200)
        self.assertEqual(self.fake.quantity, 2)

    def test_no_subscription_means_no_stripe_call(self):
        with Session(self.engine) as db:
            db.get(Account, "a").stripe_subscription_id = None
            db.commit()
        self.assertEqual(self.add("one.example").status_code, 200)
        self.assertEqual(self.fake.calls, [])

    def test_a_stripe_outage_does_not_break_adding_a_site(self):
        self.fake.fail = True
        r = self.add("one.example")
        self.assertEqual(r.status_code, 200)                   # the site is saved regardless
        self.assertEqual(self.client.get("/api/projects").status_code, 200)

    def test_the_partner_api_syncs_too(self):
        from app.api import router as partner
        from app.auth import require_account
        app = FastAPI()
        app.include_router(partner)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        def account():
            # A fresh session per request, as in production; a long-lived one
            # would hold a stale site list and misreport the count.
            with Session(self.engine) as db:
                yield db.get(Account, "a")
        app.dependency_overrides[require_account] = account
        with patch("app.api.public_hostname", side_effect=lambda raw: raw.strip().lower()):
            client = TestClient(app)
            made = client.post("/v1/sites", json={"hostname": "partner-one.example"})
            self.assertEqual(made.status_code, 201)
            self.assertEqual(self.fake.quantity, 1)
            made2 = client.post("/v1/sites", json={"hostname": "partner-two.example"})
            self.assertEqual(self.fake.quantity, 2)
            client.delete("/v1/sites/" + made2.json()["id"])
            self.assertEqual(self.fake.quantity, 1)


if __name__ == "__main__":
    unittest.main()
