"""GitHub OAuth connect flow: no network, no real GitHub OAuth App.

Only the CONNECT step is real -- same limitation as every other platform
here (app/oauth.py's module docstring). Shaped like Google/Webflow (one
fixed authorize URL, no extra callback signature), plus one thing Shopify's
/start also needs that Google/Webflow's doesn't: a caller-supplied value
the grant itself doesn't carry -- there it's `shop`, here it's `repo`.
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

CLIENT_ID = "github-test-client-id"
CLIENT_SECRET = "test-github-client-secret"
REDIRECT_URI = "https://fig-ai-backend.onrender.com/oauth/github/callback"


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class GithubOAuthTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "GITHUB_CLIENT_ID", CLIENT_ID),
            patch.object(config, "GITHUB_CLIENT_SECRET", CLIENT_SECRET),
            patch.object(config, "GITHUB_OAUTH_REDIRECT_URI", REDIRECT_URI),
            patch.object(config, "GITHUB_OAUTH_ENABLED", True),
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

    def start(self, site_id="site-a", repo="owner/repo", account="a"):
        params = {"site_id": site_id}
        if repo is not None:
            params["repo"] = repo
        return self.client.get("/oauth/github/start", params=params,
                               headers={"x-test-account": account} if account else {})

    def state_from(self, start_response) -> str:
        return parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    # -- /start --------------------------------------------------------

    def test_not_signed_in_is_401(self):
        self.assertEqual(self.start(account=None).status_code, 401)

    def test_someone_elses_site_is_404(self):
        self.assertEqual(self.start(account="b").status_code, 404)

    def test_not_configured_is_503(self):
        with patch.object(config, "GITHUB_OAUTH_ENABLED", False):
            self.assertEqual(self.start().status_code, 503)

    def test_a_malformed_repo_is_refused(self):
        for bad in ("not-a-repo", "owner/", "/repo", "owner/repo/extra", ""):
            self.assertEqual(self.start(repo=bad).status_code, 422, bad)

    def test_redirects_to_githubs_one_fixed_authorize_url(self):
        r = self.start(repo="octocat/hello-world")
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(f"{loc.scheme}://{loc.netloc}{loc.path}", "https://github.com/login/oauth/authorize")
        q = parse_qs(loc.query)
        self.assertEqual(q["client_id"][0], CLIENT_ID)
        self.assertEqual(q["redirect_uri"][0], REDIRECT_URI)
        self.assertEqual(q["scope"][0], "repo")

    # -- /callback -------------------------------------------------------

    def test_a_successful_callback_connects_and_stores_the_token_and_repo(self):
        state = self.state_from(self.start(repo="octocat/hello-world"))
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "gho_real_token", "scope": "repo",
                                               "token_type": "bearer"})
            r = self.client.get("/oauth/github/callback", params={"code": "a-real-looking-code", "state": state})
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(integ.platform, "github")
            self.assertEqual(integ.endpoint, "octocat/hello-world")
            self.assertIsNotNone(integ.connected_at)
            creds = read_secret(db, integ.credential_ref)
            self.assertEqual(creds["access_token"], "gho_real_token")

    def test_githubs_200_status_error_body_is_treated_as_a_failure(self):
        """GitHub's real quirk: a bad/expired code answers with HTTP 200 and
        an error field in the body, not a 4xx status -- checking status
        alone would have connected nothing while claiming success."""
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"error": "bad_verification_code",
                                               "error_description": "The code passed is incorrect or expired."})
            r = self.client.get("/oauth/github/callback", params={"code": "bad-code", "state": state})
        self.assertIn("token_exchange_failed", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_the_provider_denying_consent_is_reported_not_hidden(self):
        r = self.client.get("/oauth/github/callback", params={"error": "access_denied", "state": "irrelevant"})
        self.assertIn("access_denied", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_an_expired_state_is_rejected(self):
        state = self.state_from(self.start())
        with patch.object(oauth, "STATE_MAX_AGE", -1):
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        self.assertIn("expired_state", r.headers["location"])

    def test_a_forged_state_signed_with_the_wrong_secret_is_rejected(self):
        from itsdangerous import URLSafeTimedSerializer
        forged = URLSafeTimedSerializer("not-the-real-session-secret", salt="fig-oauth-state") \
            .dumps({"site_id": "site-a", "account_id": "a", "repo": "owner/repo"})
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": forged})
        post.assert_not_called()
        self.assertIn("invalid_state", r.headers["location"])

    def test_a_state_for_a_site_that_no_longer_exists_is_rejected(self):
        state = self.state_from(self.start())
        with Session(self.engine) as db:
            db.query(Site).filter(Site.id == "site-a").delete()
            db.commit()
        with patch("app.oauth.httpx.post") as post:
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        post.assert_not_called()
        self.assertIn("site_not_found", r.headers["location"])

    def test_github_rejecting_the_code_with_a_real_http_error_does_not_connect_anything(self):
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(401, {"error": "unauthorized"})
            r = self.client.get("/oauth/github/callback", params={"code": "bad-code", "state": state})
        self.assertIn("token_exchange_failed", r.headers["location"])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(Integration.__table__.c.id)), None)

    def test_a_network_failure_reaching_github_is_reported_not_raised(self):
        import httpx
        state = self.state_from(self.start())
        with patch("app.oauth.httpx.post", side_effect=httpx.ConnectError("boom")):
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        self.assertIn("token_request_failed", r.headers["location"])

    def test_reconnecting_replaces_rather_than_accumulates_secrets(self):
        state1 = self.state_from(self.start(repo="octocat/repo-one"))
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "gho_first", "scope": "repo"})
            self.client.get("/oauth/github/callback", params={"code": "code-1", "state": state1})
        state2 = self.state_from(self.start(repo="octocat/repo-two"))
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "gho_second", "scope": "repo"})
            self.client.get("/oauth/github/callback", params={"code": "code-2", "state": state2})
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 1)
            integ = db.scalars(select(Integration).where(Integration.site_id == "site-a")).one()
            self.assertEqual(integ.endpoint, "octocat/repo-two")
            self.assertEqual(read_secret(db, integ.credential_ref)["access_token"], "gho_second")

    def test_a_site_owned_by_someone_else_cannot_be_connected_by_replaying_a_stolen_state(self):
        state = self.state_from(self.start(account="a", repo="octocat/hello-world"))
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "gho_stolen", "scope": "repo"})
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state},
                                headers={"x-test-account": "b"})
        self.assertIn("connected=1", r.headers["location"])
        with Session(self.engine) as db:
            site = db.get(Site, "site-a")
            self.assertEqual(site.account_id, "a")


if __name__ == "__main__":
    unittest.main()
