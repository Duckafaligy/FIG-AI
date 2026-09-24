"""Wix OAuth connect flow: no network, no real Wix app.

Only the CONNECT step is real -- same limitation as Shopify/Webflow (see
app/oauth.py's module docstring). Wix's own shape is genuinely different
from the other three: no code exchange, no callback signature the site
sends back for FIG to check against a client secret the usual way -- the
trust anchor is `signedInstance`, which FIG verifies locally with the same
HMAC-SHA256 algorithm Wix's own docs give (dev.wix.com/docs/build-apps/
develop-your-app/auth/app-instances/parse-the-app-instance-query-parameter),
and `state` still rides along on postInstallationUrl exactly the way Wix's
own external-install-flow docs recommend.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import base64
import hashlib
import hmac
import json
import unittest
from urllib.parse import parse_qs, unquote, urlparse
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

CLIENT_ID = "wix-test-app-id"
CLIENT_SECRET = "test-wix-app-secret"
SHARE_URL_ID = "11111111-1111-1111-1111-111111111111"
REDIRECT_URI = "https://fig-ai-backend.onrender.com/oauth/wix/callback"


def sign_instance(payload: dict, secret: str) -> str:
    """The exact algorithm Wix documents for signedInstance: HMAC-SHA256
    over the still-base64url-encoded (unpadded) data string."""
    data_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), data_b64.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{sig_b64}.{data_b64}"


class WixOAuthTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "WIX_CLIENT_ID", CLIENT_ID),
            patch.object(config, "WIX_CLIENT_SECRET", CLIENT_SECRET),
            patch.object(config, "WIX_SHARE_URL_ID", SHARE_URL_ID),
            patch.object(config, "WIX_OAUTH_REDIRECT_URI", REDIRECT_URI),
            patch.object(config, "WIX_OAUTH_ENABLED", True),
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
        return self.client.get("/oauth/wix/start", params={"site_id": site_id},
                               headers={"x-test-account": account} if account else {})

    def state_from(self, start_response) -> str:
        """The state lives inside the (percent-encoded) postInstallationUrl
        query param, not as a top-level param on the installer URL itself."""
        loc = start_response.headers["location"]
        q = parse_qs(urlparse(loc).query)
        callback_url = unquote(q["postInstallationUrl"][0])
        return parse_qs(urlparse(callback_url).query)["state"][0]

    def callback(self, instance_id="wix-instance-1", state=None, sign_with=CLIENT_SECRET,
                omit_instance_id=False, omit_signed_instance=False):
        params = {}
        if state is not None:
            params["state"] = state
        if not omit_instance_id:
            params["instanceId"] = instance_id
        if not omit_signed_instance:
            params["signedInstance"] = sign_instance({"instanceId": instance_id}, sign_with)
        return self.client.get("/oauth/wix/callback", params=params)

    # -- /start --------------------------------------------------------

    def test_not_signed_in_is_401(self):
        self.assertEqual(self.start(account=None).status_code, 401)

    def test_someone_elses_site_is_404(self):
        self.assertEqual(self.start(account="b").status_code, 404)

    def test_not_configured_is_503(self):
        with patch.object(config, "WIX_OAUTH_ENABLED", False):
            self.assertEqual(self.start().status_code, 503)

    def test_redirects_to_the_fixed_installer_url_with_app_id_and_share_url_id(self):
        r = self.start()
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(f"{loc.scheme}://{loc.netloc}{loc.path}", "https://www.wix.com/app-installer")
        q = parse_qs(loc.query)
        self.assertEqual(q["appId"][0], CLIENT_ID)
        self.assertEqual(q["shareUrlId"][0], SHARE_URL_ID)
        callback_url = unquote(q["postInstallationUrl"][0])
        self.assertTrue(callback_url.startswith(REDIRECT_URI))
        self.assertIn("state=", callback_url)

    # -- /callback -------------------------------------------------------

    def test_a_successful_callback_connects_and_stores_the_verified_instance_id(self):
        state = self.state_from(self.start())
        r = self.callback(instance_id="wix-instance-real", state=state)
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        self.assertIn("project=site-a", r.headers["location"])  # lands back on the connected project, not the account default
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(integ.platform, "wix")
            self.assertIsNotNone(integ.connected_at)
            creds = read_secret(db, integ.credential_ref)
            self.assertEqual(creds["instance_id"], "wix-instance-real")

    def test_a_missing_instance_id_or_signed_instance_means_a_failed_or_cancelled_install(self):
        state = self.state_from(self.start())
        r = self.callback(state=state, omit_signed_instance=True)
        self.assertIn("install_failed", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_tampered_signed_instance_is_rejected_and_nothing_is_stored(self):
        """The raw instanceId query param is explicitly untrusted by Wix's
        own docs -- only a verifying signedInstance should ever connect
        anything."""
        state = self.state_from(self.start())
        forged = sign_instance({"instanceId": "wix-instance-real"}, "not-the-real-secret")
        r = self.client.get("/oauth/wix/callback",
                            params={"instanceId": "wix-instance-real",
                                    "signedInstance": forged, "state": state})
        self.assertIn("invalid_signed_instance", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_signed_instance_naming_a_different_instance_than_the_query_param_still_trusts_the_signed_one(self):
        """A confused-deputy check: even if a caller sends a mismatched raw
        instanceId, the verified signedInstance payload's own instanceId is
        what gets stored -- the raw param is cosmetic, never trusted."""
        state = self.state_from(self.start())
        signed = sign_instance({"instanceId": "the-real-one"}, CLIENT_SECRET)
        r = self.client.get("/oauth/wix/callback",
                            params={"instanceId": "a-different-claimed-id",
                                    "signedInstance": signed, "state": state})
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            creds = read_secret(db, integ.credential_ref)
            self.assertEqual(creds["instance_id"], "the-real-one")

    def test_an_expired_state_is_rejected(self):
        state = self.state_from(self.start())
        with patch.object(oauth, "STATE_MAX_AGE", -1):
            r = self.callback(state=state)
        self.assertIn("expired_state", r.headers["location"])

    def test_a_forged_state_signed_with_the_wrong_secret_is_rejected(self):
        from itsdangerous import URLSafeTimedSerializer
        forged = URLSafeTimedSerializer("not-the-real-session-secret", salt="fig-oauth-state") \
            .dumps({"site_id": "site-a", "account_id": "a"})
        r = self.callback(state=forged)
        self.assertIn("invalid_state", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_state_for_a_site_that_no_longer_exists_is_rejected(self):
        state = self.state_from(self.start())
        with Session(self.engine) as db:
            db.query(Site).filter(Site.id == "site-a").delete()
            db.commit()
        r = self.callback(state=state)
        self.assertIn("site_not_found", r.headers["location"])

    def test_reconnecting_replaces_rather_than_accumulates_secrets(self):
        state1 = self.state_from(self.start())
        self.callback(instance_id="wix-instance-first", state=state1)
        state2 = self.state_from(self.start())
        self.callback(instance_id="wix-instance-second", state=state2)
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 1)
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(read_secret(db, integ.credential_ref)["instance_id"], "wix-instance-second")

    def test_a_site_owned_by_someone_else_cannot_be_connected_by_replaying_a_stolen_state(self):
        """The state a site's real owner receives from /start must not work
        if handed to (or stolen by) a different account -- /callback trusts
        the signed state's own account_id, not any caller session (there
        isn't necessarily one: the browser hitting postInstallationUrl is
        Wix's redirect, not an authenticated FIG session)."""
        state = self.state_from(self.start(account="a"))
        r = self.client.get("/oauth/wix/callback",
                            params={"instanceId": "wix-stolen",
                                    "signedInstance": sign_instance({"instanceId": "wix-stolen"}, CLIENT_SECRET),
                                    "state": state},
                            headers={"x-test-account": "b"})
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            site = db.get(Site, "site-a")
            self.assertEqual(site.account_id, "a")   # still A's site, not reassigned to B


if __name__ == "__main__":
    unittest.main()
