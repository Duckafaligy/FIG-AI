"""Webflow OAuth connect flow: no network, no real Webflow app.

Only the CONNECT step is real -- same limitation as Shopify (app/oauth.py's
docstring: no live site to verify a write adapter against). Shaped like
Google, not Shopify: one fixed authorize URL, state is the only CSRF check
(no extra callback signature the way Shopify's HMAC is).
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
from app.models import Account, Base, Integration, Secret, Site
from app.secrets_store import read_secret

CLIENT_ID = "webflow-test-client-id"
CLIENT_SECRET = "test-webflow-client-secret"
REDIRECT_URI = "https://fig-ai-backend.onrender.com/oauth/webflow/callback"


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class WebflowOAuthTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "WEBFLOW_CLIENT_ID", CLIENT_ID),
            patch.object(config, "WEBFLOW_CLIENT_SECRET", CLIENT_SECRET),
            patch.object(config, "WEBFLOW_OAUTH_REDIRECT_URI", REDIRECT_URI),
            patch.object(config, "WEBFLOW_OAUTH_ENABLED", True),
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
            db.add(Site(id="site-a", account_id="a", hostname="a.example"))
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

    def start(self, site_id="site-a", account="a"):
        return self.client.get("/oauth/webflow/start", params={"site_id": site_id},
                               headers={"x-test-account": account} if account else {})

    def state_from(self, start_response) -> str:
        return parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    # -- /start --------------------------------------------------------

    def test_not_signed_in_is_401(self):
        self.assertEqual(self.start(account=None).status_code, 401)

    def test_someone_elses_site_is_404(self):
        self.assertEqual(self.start(account="b").status_code, 404)

    def test_not_configured_is_503(self):
        with patch.object(config, "WEBFLOW_OAUTH_ENABLED", False):
            self.assertEqual(self.start().status_code, 503)

    def test_redirects_to_webflows_one_fixed_authorize_url(self):
        r = self.start()
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(f"{loc.scheme}://{loc.netloc}{loc.path}", "https://webflow.com/oauth/authorize")
        q = parse_qs(loc.query)
        self.assertEqual(q["client_id"][0], CLIENT_ID)
        self.assertEqual(q["redirect_uri"][0], REDIRECT_URI)
        self.assertEqual(q["response_type"][0], "code")
        self.assertIn("cms:read", q["scope"][0])

    # -- /callback -------------------------------------------------------

    def test_a_successful_callback_connects_and_stores_the_token(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_real_token", "scope": "cms:read cms:write"})
            get.return_value = FakeResp(200, {"sites": [{"id": "wf-site-123", "displayName": "My Site"}]})
            r = self.client.get("/oauth/webflow/callback", params={"code": "a-real-looking-code", "state": state})
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        self.assertTrue(r.headers["location"].startswith(f"{config.FRONTEND_URL}/projects/site-a/settings?"))  # lands back on the connected project's own settings page
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(integ.platform, "webflow")
            self.assertIsNotNone(integ.connected_at)
            self.assertEqual(integ.endpoint, "wf-site-123")
            creds = read_secret(db, integ.credential_ref)
            self.assertEqual(creds["access_token"], "wf_real_token")

    def test_site_discovery_failing_does_not_block_the_connection(self):
        """A real access token was still granted; not knowing which site it
        reaches yet shouldn't undo that -- the write adapter refuses on its
        own later if endpoint never gets filled in, same as any other
        not-fully-configured integration."""
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_real_token", "scope": "cms:read"})
            get.return_value = FakeResp(500, {})
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertIsNone(integ.endpoint)

    def test_the_provider_denying_consent_is_reported_not_hidden(self):
        r = self.client.get("/oauth/webflow/callback", params={"error": "access_denied", "state": "irrelevant"})
        self.assertIn("access_denied", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_an_expired_state_is_rejected(self):
        state = self.state_from(self.start())
        with patch.object(oauth, "STATE_MAX_AGE", -1):
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("expired_state", r.headers["location"])

    def test_a_forged_state_signed_with_the_wrong_secret_is_rejected(self):
        from itsdangerous import URLSafeTimedSerializer
        forged = URLSafeTimedSerializer("not-the-real-session-secret", salt="fig-oauth-state") \
            .dumps({"site_id": "site-a", "account_id": "a"})
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": forged})
        post.assert_not_called()
        self.assertIn("invalid_state", r.headers["location"])

    def test_a_state_for_a_site_that_no_longer_exists_is_rejected(self):
        state = self.state_from(self.start())
        with Session(self.engine) as db:
            db.query(Site).filter(Site.id == "site-a").delete()
            db.commit()
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        post.assert_not_called()
        self.assertIn("site_not_found", r.headers["location"])

    def test_webflow_rejecting_the_code_does_not_connect_anything(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(401, {"error": "invalid_grant"})
            r = self.client.get("/oauth/webflow/callback", params={"code": "bad-code", "state": state})
        self.assertIn("token_exchange_failed", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_network_failure_reaching_webflow_is_reported_not_raised(self):
        import httpx
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post", side_effect=httpx.ConnectError("boom")):
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("token_request_failed", r.headers["location"])

    def test_reconnecting_replaces_rather_than_accumulates_secrets(self):
        state1 = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_first", "scope": "cms:read"})
            get.return_value = FakeResp(200, {"sites": [{"id": "wf-site-123"}]})
            self.client.get("/oauth/webflow/callback", params={"code": "code-1", "state": state1})
        state2 = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_second", "scope": "cms:read cms:write"})
            get.return_value = FakeResp(200, {"sites": [{"id": "wf-site-123"}]})
            self.client.get("/oauth/webflow/callback", params={"code": "code-2", "state": state2})
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 1)
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(read_secret(db, integ.credential_ref)["access_token"], "wf_second")

    def test_a_site_owned_by_someone_else_cannot_be_connected_by_replaying_a_stolen_state(self):
        """The state a site's real owner receives from /start must not work
        if handed to (or stolen by) a different account."""
        state = self.state_from(self.start(account="a"))
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_stolen", "scope": "cms:read"})
            get.return_value = FakeResp(200, {"sites": [{"id": "wf-site-123"}]})
            # /callback trusts the signed state's own account_id, not the
            # caller's session -- this proves the state itself, not just the
            # session, is what's checked against the site's real owner.
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state},
                                headers={"x-test-account": "b"})
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            site = db.get(Site, "site-a")
            self.assertEqual(site.account_id, "a")   # still A's site, not reassigned to B


if __name__ == "__main__":
    unittest.main()
