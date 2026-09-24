"""Deleting a workspace, ending sessions after a password reset, and retention.

All in-memory, no network. Stripe and Supabase are faked, and the Stripe settings
are patched to dummies so nothing here can reach the live account.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from app import account_data, billing, config, retention
from app.db import get_session
from app.models import (Account, ApiKey, Base, Change, ContentPost, Finding, Integration,
                        Page, PublicRead, Scan, Secret, Site, User)
from app.secrets_store import store_secret
from app.webapp import router


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


class Fixture(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "STRIPE_SECRET_KEY", "sk_test_dummy_never_used"),
            patch.object(config, "BILLING_ENABLED", True),
        ]
        for p in self.patches:
            p.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            self.populate(db, "a", "a@example.com", subscription="sub_a")
            self.populate(db, "b", "b@example.com")
            demo = Account(id="demo", name="Demo", slug=config.DEMO_ACCOUNT_SLUG)
            db.add(demo)
            db.commit()

    def populate(self, db, key, email, subscription=None):
        db.add(Account(id=key, name=f"Workspace {key}", slug=f"ws-{key}", contact_email=email,
                       stripe_subscription_id=subscription))
        db.flush()
        db.add(User(id=f"user-{key}", account_id=key, email=email, supabase_uid=f"uid-{key}", role="owner"))
        site = Site(id=f"site-{key}", account_id=key, hostname=f"{key}.example")
        db.add(site)
        db.flush()
        scan = Scan(id=f"scan-{key}", site_id=site.id, status="done", trigger="manual")
        db.add(scan)
        db.flush()
        db.add(Page(scan_id=scan.id, url=f"https://{key}.example/"))
        finding = Finding(id=f"finding-{key}", scan_id=scan.id, check="x", layer="craft", severity="low", summary="s")
        db.add(finding)
        db.add(ContentPost(site_id=site.id, title="Draft", slug="draft", state="queued"))
        db.add(Change(site_id=site.id, finding_id=finding.id, kind="heading", layer="craft",
                      title="Fix", before="a", after="b", state="proposed"))
        ref = store_secret(db, {"refresh_token": f"secret-{key}"})
        db.add(Integration(site_id=site.id, platform="google_analytics", credential_ref=ref))
        db.add(ApiKey(account_id=key, prefix=f"fig_live_{key}", key_hash=f"hash-{key}", label="k"))
        db.commit()

    def tearDown(self):
        self.engine.dispose()
        for p in self.patches:
            p.stop()


class FakeStripe:
    def __init__(self, status="active", fail=False, missing=False):
        self.cancelled, self.status, self.fail, self.missing = [], status, fail, missing
        outer = self

        class Missing(Exception):
            code = "resource_missing"

        class Subscription:
            @staticmethod
            def retrieve(sub_id):
                if outer.missing:
                    raise Missing("no such subscription")
                if outer.fail:
                    raise RuntimeError("stripe is down")
                return {"status": outer.status}

            @staticmethod
            def cancel(sub_id):
                outer.cancelled.append(sub_id)
        self.Subscription = Subscription


class DeleteWorkspaceTests(Fixture):
    def delete(self, key="a", confirm=None, stripe=None):
        stripe = stripe or FakeStripe()
        with Session(self.engine) as db, \
                patch.object(billing, "_stripe", return_value=stripe), \
                patch.object(account_data, "delete_auth_user", return_value=True) as auth:
            account, user = db.get(Account, key), db.get(User, f"user-{key}")
            result = account_data.delete_workspace(db, account, user, confirm=confirm or user.email)
        return result, stripe, auth

    def test_everything_in_the_workspace_goes_and_nothing_else(self):
        result, stripe, auth = self.delete("a")
        self.assertTrue(result["deleted"])
        self.assertEqual(stripe.cancelled, ["sub_a"])
        auth.assert_called_once_with("uid-a")
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Account, "a"))
            self.assertEqual(count(db, Site), 1)                      # only b's remains
            self.assertEqual(count(db, Scan), 1)
            self.assertEqual(count(db, Page), 1)
            self.assertEqual(count(db, Finding), 1)
            self.assertEqual(count(db, ContentPost), 1)
            self.assertEqual(count(db, Change), 1)
            self.assertEqual(count(db, Integration), 1)
            self.assertEqual(count(db, ApiKey), 1)
            self.assertEqual(count(db, User), 1)
            self.assertEqual(count(db, Secret), 1)                    # a's credential is gone too
            self.assertIsNotNone(db.get(Account, "b"))
            self.assertIsNotNone(db.get(Account, "demo"))

    def test_the_stored_credential_is_deleted_with_the_integration(self):
        with Session(self.engine) as db:
            self.assertEqual(count(db, Secret), 2)
        self.delete("a")
        with Session(self.engine) as db:
            remaining = db.scalars(select(Integration)).all()
            self.assertEqual([i.site_id for i in remaining], ["site-b"])
            self.assertEqual(count(db, Secret), 1)

    def test_an_account_scoped_integration_and_its_credential_are_also_deleted(self):
        """Google Analytics/Search Console are account_id-scoped, not
        site_id-scoped (2026-09-23) -- the site_ids-only cleanup above would
        never reach these, leaking the stored token the same way disconnect()
        once did for the site-scoped kind."""
        with Session(self.engine) as db:
            ref = store_secret(db, {"refresh_token": "account-level-secret"})
            db.add(Integration(account_id="a", platform="google_analytics", credential_ref=ref))
            db.commit()
            self.assertEqual(count(db, Secret), 3)
        self.delete("a")
        with Session(self.engine) as db:
            remaining = db.scalars(select(Integration)).all()
            self.assertEqual([(i.site_id, i.account_id) for i in remaining], [("site-b", None)])
            self.assertEqual(count(db, Secret), 1)

    def test_a_wrong_confirmation_deletes_nothing_and_does_not_touch_stripe(self):
        stripe = FakeStripe()
        with self.assertRaises(account_data.DeletionRefused) as caught:
            self.delete("a", confirm="not my email", stripe=stripe)
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(stripe.cancelled, [])
        with Session(self.engine) as db:
            self.assertIsNotNone(db.get(Account, "a"))
            self.assertEqual(count(db, Site), 2)

    def test_the_confirmation_ignores_case_and_whitespace(self):
        self.delete("a", confirm="  A@Example.COM ")
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Account, "a"))

    def test_the_demo_workspace_cannot_be_deleted(self):
        with Session(self.engine) as db:
            db.add(User(id="user-demo", account_id="demo", email="d@example.com", role="owner"))
            db.commit()
        with self.assertRaises(account_data.DeletionRefused) as caught:
            self.delete("demo", confirm="d@example.com")
        self.assertEqual(caught.exception.status, 403)

    def test_a_workspace_with_other_members_is_refused(self):
        with Session(self.engine) as db:
            db.add(User(id="user-a2", account_id="a", email="second@example.com", role="member"))
            db.commit()
        with self.assertRaises(account_data.DeletionRefused):
            self.delete("a")

    def test_only_the_owner_can_delete(self):
        with Session(self.engine) as db:
            db.get(User, "user-a").role = "member"
            db.commit()
        with self.assertRaises(account_data.DeletionRefused) as caught:
            self.delete("a")
        self.assertEqual(caught.exception.status, 403)

    def test_a_person_cannot_delete_someone_elses_workspace(self):
        with Session(self.engine) as db, patch.object(billing, "_stripe", return_value=FakeStripe()):
            with self.assertRaises(account_data.DeletionRefused):
                account_data.delete_workspace(db, db.get(Account, "a"), db.get(User, "user-b"), confirm="b@example.com")
            self.assertIsNotNone(db.get(Account, "a"))

    def test_if_stripe_will_not_cancel_nothing_is_deleted(self):
        with self.assertRaises(account_data.DeletionRefused) as caught:
            self.delete("a", stripe=FakeStripe(fail=True))
        self.assertEqual(caught.exception.status, 502)
        with Session(self.engine) as db:
            self.assertIsNotNone(db.get(Account, "a"))
            self.assertEqual(db.get(Account, "a").stripe_subscription_id, "sub_a")
            self.assertEqual(count(db, Site), 2)

    def test_an_already_cancelled_or_missing_subscription_does_not_block_deletion(self):
        for stripe in (FakeStripe(status="canceled"), FakeStripe(missing=True)):
            self.setUp()          # fresh data each time
            result, fake, _ = self.delete("a", stripe=stripe)
            self.assertTrue(result["deleted"])
            self.assertEqual(fake.cancelled, [])                     # nothing left to cancel

    def test_a_workspace_with_no_subscription_needs_no_stripe(self):
        result, stripe, _ = self.delete("b")
        self.assertTrue(result["deleted"])
        self.assertFalse(result["subscription_cancelled"])
        self.assertEqual(stripe.cancelled, [])

    def test_the_sign_in_record_is_reported_honestly(self):
        with Session(self.engine) as db, patch.object(billing, "_stripe", return_value=FakeStripe()), \
                patch.object(account_data, "delete_auth_user", return_value=False):
            result = account_data.delete_workspace(db, db.get(Account, "b"), db.get(User, "user-b"), confirm="b@example.com")
        self.assertTrue(result["deleted"])
        self.assertFalse(result["sign_in_record_deleted"])

    def test_no_supabase_key_means_the_record_is_left_not_an_error(self):
        with patch.object(config, "SUPABASE_SERVICE_ROLE_KEY", ""):
            self.assertFalse(account_data.delete_auth_user("uid-x"))


class SessionTests(Fixture):
    """Real cookies through the real router, with Supabase's token check faked."""

    def setUp(self):
        super().setUp()
        with Session(self.engine) as db:
            self.user_supabase_id = "uid-a"
        app = FastAPI()
        app.add_middleware(SessionMiddleware, secret_key="test-secret", session_cookie="fig_session")
        app.include_router(router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.app = app
        def fake_verify(token):
            # Mirrors the real function: it RAISES 401 for a bad token, it does not return None.
            if token == "good":
                return {"id": "uid-a", "email": "a@example.com"}
            raise HTTPException(401, "that sign-in could not be verified")
        self.verify = patch("app.auth.verify_access_token", new=AsyncMock(side_effect=fake_verify))
        self.verify.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.verify.stop()
        self.client.close()
        super().tearDown()

    def sign_in(self, client=None):
        return (client or self.client).post("/api/session", json={"access_token": "good"})

    def me(self, client=None):
        return (client or self.client).get("/api/me").json().get("signed_in")

    def test_signing_in_works_and_the_session_survives(self):
        self.assertEqual(self.sign_in().status_code, 200)
        self.assertTrue(self.me())

    def test_revoking_signs_out_every_device_but_not_the_next_sign_in(self):
        self.sign_in()
        laptop = self.client
        phone = TestClient(self.app)
        self.sign_in(phone)
        self.assertTrue(self.me(laptop) and self.me(phone))
        r = TestClient(self.app).post("/api/session/revoke", json={"access_token": "good"})   # from the reset page
        self.assertEqual(r.json(), {"ok": True})
        self.assertFalse(self.me(laptop))
        self.assertFalse(self.me(phone))
        self.sign_in(laptop)                                   # signing in again works...
        self.assertTrue(self.me(laptop))
        self.assertFalse(self.me(phone))                       # ...and does not revive the other one
        phone.close()

    def test_a_replayed_old_cookie_stays_dead_after_a_new_sign_in(self):
        self.sign_in()
        stolen = dict(self.client.cookies)
        self.client.post("/api/session/revoke", json={"access_token": "good"})
        self.sign_in()
        attacker = TestClient(self.app, cookies=stolen)
        self.assertFalse(self.me(attacker))
        attacker.close()

    def test_a_bad_token_revokes_nothing_and_answers_the_same(self):
        self.sign_in()
        r = self.client.post("/api/session/revoke", json={"access_token": "forged"})
        self.assertEqual(r.json(), {"ok": True})
        self.assertTrue(self.me())
        self.assertEqual(self.client.post("/api/session/revoke", json={}).json(), {"ok": True})

    def test_revoking_one_person_does_not_sign_out_another(self):
        other = TestClient(self.app)
        with patch("app.auth.verify_access_token", new=AsyncMock(return_value={"id": "uid-b", "email": "b@example.com"})):
            other.post("/api/session", json={"access_token": "x"})
        self.sign_in()
        self.client.post("/api/session/revoke", json={"access_token": "good"})
        self.assertFalse(self.me())
        self.assertTrue(self.me(other))
        other.close()

    def test_sessions_issued_before_epochs_existed_keep_working(self):
        """Deploying this must not sign everyone out: an old cookie carries no epoch."""
        from itsdangerous import TimestampSigner
        import base64, json
        payload = base64.b64encode(json.dumps({"uid": "user-a"}).encode())      # old format: no "ep"
        cookie = TimestampSigner("test-secret").sign(payload).decode()
        client = TestClient(self.app, cookies={"fig_session": cookie})
        self.assertTrue(self.me(client))
        client.close()

    def test_deleting_the_account_through_the_api_ends_the_session(self):
        self.sign_in()
        with patch.object(billing, "_stripe", return_value=FakeStripe()), \
                patch.object(account_data, "delete_auth_user", return_value=True):
            wrong = self.client.post("/api/account/delete", json={"confirm": "nope"})
            self.assertEqual(wrong.status_code, 422)
            self.assertTrue(self.me())                                       # still signed in, nothing deleted
            ok = self.client.post("/api/account/delete", json={"confirm": "a@example.com"})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["deleted"])
        self.assertFalse(self.me())
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Account, "a"))
            self.assertIsNotNone(db.get(Account, "b"))

    def test_deleting_requires_signing_in(self):
        r = TestClient(self.app).post("/api/account/delete", json={"confirm": "a@example.com"})
        self.assertEqual(r.status_code, 401)


