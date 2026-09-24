"""Connecting a platform IS how a new project gets created (2026-09-24) --
no network, no real platform apps. Covers the create-mode path added to
every site-scoped OAuth callback in app/oauth.py: `site_id` omitted from
`/start` means the callback discovers a real hostname (where the platform's
own API allows it) and creates the Site itself via
app/webapp.py:create_project, rather than requiring one to already exist.

Two platforms can't discover their own domain (GitHub without a GitHub
Pages custom domain; Wix, whose Site Properties API has no URL field at
all) and instead land on the pending-token "what's this deployed at?"
step, finished by POST /api/projects/finish-oauth-create. WordPress's own
create path (no OAuth at all) is covered here too.
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
from app.models import Account, Base, Integration, Scan, Secret, Site
from app.secrets_store import read_secret
from app.webapp import router as workspace_router

SHOPIFY_CLIENT_ID = "shpat_test_client_id"
SHOPIFY_CLIENT_SECRET = "test-shopify-client-secret"
WEBFLOW_CLIENT_ID = "webflow-test-client-id"
WEBFLOW_CLIENT_SECRET = "test-webflow-client-secret"
GITHUB_CLIENT_ID = "github-test-client-id"
GITHUB_CLIENT_SECRET = "test-github-client-secret"
WIX_CLIENT_ID = "wix-test-client-id"
WIX_CLIENT_SECRET = "test-wix-client-secret"
WIX_SHARE_URL_ID = "11111111-1111-1111-1111-111111111111"


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class OAuthCreateProjectTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode()),
            patch.object(config, "SESSION_SECRET", "test-session-secret-not-real"),
            patch.object(config, "SHOPIFY_CLIENT_ID", SHOPIFY_CLIENT_ID),
            patch.object(config, "SHOPIFY_CLIENT_SECRET", SHOPIFY_CLIENT_SECRET),
            patch.object(config, "SHOPIFY_OAUTH_ENABLED", True),
            patch.object(config, "WEBFLOW_CLIENT_ID", WEBFLOW_CLIENT_ID),
            patch.object(config, "WEBFLOW_CLIENT_SECRET", WEBFLOW_CLIENT_SECRET),
            patch.object(config, "WEBFLOW_OAUTH_ENABLED", True),
            patch.object(config, "GITHUB_CLIENT_ID", GITHUB_CLIENT_ID),
            patch.object(config, "GITHUB_CLIENT_SECRET", GITHUB_CLIENT_SECRET),
            patch.object(config, "GITHUB_OAUTH_ENABLED", True),
            patch.object(config, "WIX_CLIENT_ID", WIX_CLIENT_ID),
            patch.object(config, "WIX_CLIENT_SECRET", WIX_CLIENT_SECRET),
            patch.object(config, "WIX_SHARE_URL_ID", WIX_SHARE_URL_ID),
            patch.object(config, "WIX_OAUTH_ENABLED", True),
            patch("app.webapp.public_hostname",
                 side_effect=lambda raw: raw.strip().lower().split("://")[-1].split("/")[0]),
        ]
        for p in self.patches:
            p.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.commit()

        app = FastAPI()
        app.include_router(oauth.router)
        app.include_router(workspace_router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session

        def account_of(request, db):
            return db.get(Account, request.headers.get("x-test-account")) \
                if request.headers.get("x-test-account") else None
        self.auth_oauth = patch("app.oauth.current_account", side_effect=account_of)
        self.auth_webapp = patch("app.webapp.current_account", side_effect=account_of)
        self.auth_oauth.start()
        self.auth_webapp.start()
        self.client = TestClient(app, follow_redirects=False)

    def tearDown(self):
        self.client.close()
        self.auth_oauth.stop()
        self.auth_webapp.stop()
        for p in self.patches:
            p.stop()
        self.engine.dispose()

    def headers(self):
        return {"x-test-account": "a"}

    def state_from(self, start_response) -> str:
        return parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]

    def wix_state_from(self, start_response) -> str:
        """Wix's `state` rides inside the (percent-encoded) postInstallationUrl
        param, not as a top-level query param of the installer redirect."""
        from urllib.parse import unquote
        outer = parse_qs(urlparse(start_response.headers["location"]).query)
        inner = unquote(outer["postInstallationUrl"][0])
        return parse_qs(urlparse(inner).query)["state"][0]

    def sites(self):
        with Session(self.engine) as db:
            return list(db.scalars(select(Site)))

    # -- Shopify: discovers the real storefront domain, not the .myshopify.com id --

    def test_shopify_create_mode_uses_the_shops_primary_domain_not_the_typed_shop(self):
        start = self.client.get("/oauth/shopify/start", params={"shop": "test-store.myshopify.com"},
                                headers=self.headers())
        self.assertEqual(start.status_code, 307)
        state = self.state_from(start)
        params = self.params_for_shopify(state)
        with patch("app.oauth.httpx.post") as post:
            post.side_effect = [
                FakeResp(200, {"access_token": "shpat_real", "scope": "read_content,write_content"}),
                FakeResp(200, {"data": {"shop": {"primaryDomain": {"host": "www.real-storefront.com"}}}}),
            ]
            r = self.client.get("/oauth/shopify/callback", params=params)
        self.assertEqual(r.status_code, 307)
        self.assertIn("connected=1", r.headers["location"])
        sites = self.sites()
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0].hostname, "www.real-storefront.com")
        with Session(self.engine) as db:
            integ = db.scalars(select(Integration).where(Integration.site_id == sites[0].id)).one()
            self.assertEqual(integ.platform, "shopify")
            self.assertTrue(integ.is_connected())

    def test_shopify_create_mode_persists_nothing_if_domain_discovery_fails(self):
        start = self.client.get("/oauth/shopify/start", params={"shop": "test-store.myshopify.com"},
                                headers=self.headers())
        state = self.state_from(start)
        params = self.params_for_shopify(state)
        with patch("app.oauth.httpx.post") as post:
            post.side_effect = [
                FakeResp(200, {"access_token": "shpat_real", "scope": "read_content"}),
                FakeResp(500, {}),
            ]
            r = self.client.get("/oauth/shopify/callback", params=params)
        self.assertIn("domain_discovery_failed", r.headers["location"])
        self.assertEqual(self.sites(), [])
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 0)

    def test_shopify_reconnect_mode_still_works_with_an_existing_site(self):
        """site_id given: unchanged behavior, no discovery call at all."""
        with Session(self.engine) as db:
            db.add(Site(id="site-a", account_id="a", hostname="a.example"))
            db.commit()
        start = self.client.get("/oauth/shopify/start",
                                params={"shop": "test-store.myshopify.com", "site_id": "site-a"},
                                headers=self.headers())
        state = self.state_from(start)
        params = self.params_for_shopify(state)
        with patch("app.oauth.httpx.post") as post:
            post.return_value = FakeResp(200, {"access_token": "shpat_real", "scope": "read_content"})
            r = self.client.get("/oauth/shopify/callback", params=params)
        self.assertEqual(post.call_count, 1)   # only the token exchange -- no domain lookup
        self.assertIn(f"{config.FRONTEND_URL}/projects/a.example/settings", r.headers["location"])

    def params_for_shopify(self, state, shop="test-store.myshopify.com", code="a-code"):
        import hashlib
        import hmac as hmac_module
        base = {"code": code, "shop": shop, "state": state, "timestamp": "1732000000"}
        ordered = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
        base["hmac"] = hmac_module.new(SHOPIFY_CLIENT_SECRET.encode(), ordered.encode(), hashlib.sha256).hexdigest()
        return base

    # -- Webflow: custom domain first, {shortName}.webflow.io fallback --

    def test_webflow_create_mode_prefers_a_custom_domain(self):
        start = self.client.get("/oauth/webflow/start", headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_token", "scope": "sites:read"})
            get.return_value = FakeResp(200, {"sites": [{
                "id": "wf-site-1", "shortName": "myproject",
                "customDomains": [{"id": "d1", "url": "www.customdomain.com"}],
            }]})
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("connected=1", r.headers["location"])
        sites = self.sites()
        self.assertEqual(sites[0].hostname, "www.customdomain.com")

    def test_webflow_create_mode_falls_back_to_the_default_webflow_io_domain(self):
        start = self.client.get("/oauth/webflow/start", headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_token", "scope": "sites:read"})
            get.return_value = FakeResp(200, {"sites": [{"id": "wf-site-1", "shortName": "myproject",
                                                         "customDomains": []}]})
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("connected=1", r.headers["location"])
        self.assertEqual(self.sites()[0].hostname, "myproject.webflow.io")

    def test_webflow_create_mode_refuses_cleanly_with_no_site_info_at_all(self):
        start = self.client.get("/oauth/webflow/start", headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "wf_token", "scope": "sites:read"})
            get.return_value = FakeResp(500, {})
            r = self.client.get("/oauth/webflow/callback", params={"code": "c", "state": state})
        self.assertIn("domain_discovery_failed", r.headers["location"])
        self.assertEqual(self.sites(), [])

    # -- GitHub: GitHub Pages custom domain, default Pages domain, or a "confirm URL" step --

    def test_github_create_mode_uses_a_pages_custom_domain(self):
        start = self.client.get("/oauth/github/start", params={"repo": "octocat/site"}, headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "gh_token", "scope": "repo"})
            get.return_value = FakeResp(200, {"cname": "www.mysite.com", "html_url": "https://octocat.github.io/site/"})
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        self.assertIn("connected=1", r.headers["location"])
        self.assertEqual(self.sites()[0].hostname, "www.mysite.com")

    def test_github_create_mode_uses_the_default_pages_domain_with_no_cname(self):
        start = self.client.get("/oauth/github/start", params={"repo": "octocat/site"}, headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "gh_token", "scope": "repo"})
            get.return_value = FakeResp(200, {"cname": None, "html_url": "https://octocat.github.io/site/"})
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        self.assertIn("connected=1", r.headers["location"])
        self.assertEqual(self.sites()[0].hostname, "octocat.github.io")

    def test_github_create_mode_with_no_pages_at_all_lands_on_the_confirm_url_step(self):
        start = self.client.get("/oauth/github/start", params={"repo": "octocat/site"}, headers=self.headers())
        state = self.state_from(start)
        with patch("app.oauth.httpx.post") as post, patch("app.oauth.httpx.get") as get:
            post.return_value = FakeResp(200, {"access_token": "gh_token", "scope": "repo"})
            get.return_value = FakeResp(404, {})     # Pages not enabled -- not an error
            r = self.client.get("/oauth/github/callback", params={"code": "c", "state": state})
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(loc.path, "/projects/confirm-url")
        q = parse_qs(loc.query)
        self.assertEqual(q["platform"][0], "github")
        self.assertEqual(self.sites(), [])   # nothing created yet
        # A real credential is already connected, just not attached to a Site yet.
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(__import__("sqlalchemy").func.count()).select_from(Secret)), 1)

        finish = self.client.post("/api/projects/finish-oauth-create", headers=self.headers(),
                                  json={"pending": q["pending"][0], "hostname": "www.myrealsite.com"})
        self.assertEqual(finish.status_code, 200, finish.text)
        self.assertEqual(finish.json()["hostname"], "www.myrealsite.com")
        with Session(self.engine) as db:
            site = db.scalars(select(Site)).one()
            integ = db.scalars(select(Integration).where(Integration.site_id == site.id)).one()
            self.assertEqual(integ.platform, "github")
            self.assertEqual(integ.endpoint, "octocat/site")
            self.assertTrue(integ.is_connected())

    # -- Wix: never discoverable, always the confirm-URL step --

    def test_wix_create_mode_always_lands_on_the_confirm_url_step(self):
        start = self.client.get("/oauth/wix/start", headers=self.headers())
        state = self.wix_state_from(start)
        with patch("app.oauth._wix_verify_signed_instance",
                  return_value={"instanceId": "inst-123"}):
            r = self.client.get("/oauth/wix/callback",
                                params={"instanceId": "inst-123", "signedInstance": "sig.data", "state": state})
        self.assertEqual(r.status_code, 307)
        loc = urlparse(r.headers["location"])
        self.assertEqual(loc.path, "/projects/confirm-url")
        q = parse_qs(loc.query)
        self.assertEqual(q["platform"][0], "wix")
        self.assertEqual(self.sites(), [])

        finish = self.client.post("/api/projects/finish-oauth-create", headers=self.headers(),
                                  json={"pending": q["pending"][0], "hostname": "mywixsite.com"})
        self.assertEqual(finish.status_code, 200, finish.text)
        with Session(self.engine) as db:
            site = db.scalars(select(Site)).one()
            integ = db.scalars(select(Integration).where(Integration.site_id == site.id)).one()
            self.assertEqual(integ.platform, "wix")
            self.assertEqual(read_secret(db, integ.credential_ref)["instance_id"], "inst-123")

    # -- pending-token security --

    def test_a_pending_token_cannot_be_redeemed_by_a_different_account(self):
        with Session(self.engine) as db:
            db.add(Account(id="other", name="Other", slug="other"))
            db.commit()
        pending = oauth._make_pending_create("a", "github", credential_ref="ref-1", endpoint="o/r")
        finish = self.client.post("/api/projects/finish-oauth-create",
                                  headers={"x-test-account": "other"},
                                  json={"pending": pending, "hostname": "x.example"})
        self.assertEqual(finish.status_code, 400)
        self.assertEqual(self.sites(), [])

    def test_an_expired_pending_token_is_rejected(self):
        pending = oauth._make_pending_create("a", "github", credential_ref="ref-1", endpoint="o/r")
        with patch.object(oauth, "PENDING_MAX_AGE", -1):
            finish = self.client.post("/api/projects/finish-oauth-create", headers=self.headers(),
                                      json={"pending": pending, "hostname": "x.example"})
        self.assertEqual(finish.status_code, 400)

    def test_finish_oauth_create_requires_a_hostname(self):
        pending = oauth._make_pending_create("a", "github", credential_ref="ref-1", endpoint="o/r")
        finish = self.client.post("/api/projects/finish-oauth-create", headers=self.headers(),
                                  json={"pending": pending, "hostname": ""})
        self.assertEqual(finish.status_code, 400)

    # -- WordPress: no OAuth, the form's site URL directly creates the project --

    def test_wordpress_connect_creates_the_project_and_connects_on_success(self):
        with patch("app.publishing.wordpress.test_connection", return_value=(True, "")):
            r = self.client.post("/api/projects/connect/wordpress", headers=self.headers(),
                                 json={"endpoint": "https://myblog.example", "credential": "user:app-pass"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["connected"])
        sites = self.sites()
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0].hostname, "myblog.example")

    def test_wordpress_connect_still_creates_the_project_on_a_bad_credential(self):
        """Connected: false, but the project itself exists -- retryable from
        that project's own Settings page, same as reconnecting always was."""
        with patch("app.publishing.wordpress.test_connection", return_value=(False, "401 unauthorized")):
            r = self.client.post("/api/projects/connect/wordpress", headers=self.headers(),
                                 json={"endpoint": "https://myblog.example", "credential": "user:wrong"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(r.json()["connected"])
        self.assertEqual(len(self.sites()), 1)

    def test_wordpress_connect_requires_a_site_url(self):
        r = self.client.post("/api/projects/connect/wordpress", headers=self.headers(),
                             json={"credential": "user:pass"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
