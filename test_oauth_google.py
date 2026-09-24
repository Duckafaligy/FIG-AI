"""Google OAuth connect flow: no network, no real Google app.

Closes a real pre-existing gap -- every other OAuth platform in app/oauth.py
(Shopify, Webflow, Wix, GitHub) had its own dedicated fake-network test file;
Google, the first one built, never got one. Written now because this same
flow just changed shape (2026-09-23): Google moved from site_id-scoped to
account_id-scoped (one workspace connection, not one per project -- see
Integration's docstring in app/models.py), so /start no longer takes a
site_id at all and /callback resolves an Account directly instead of a Site.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, oauth
from app.db import get_session
from app.models import Account, Base, Integration, Site
from app.secrets_store import read_secret

CLIENT_ID = "test-google-client-id"
CLIENT_SECRET = "test-google-client-secret"
REDIRECT_URI = "https://fig-ai-backend.onrender.com/oauth/google/callback"


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class GoogleOAuthTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "GOOGLE_CLIENT_ID", CLIENT_ID),
            patch.object(config, "GOOGLE_CLIENT_SECRET", CLIENT_SECRET),
            patch.object(config, "GOOGLE_OAUTH_REDIRECT_URI", REDIRECT_URI),
            patch.object(config, "GOOGLE_OAUTH_ENABLED", True),
            patch.object(config, "SESSION_SECRET", "test-session-secret-not-real"),
        ]
        for p in self.patches:
            p.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.add(Account(id="b", name="B", slug="b"))
            db.add(Site(id="site-a1", account_id="a", hostname="one.example"))
            db.add(Site(id="site-a2", account_id="a", hostname="two.example"))
            db.commit()
        app = FastAPI()
        app.include_router(oauth.router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.oauth.current_account",
                          side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account"))
                          if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.client = TestClient(app, follow_redirects=False)

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        for p in self.patches:
            p.stop()
        self.engine.dispose()

    def start(self, account="a"):
        return self.client.get("/oauth/google/start",
                               headers={"x-test-account": account} if account else {})

    def state_from(self, start_response) -> str:
        return parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    # -- /start ------------------------------------------------------------

    def test_not_signed_in_is_401(self):
        self.assertEqual(self.start(account=None).status_code, 401)

    def test_not_configured_is_503(self):
        with patch.object(config, "GOOGLE_OAUTH_ENABLED", False):
            self.assertEqual(self.start().status_code, 503)

    def test_start_takes_no_site_id_and_carries_only_the_account(self):
        """The real behavior change: /start used to require a site_id (whose
        site had to belong to the caller); it no longer takes one at all."""
        r = self.start()
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(loc.netloc, "accounts.google.com")
        q = parse_qs(loc.query)
        self.assertEqual(q["client_id"][0], CLIENT_ID)
        self.assertEqual(q["redirect_uri"][0], REDIRECT_URI)
        self.assertIn("analytics.readonly", q["scope"][0])
        self.assertIn("webmasters.readonly", q["scope"][0])
        self.assertNotIn("site_id", q)

    # -- /callback -----------------------------------------------------

    def test_a_correctly_signed_callback_connects_the_account_not_a_site(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {
                "access_token": "ya29.real-token", "refresh_token": "1//real-refresh",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/analytics.readonly "
                        "https://www.googleapis.com/auth/webmasters.readonly",
            })
            r = self.client.get("/oauth/google/callback", params={"code": "a-real-code", "state": state})
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            rows = db.scalars(select(Integration)).all()
            self.assertEqual(len(rows), 2)
            for integ in rows:
                self.assertIn(integ.platform, ("google_analytics", "google_search_console"))
                self.assertEqual(integ.account_id, "a")
                self.assertIsNone(integ.site_id)          # account-scoped, not tied to either site
                self.assertIsNotNone(integ.connected_at)
                creds = read_secret(db, integ.credential_ref)
                self.assertEqual(creds["refresh_token"], "1//real-refresh")

    def test_only_the_scope_google_actually_granted_is_connected(self):
        """Analytics only, no Search Console -- proves the two Integration
        rows are independent, not all-or-nothing."""
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {
                "access_token": "ya29.real-token", "refresh_token": "1//real-refresh",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/analytics.readonly",
            })
            self.client.get("/oauth/google/callback", params={"code": "c", "state": state})
        with Session(self.engine) as db:
            rows = db.scalars(select(Integration)).all()
            self.assertEqual([r.platform for r in rows], ["google_analytics"])

    def test_a_stolen_or_replayed_state_resolves_to_its_own_signed_account(self):
        """A state token signed for account a, replayed by account b, must
        still only ever connect account a -- there's no code path here for
        "whichever account presents the state," mirroring Shopify's and
        Webflow's equivalent tests."""
        state = self.state_from(self.start(account="a"))
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {
                "access_token": "tok", "refresh_token": "1//tok",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/analytics.readonly",
            })
            self.client.get("/oauth/google/callback", params={"code": "c", "state": state},
                            headers={"x-test-account": "b"})
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration)).one()
            self.assertEqual(integ.account_id, "a")

    def test_a_tampered_state_is_rejected(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/google/callback",
                                params={"code": "c", "state": state + "x"})
        post.assert_not_called()
        self.assertIn("invalid_state", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_google_reports_an_error_and_nothing_is_stored(self):
        r = self.client.get("/oauth/google/callback", params={"error": "access_denied"})
        self.assertIn("error=access_denied", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_reconnecting_replaces_the_stored_token_rather_than_duplicating_the_row(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {
                "access_token": "first", "refresh_token": "1//first",
                "expires_in": 3600, "scope": "https://www.googleapis.com/auth/analytics.readonly",
            })
            self.client.get("/oauth/google/callback", params={"code": "c1", "state": state})

        state2 = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {
                "access_token": "second", "refresh_token": "1//second",
                "expires_in": 3600, "scope": "https://www.googleapis.com/auth/analytics.readonly",
            })
            self.client.get("/oauth/google/callback", params={"code": "c2", "state": state2})

        with Session(self.engine) as db:
            rows = db.scalars(select(Integration)).all()
            self.assertEqual(len(rows), 1)              # replaced, not duplicated
            creds = read_secret(db, rows[0].credential_ref)
            self.assertEqual(creds["refresh_token"], "1//second")


if __name__ == "__main__":
    unittest.main()