class RetentionTests(Fixture):
    def make(self, db, days_old, ip="iphash", dev="devhash", hostname="x.example"):
        db.add(PublicRead(scan_id="scan-a", hostname=hostname, device_hash=dev, ip_hash=ip,
                          created_at=(datetime.now(timezone.utc) - timedelta(days=days_old)).replace(tzinfo=None)))

    def test_old_identifiers_are_blanked_and_recent_ones_kept(self):
        with Session(self.engine) as db:
            self.make(db, 45, hostname="old.example")
            self.make(db, 3, hostname="new.example")
            db.commit()

        @__import__("contextlib").contextmanager
        def scope():
            with Session(self.engine) as db:
                yield db
                db.commit()
        with patch.object(retention, "session_scope", scope):
            self.assertEqual(retention.purge_identifiers(), 1)
            self.assertEqual(retention.purge_identifiers(), 0)               # idempotent
        with Session(self.engine) as db:
            rows = {r.hostname: r for r in db.scalars(select(PublicRead))}
            self.assertEqual((rows["old.example"].device_hash, rows["old.example"].ip_hash), ("", ""))
            self.assertEqual((rows["new.example"].device_hash, rows["new.example"].ip_hash), ("devhash", "iphash"))
            self.assertEqual(len(rows), 2)                                    # the public result itself is untouched


