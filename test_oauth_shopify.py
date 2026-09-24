"""Shopify OAuth connect flow: no network, no real Shopify app.

Only the CONNECT step is real (app/oauth.py's docstring for why: no live
store exists to verify a write adapter against). These tests exercise it
against a fake `httpx.post` and a genuinely-computed HMAC -- the HMAC check
is Shopify's real algorithm, run here both to produce a valid signature and
to prove the endpoint's own verification of it is actually correct, not just
"was some function called."
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import hashlib
import hmac as hmac_module
import unittest
from urllib.parse import parse_qs, urlencode, urlparse
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

CLIENT_ID = "shpat_test_client_id"
CLIENT_SECRET = "test-shopify-client-secret"
REDIRECT_URI = "https://fig-ai-backend.onrender.com/oauth/shopify/callback"
SHOP = "test-store.myshopify.com"


def sign(params: dict) -> str:
    """Exactly Shopify's own documented algorithm, used here to produce a
    signature the endpoint should accept -- and, with one byte changed, one
    it must not."""
    ordered = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac_module.new(CLIENT_SECRET.encode(), ordered.encode(), hashlib.sha256).hexdigest()


class ShopifyOAuthTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "SHOPIFY_CLIENT_ID", CLIENT_ID),
            patch.object(config, "SHOPIFY_CLIENT_SECRET", CLIENT_SECRET),
            patch.object(config, "SHOPIFY_OAUTH_REDIRECT_URI", REDIRECT_URI),
            patch.object(config, "SHOPIFY_OAUTH_ENABLED", True),
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

    def start(self, site_id="site-a", shop=SHOP, account="a"):
        return self.client.get("/oauth/shopify/start", params={"site_id": site_id, "shop": shop},
                               headers={"x-test-account": account} if account else {})

    def state_from(self, start_response) -> str:
        return parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    def callback_params(self, state: str, shop=SHOP, code="a-real-looking-code"):
        base = {"code": code, "shop": shop, "state": state, "timestamp": "1732000000"}
        return base | {"hmac": sign(base)}

    # -- /start --------------------------------------------------------

    def test_not_signed_in_is_401(self):
        self.assertEqual(self.start(account=None).status_code, 401)

    def test_someone_elses_site_is_404(self):
        self.assertEqual(self.start(account="b").status_code, 404)

    def test_not_configured_is_503(self):
        with patch.object(config, "SHOPIFY_OAUTH_ENABLED", False):
            self.assertEqual(self.start().status_code, 503)

    def test_a_malformed_shop_is_refused(self):
        for bad in ("not-a-shop", "evil.com", "store.myshopify.com.evil.com", ""):
            with self.subTest(shop=bad):
                self.assertEqual(self.start(shop=bad).status_code, 422)

    def test_redirects_to_the_named_stores_own_authorize_url(self):
        r = self.start()
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(loc.netloc, SHOP)
        self.assertEqual(loc.path, "/admin/oauth/authorize")
        q = parse_qs(loc.query)
        self.assertEqual(q["client_id"][0], CLIENT_ID)
        self.assertEqual(q["redirect_uri"][0], REDIRECT_URI)
        self.assertIn("write_content", q["scope"][0])

    # -- /callback -------------------------------------------------------

    def test_a_correctly_signed_callback_connects_and_stores_the_token(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "shpat_real_token", "scope": "read_content,write_content"})
            r = self.client.get("/oauth/shopify/callback", params=self.callback_params(state))
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        self.assertTrue(r.headers["location"].startswith(f"{config.FRONTEND_URL}/projects/site-a/settings?"))  # lands back on the connected project's own settings page
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(integ.platform, "shopify")
            self.assertEqual(integ.endpoint, SHOP)
            self.assertIsNotNone(integ.connected_at)
            creds = read_secret(db, integ.credential_ref)
            self.assertEqual(creds["access_token"], "shpat_real_token")
            self.assertEqual(db.scalar(select(Integration.__table__.c.id).select_from(Integration)), integ.id)

    def test_a_tampered_hmac_is_rejected_and_nothing_is_stored(self):
        state = self.state_from(self.start())
        params = self.callback_params(state)
        params["hmac"] = "0" * 64        # same length, wrong value
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/shopify/callback", params=params)
        post.assert_not_called()          # never even reaches the token exchange
        self.assertIn("invalid_hmac", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_param_added_after_signing_is_rejected(self):
        """Proves the check covers the whole query string, not a fixed
        subset -- an attacker appending an extra param must not slip through."""
        state = self.state_from(self.start())
        params = self.callback_params(state)
        url = "/oauth/shopify/callback?" + urlencode(params) + "&extra=1"
        with patch("app.oauth.httpx.post"):
            r = self.client.get(url)
        self.assertIn("invalid_hmac", r.headers["location"])

    def test_a_shop_that_does_not_match_the_signed_state_is_rejected(self):
        """The state token from /start for one store must not be replayable
        against a callback claiming to be a different store."""
        state = self.state_from(self.start(shop=SHOP))
        other_shop = "other-store.myshopify.com"
        params = self.callback_params(state, shop=other_shop)
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/shopify/callback", params=params)
        post.assert_not_called()
        self.assertIn("shop_mismatch", r.headers["location"])

    def test_an_expired_state_is_rejected(self):
        state = self.state_from(self.start())
        with patch.object(oauth, "STATE_MAX_AGE", -1):
            params = self.callback_params(state)
            r = self.client.get("/oauth/shopify/callback", params=params)
        self.assertIn("expired_state", r.headers["location"])

    def test_a_forged_state_signed_with_the_wrong_secret_is_rejected(self):
        from itsdangerous import URLSafeTimedSerializer
        forged = URLSafeTimedSerializer("not-the-real-session-secret", salt="fig-oauth-state") \
            .dumps({"site_id": "site-a", "account_id": "a", "shop": SHOP})
        params = self.callback_params(forged)
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/shopify/callback", params=params)
        post.assert_not_called()
        self.assertIn("invalid_state", r.headers["location"])

    def test_shopify_rejecting_the_code_does_not_connect_anything(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(401, {"error": "invalid_request"})
            r = self.client.get("/oauth/shopify/callback", params=self.callback_params(state))
        self.assertIn("token_exchange_failed", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_reconnecting_replaces_rather_than_accumulates_secrets(self):
        state1 = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "shpat_first", "scope": "read_content"})
            self.client.get("/oauth/shopify/callback", params=self.callback_params(state1))
        state2 = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "shpat_second", "scope": "read_content,write_content"})
            self.client.get("/oauth/shopify/callback", params=self.callback_params(state2, code="second-code"))
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 1)
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(read_secret(db, integ.credential_ref)["access_token"], "shpat_second")


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


if __name__ == "__main__":
    unittest.main()