class MigrationTests(unittest.TestCase):
    def test_the_session_epoch_column_is_added_to_an_existing_database(self):
        """Production has a `users` table without the column. The backend must add it
        at startup without touching existing rows, or every request that loads a user fails."""
        from sqlalchemy import inspect, text
        from app import db as app_db
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users (id VARCHAR PRIMARY KEY, account_id VARCHAR, email VARCHAR NOT NULL, "
                              "supabase_uid VARCHAR, role VARCHAR NOT NULL DEFAULT 'owner', created_at DATETIME)"))
            conn.execute(text("INSERT INTO users (id, email) VALUES ('existing', 'old@example.com')"))
        with patch.object(app_db, "engine", engine):
            app_db._add_missing_columns()
            app_db._add_missing_columns()                       # idempotent
        self.assertIn("session_epoch", {c["name"] for c in inspect(engine).get_columns("users")})
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT session_epoch FROM users WHERE id='existing'")).scalar(), 0)
        with Session(engine) as session:
            user = session.get(User, "existing")
            self.assertEqual(user.session_epoch, 0)             # the ORM reads the old row fine
        engine.dispose()

    def test_the_integrations_account_id_column_is_added_to_an_existing_database(self):
        """Production predates account_id-scoped integrations (2026-09-23,
        Google Analytics/Search Console moving off site_id) -- same story as
        the columns above."""
        from sqlalchemy import inspect, text
        from app import db as app_db
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE integrations (id VARCHAR PRIMARY KEY, "
                              "site_id VARCHAR NOT NULL, platform VARCHAR NOT NULL, endpoint VARCHAR, "
                              "credential_ref VARCHAR, credential_hint VARCHAR, "
                              "auto_publish BOOLEAN NOT NULL DEFAULT 0, scopes JSON, "
                              "connected_at DATETIME, last_publish_at DATETIME, last_error TEXT, "
                              "created_at DATETIME)"))
            conn.execute(text("INSERT INTO integrations (id, site_id, platform) VALUES ('existing', 'site-1', 'wordpress')"))
        with patch.object(app_db, "engine", engine):
            app_db._add_missing_columns()
            app_db._add_missing_columns()                       # idempotent
        self.assertIn("account_id", {c["name"] for c in inspect(engine).get_columns("integrations")})
        with Session(engine) as session:
            integ = session.get(Integration, "existing")
            self.assertIsNone(integ.account_id)                 # the ORM reads the old row fine

    def test_relaxing_site_id_not_null_is_skipped_on_sqlite_not_attempted(self):
        """SQLite has no ALTER COLUMN at all -- if the dialect gate in
        _relax_not_null_columns() were ever removed, this would raise
        (SQLite rejects the syntax outright) instead of quietly doing
        nothing, so a real sqlite engine (every test in this file, and every
        local/dev run) proves the gate rather than assuming it."""
        from sqlalchemy import inspect, text
        from app import db as app_db
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE integrations (id VARCHAR PRIMARY KEY, "
                              "site_id VARCHAR NOT NULL, platform VARCHAR NOT NULL)"))
        with patch.object(app_db, "engine", engine):
            app_db._relax_not_null_columns()                    # must not raise
        self.assertFalse(inspect(engine).get_columns("integrations")[1]["nullable"])

    def test_relaxing_site_id_not_null_runs_on_postgres(self):
        """The real target: a Postgres engine gets the ALTER, run
        idempotently (the gate re-checks nullability so a second call is a
        no-op) -- verified against the actual SQL text this emits, not just
        that some function ran, since no real Postgres is reachable here."""
        from unittest.mock import MagicMock
        from app import db as app_db
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            from sqlalchemy import text as sql_text
            conn.execute(sql_text("CREATE TABLE integrations (id VARCHAR PRIMARY KEY, "
                                  "site_id VARCHAR NOT NULL, platform VARCHAR NOT NULL)"))
        object.__setattr__(engine.dialect, "name", "postgresql")
        executed = []
        fake_conn = MagicMock()
        fake_conn.execute.side_effect = lambda stmt: executed.append(str(stmt))
        fake_begin = MagicMock()
        fake_begin.__enter__.return_value = fake_conn
        fake_begin.__exit__.return_value = False
        with patch.object(app_db, "engine", engine), \
                patch.object(engine, "begin", return_value=fake_begin):
            app_db._relax_not_null_columns()
        self.assertEqual(len(executed), 1)
        self.assertIn("ALTER TABLE integrations ALTER COLUMN site_id DROP NOT NULL", executed[0])

    def test_the_js_dependent_columns_are_added_to_an_existing_database(self):
        """Same story for `pages`: production predates js_dependent/
        js_dependent_reason, added when the JS-dependency signal was built."""
        from sqlalchemy import inspect, text
        from app import db as app_db
        from app.models import Page
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE pages (id VARCHAR PRIMARY KEY, scan_id VARCHAR NOT NULL, "
                              "url VARCHAR NOT NULL, path VARCHAR NOT NULL DEFAULT '/', title VARCHAR, "
                              "status_code INTEGER, word_count INTEGER NOT NULL DEFAULT 0, "
                              "section_roles JSON, fetched_at DATETIME)"))
            conn.execute(text("INSERT INTO pages (id, scan_id, url) VALUES ('existing', 'scan-1', 'https://a.example/')"))
        with patch.object(app_db, "engine", engine):
            app_db._add_missing_columns()
            app_db._add_missing_columns()
        columns = {c["name"] for c in inspect(engine).get_columns("pages")}
        self.assertIn("js_dependent", columns)
        self.assertIn("js_dependent_reason", columns)
        with Session(engine) as session:
            page = session.get(Page, "existing")
            self.assertFalse(page.js_dependent)
            self.assertIsNone(page.js_dependent_reason)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
