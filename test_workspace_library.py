"""Isolated workspace API contract tests. Never uses the configured database."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["FIG_DEV_NO_AUTH"] = "0"

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app import config, pages
from app.db import get_session
from app.models import Base, Account, Site
from app.webapp import router


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add_all([Account(id="a", name="Account A", slug="a"), Account(id="b", name="Account B", slug="b")])
            db.flush()
            db.add_all([Site(id="site-a", account_id="a", hostname="a.example"), Site(id="site-b", account_id="b", hostname="b.example")])
            db.commit()
        app = FastAPI()
        app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account", side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account")) if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.client = TestClient(app)
        self.headers = {"x-test-account": "a"}

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.engine.dispose()

    def test_project_rename_is_owned_and_validated(self):
        self.assertEqual(self.client.patch('/api/projects/site-a', json={'name': 'Name'}).status_code, 401)
        self.assertEqual(self.client.patch('/api/projects/site-b', headers=self.headers, json={'name': 'Name'}).status_code, 404)
        for name in ('', ' ', 'x' * 81, None):
            self.assertEqual(self.client.patch('/api/projects/site-a', headers=self.headers, json={'name': name}).status_code, 422)
        result = self.client.patch('/api/projects/site-a', headers=self.headers, json={'name': ' New name '})
        self.assertEqual(result.status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Site, 'site-a').client_name, 'New name')
            self.assertEqual(db.get(Site, 'site-a').hostname, 'a.example')

    def test_new_owner_starts_without_demo_projects(self):
        from app.auth import link_user
        with Session(self.engine) as db:
            with patch.object(config, 'OWNER_EMAIL', 'new-owner@example.com'), patch.object(config, 'DEMO_ACCOUNT_SLUG', 'a'):
                user = link_user(db, {'id': 'new-owner', 'email': 'new-owner@example.com'})
            self.assertNotEqual(user.account_id, 'a')
            self.assertEqual(pages.sites_of(db, db.get(Account, user.account_id)), [])

    def test_remove_project_is_owned_soft_removal(self):
        with patch('app.webapp.billing.try_sync') as sync:
            self.assertEqual(self.client.delete('/api/projects/site-b', headers=self.headers).status_code, 404)
            sync.assert_not_called()
            self.assertEqual(self.client.delete('/api/projects/site-a', headers=self.headers).status_code, 200)
            sync.assert_called_once()
        with Session(self.engine) as db:
            self.assertIsNotNone(db.get(Site, 'site-a'))
            self.assertFalse(db.get(Site, 'site-a').is_active)
            self.assertTrue(db.get(Site, 'site-b').is_active)
            self.assertEqual(pages.sites_of(db, db.get(Account, 'a')), [])

    def create(self, title="My guide", account="a", site="site-a"):
        return self.client.post("/api/content", headers={"x-test-account": account}, json={"project_id": site, "title": title})

    def test_auth_and_empty_library(self):
        self.assertEqual(self.client.get("/api/content").status_code, 401)
        result = self.client.get("/api/content", headers=self.headers).json()
        self.assertEqual(result["items"], [])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["projects"][0]["name"], "a.example")

    def test_workspace_reads_require_authentication(self):
        for path in ["projects", "overview", "seo", "geo", "notifications", "history", "settings", "content", "changes"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get("/api/" + path).status_code, 401)

    def test_foreign_content_cannot_be_created_or_moved(self):
        self.assertEqual(self.create(site="site-b").status_code, 422)
        foreign = self.create(account="b", site="site-b").json()["id"]
        self.assertEqual(self.client.post("/api/content/" + foreign + "/move", headers=self.headers, json={"to": "in_progress"}).status_code, 409)
        self.assertEqual(self.client.get("/api/content/" + foreign, headers={"x-test-account": "b"}).json()["state"], "queued")

    def test_account_isolation(self):
        foreign = self.create(account="b", site="site-b").json()["id"]
        self.assertEqual(self.client.get("/api/content", headers=self.headers).json()["total"], 0)
        self.assertEqual(self.client.get("/api/content/" + foreign, headers=self.headers).status_code, 404)
        self.assertEqual(self.client.patch("/api/content/" + foreign, headers=self.headers, json={"body": "no"}).status_code, 404)
        self.assertEqual(self.client.get("/api/content?project=site-b", headers=self.headers).status_code, 404)

    def test_save_and_review(self):
        post = self.create().json()
        saved = self.client.patch("/api/content/" + post["id"], headers=self.headers, json={"title": "Updated guide", "body": "# A draft\n\nA real saved paragraph.", "keyword": "draft"})
        self.assertEqual(saved.status_code, 200)
        for state in ["in_progress", "review"]:
            moved = self.client.post("/api/content/" + post["id"] + "/move", headers=self.headers, json={"to": state})
            self.assertEqual(moved.status_code, 200)
        result = self.client.get("/api/content?state=review&q=Updated", headers=self.headers).json()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["body"], "# A draft\n\nA real saved paragraph.")

    def test_editing_approved_text_goes_back_through_review(self):
        post = self.create().json()["id"]
        url = "/api/content/" + post
        self.client.patch(url, headers=self.headers, json={"body": "The approved draft."})
        for state in ["in_progress", "review", "scheduled"]:
            self.assertEqual(self.client.post(url + "/move", headers=self.headers, json={"to": state}).status_code, 200)
        # Saving identical text is not an edit: still scheduled, date kept.
        same = self.client.patch(url, headers=self.headers, json={"body": "The approved draft."}).json()
        self.assertEqual(same["state"], "scheduled")
        self.assertTrue(same["scheduled_for"])
        # Changing the text after approval withdraws the approval.
        edited = self.client.patch(url, headers=self.headers, json={"body": "Different words, never read."}).json()
        self.assertEqual(edited["state"], "review")
        self.assertIsNone(edited["scheduled_for"])
        # A change of keyword alone does not touch the approved text.
        self.client.post(url + "/move", headers=self.headers, json={"to": "scheduled"})
        kept = self.client.patch(url, headers=self.headers, json={"keyword": "another"}).json()
        self.assertEqual(kept["state"], "scheduled")

    def test_a_scheduled_post_past_its_date_is_reported_overdue(self):
        from datetime import datetime, timedelta, timezone
        from app.models import ContentPost
        post = self.create().json()["id"]
        url = "/api/content/" + post
        self.assertFalse(self.client.get(url, headers=self.headers).json()["overdue"])
        self.client.patch(url, headers=self.headers, json={"body": "A real draft to approve."})
        for state in ["in_progress", "review", "scheduled"]:
            self.client.post(url + "/move", headers=self.headers, json={"to": state})
        self.assertFalse(self.client.get(url, headers=self.headers).json()["overdue"])   # two days out
        with Session(self.engine) as db:
            db.get(ContentPost, post).scheduled_for = datetime.now(timezone.utc) - timedelta(hours=3)
            db.commit()
        late = self.client.get(url, headers=self.headers).json()
        self.assertTrue(late["overdue"])
        self.assertEqual(late["state"], "scheduled")          # reported, never auto-published
        listed = self.client.get("/api/content?state=scheduled", headers=self.headers).json()["items"]
        self.assertTrue(listed[0]["overdue"])

    def test_someone_elses_post_looks_the_same_as_a_missing_one(self):
        foreign = self.create(account="b", site="site-b").json()["id"]
        theirs = self.client.get("/api/content/" + foreign, headers=self.headers)
        missing = self.client.get("/api/content/no-such-post", headers=self.headers)
        self.assertEqual(theirs.status_code, missing.status_code)
        self.assertEqual(theirs.text, missing.text)
        moved = self.client.post("/api/content/" + foreign + "/move", headers=self.headers, json={"to": "in_progress"})
        gone = self.client.post("/api/content/no-such-post/move", headers=self.headers, json={"to": "in_progress"})
        self.assertEqual(moved.text, gone.text)

    def test_profile_rename(self):
        url = "/api/settings/profile"
        self.assertEqual(self.client.patch(url, json={"name": "New"}).status_code, 401)
        ok = self.client.patch(url, headers=self.headers, json={"name": "  Acme   Studio \n"})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["profile"]["name"], "Acme Studio")
        with Session(self.engine) as db:
            self.assertEqual(db.get(Account, "a").name, "Acme Studio")
            self.assertEqual(db.get(Account, "a").slug, "a")        # the slug is untouched
            self.assertEqual(db.get(Account, "b").name, "Account B")  # so is everyone else
        for bad in ({}, {"name": ""}, {"name": "x"}, {"name": "y" * 81}, {"name": 5}, {"name": "a\x00b"}):
            with self.subTest(bad=bad):
                self.assertEqual(self.client.patch(url, headers=self.headers, json=bad).status_code, 422)
        # Only the name is editable: slug and email in the body are ignored.
        self.client.patch(url, headers=self.headers, json={"name": "Keep", "slug": "hijack", "email": "x@y.z"})
        with Session(self.engine) as db:
            self.assertEqual(db.get(Account, "a").slug, "a")
            self.assertIsNone(db.get(Account, "a").contact_email)

    def test_pagination_and_validation(self):
        for title in ["One", "Two", "100% literal"]:
            self.create(title)
        self.assertEqual(len(self.client.get("/api/content?limit=2", headers=self.headers).json()["items"]), 2)
        self.assertEqual(self.client.get("/api/content?q=%25", headers=self.headers).json()["total"], 1)
        self.assertEqual(self.client.get("/api/content?state=invalid", headers=self.headers).status_code, 422)
        self.assertEqual(self.client.get("/api/content?limit=500", headers=self.headers).status_code, 422)


class PublishQueueEndpointTests(unittest.TestCase):
    """GET /api/changes: publishing.queue()'s return dict carries raw
    SQLAlchemy ORM objects (a Change and a list of Integration rows) under
    "_change"/"_integrations" for an internal Python caller -- this proved
    to still JSON-serialize by accident (FastAPI's jsonable_encoder walks
    an ORM object's __dict__), so it never crashed, but it dumped every
    column of both, unfiltered, straight to the browser. Found while
    building the first real frontend caller of this endpoint; nothing had
    ever actually hit it before. webapp.py's /changes route now strips both
    via _public(), applied per-row too since "_change" is one level down."""

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.add(Site(id="s", account_id="a", hostname="a.example"))
            db.commit()
            from app.models import Change, Finding, Integration, Scan
            db.add(Scan(id="scan-1", site_id="s", status="done"))
            db.commit()
            finding = Finding(scan_id="scan-1", check="missing_title", summary="x")
            db.add(finding)
            db.commit()
            db.add(Change(site_id="s", finding_id=finding.id, page_url="https://a.example/p",
                          kind="meta", title="missing_title", state="proposed"))
            db.add(Integration(site_id="s", platform="wordpress", endpoint="https://a.example",
                               connected_at=datetime.now(timezone.utc)))
            db.commit()
        app = FastAPI()
        app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account",
                          side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account"))
                          if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.client = TestClient(app)
        self.headers = {"x-test-account": "a"}

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.engine.dispose()

    def test_the_response_carries_no_internal_orm_keys(self):
        r = self.client.get("/api/changes", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        # The pre-fix bug: a top-level "integrations" key (no underscore)
        # held every column of every raw Integration row; a per-row
        # "change" key (also no underscore) held the raw Change row too --
        # both survived _public() because that helper only strips keys that
        # already start with "_". Check the exact key set, not just for
        # the new "_"-prefixed names, so this fails the same way the old
        # unprefixed leak would have.
        self.assertEqual(set(body.keys()), {"rows", "counts", "connected", "sites"})
        self.assertEqual(len(body["rows"]), 1)
        row = body["rows"][0]
        self.assertEqual(set(row.keys()), {
            "id", "site_id", "hostname", "client", "page", "kind", "title",
            "detail", "state", "error", "platform", "can_publish", "at",
        })
        self.assertEqual(row["state"], "proposed")
        self.assertEqual(row["platform"], "wordpress")
        self.assertEqual(row["hostname"], "a.example")

    def test_someone_elses_workspace_sees_nothing(self):
        with Session(self.engine) as db:
            db.add(Account(id="b", name="B", slug="b"))
            db.commit()
        r = self.client.get("/api/changes", headers={"x-test-account": "b"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["rows"], [])

    def test_project_filter_scopes_to_one_site(self):
        with Session(self.engine) as db:
            db.add(Site(id="s2", account_id="a", hostname="two.example"))
            db.commit()
        r = self.client.get("/api/changes", params={"project": "s2"}, headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["rows"], [])
        self.assertEqual(r.json()["sites"], 1)

    def test_project_filter_for_a_site_you_dont_own_404s(self):
        with Session(self.engine) as db:
            db.add(Account(id="b", name="B", slug="b"))
            db.add(Site(id="foreign", account_id="b", hostname="foreign.example"))
            db.commit()
        r = self.client.get("/api/changes", params={"project": "foreign"}, headers=self.headers)
        self.assertEqual(r.status_code, 404)

    def test_propose_with_a_project_only_proposes_for_that_site(self):
        from app.models import Finding, Scan
        with Session(self.engine) as db:
            db.add(Site(id="s2", account_id="a", hostname="two.example"))
            db.add(Scan(id="scan-2", site_id="s2", status="done"))
            db.commit()
            db.add(Finding(scan_id="scan-2", check="missing_title", summary="x"))
            db.commit()
        r = self.client.post("/api/changes/propose", params={"project": "s2"}, headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["changes"], 1)
        # The already-proposed change on site "s" from setUp must not be
        # counted or re-proposed by a call scoped to a different project.
        rows = self.client.get("/api/changes", params={"project": "s2"}, headers=self.headers).json()["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["site_id"], "s2")


class ProjectSettingsEndpointTests(unittest.TestCase):
    """GET /api/project-settings?project= -- /projects/[id]/settings' real data.
    Scoped the same way /api/overview, /api/seo and /api/geo already are:
    an explicit id is ownership-checked, empty defaults to the account's
    first site, and a zero-site account gets an empty, non-error shape
    rather than a 404 -- the real fix for Settings always defaulting to
    account.sites[0] with no way to tell (or see) which project it was
    even scoped to."""

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.add(Site(id="site-1", account_id="a", hostname="one.example"))
            db.add(Site(id="site-2", account_id="a", hostname="two.example"))
            db.add(Account(id="empty", name="Empty", slug="empty"))
            db.commit()
            from app.models import Integration
            db.add(Integration(site_id="site-1", platform="wordpress", endpoint="https://one.example",
                               connected_at=datetime.now(timezone.utc)))
            db.commit()
        app = FastAPI()
        app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account",
                          side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account"))
                          if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.client = TestClient(app)
        self.headers = {"x-test-account": "a"}

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.engine.dispose()

    def test_returns_only_that_projects_own_integrations(self):
        r = self.client.get("/api/project-settings?project=site-1", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["project"]["id"], "site-1")
        wp = next(a for a in body["apis"] if a["name"] == "WordPress")
        self.assertTrue(wp["ok"])

        # The other real project, with no integration connected, must show
        # WordPress as not connected -- proves this isn't reading site-1's
        # connection for every project by accident.
        r2 = self.client.get("/api/project-settings?project=site-2", headers=self.headers)
        self.assertEqual(r2.status_code, 200)
        wp2 = next(a for a in r2.json()["apis"] if a["name"] == "WordPress")
        self.assertFalse(wp2["ok"])

    def test_no_project_given_defaults_to_the_first_site(self):
        r = self.client.get("/api/project-settings", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["project"]["id"], "site-1")

    def test_an_account_with_no_sites_gets_an_empty_shape_not_an_error(self):
        r = self.client.get("/api/project-settings", headers={"x-test-account": "empty"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIsNone(body["project"])
        self.assertEqual(body["apis"], [])

    def test_a_project_you_dont_own_404s(self):
        with Session(self.engine) as db:
            db.add(Account(id="b", name="B", slug="b"))
            db.commit()
        r = self.client.get("/api/project-settings?project=site-1", headers={"x-test-account": "b"})
        self.assertEqual(r.status_code, 404)

    def test_requires_authentication(self):
        r = self.client.get("/api/project-settings?project=site-1")
        self.assertEqual(r.status_code, 401)


class TrialEnforcementTests(unittest.TestCase):
    """Scanning (adding a project, auditing one, auditing the estate) is the
    cost-incurring action -- a real crawl plus an LLM call -- so it's the one
    thing gated once the trial runs out with nothing subscribed."""

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add_all([
                Account(id="fresh", name="Fresh", slug="fresh",
                       trial_ends_at=datetime.now(timezone.utc) + timedelta(days=2)),
                Account(id="expired", name="Expired", slug="expired",
                       trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1)),
                Account(id="subscribed", name="Subscribed", slug="subscribed",
                       trial_ends_at=datetime.now(timezone.utc) - timedelta(days=30),
                       stripe_subscription_id="sub_live"),
                Account(id="legacy", name="Legacy", slug="legacy", trial_ends_at=None),
                Account(id=config.DEMO_ACCOUNT_SLUG, name="Demo", slug=config.DEMO_ACCOUNT_SLUG,
                       trial_ends_at=datetime.now(timezone.utc) - timedelta(days=365)),
            ])
            db.flush()
            for acct in ("fresh", "expired", "subscribed", "legacy", config.DEMO_ACCOUNT_SLUG):
                db.add(Site(id=f"site-{acct}", account_id=acct, hostname=f"{acct}.example"))
            db.commit()
        app = FastAPI()
        app.include_router(router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account",
                          side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account"))
                          if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.patch_hostname = patch("app.webapp.public_hostname", side_effect=lambda raw: raw.strip().lower())
        self.patch_hostname.start()
        # These tests are about trial gating, not billing sync -- and one
        # fixture account carries a fake stripe_subscription_id, which
        # without this would make add_project's billing.try_sync() call the
        # REAL Stripe API with a bogus id. Off here means try_sync always
        # returns early without a network call, whatever .env holds.
        self.patch_billing = patch.object(config, "BILLING_ENABLED", False)
        self.patch_billing.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.patch_hostname.stop()
        self.patch_billing.stop()
        self.engine.dispose()

    def headers(self, account):
        return {"x-test-account": account}

    def test_a_fresh_trial_can_add_and_audit(self):
        added = self.client.post("/api/projects", headers=self.headers("fresh"), json={"hostname": "new.example"})
        self.assertEqual(added.status_code, 200, added.text)
        pid = added.json()["id"]
        self.assertEqual(self.client.post(f"/api/projects/{pid}/audit", headers=self.headers("fresh")).status_code, 200)
        self.assertEqual(self.client.post("/api/audit-all", headers=self.headers("fresh")).status_code, 200)

    def test_an_expired_trial_is_blocked_from_all_three(self):
        added = self.client.post("/api/projects", headers=self.headers("expired"), json={"hostname": "new.example"})
        self.assertEqual(added.status_code, 402)
        self.assertIn("trial has ended", added.json()["detail"])
        self.assertEqual(self.client.post("/api/projects/site-expired/audit", headers=self.headers("expired")).status_code, 402)
        self.assertEqual(self.client.post("/api/audit-all", headers=self.headers("expired")).status_code, 402)

    def test_nothing_was_created_by_the_blocked_add(self):
        self.client.post("/api/projects", headers=self.headers("expired"), json={"hostname": "new.example"})
        listing = self.client.get("/api/projects", headers=self.headers("expired")).text
        self.assertNotIn("new.example", listing)

    def test_an_expired_trial_can_still_read_and_edit_existing_data(self):
        r = self.client.get("/api/projects", headers=self.headers("expired"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("expired.example", r.text)
        renamed = self.client.patch("/api/settings/profile", headers=self.headers("expired"), json={"name": "Still mine"})
        self.assertEqual(renamed.status_code, 200)

    def test_a_subscription_overrides_an_expired_trial(self):
        added = self.client.post("/api/projects", headers=self.headers("subscribed"), json={"hostname": "new.example"})
        self.assertEqual(added.status_code, 200, added.text)
        self.assertEqual(self.client.post("/api/projects/site-subscribed/audit", headers=self.headers("subscribed")).status_code, 200)

    def test_an_account_with_no_trial_deadline_is_not_gated(self):
        """Never given a deadline is not the same as having missed one --
        covers rows from before trials existed."""
        added = self.client.post("/api/projects", headers=self.headers("legacy"), json={"hostname": "new.example"})
        self.assertEqual(added.status_code, 200, added.text)

    def test_the_seeded_demo_account_is_always_exempt(self):
        """Its trial (set once, at seed time) is permanently in the past --
        FIG_DEV_NO_AUTH and the public showcase both resolve to this account,
        and neither should ever see a paywall."""
        added = self.client.post("/api/projects", headers=self.headers(config.DEMO_ACCOUNT_SLUG), json={"hostname": "new.example"})
        self.assertEqual(added.status_code, 200, added.text)
        self.assertEqual(self.client.post(f"/api/projects/site-{config.DEMO_ACCOUNT_SLUG}/audit",
                                          headers=self.headers(config.DEMO_ACCOUNT_SLUG)).status_code, 200)
        self.assertEqual(self.client.post("/api/audit-all", headers=self.headers(config.DEMO_ACCOUNT_SLUG)).status_code, 200)


class ReAddRemovedProjectTests(unittest.TestCase):
    """`Site.hostname` is only unique per account in the database sense --
    `remove_project` deactivates a row rather than deleting it, so the
    (account_id, hostname) constraint still holds it after removal.
    add_project's "already in this workspace" check queried
    pages.sites_of(), which filters to active sites only, so a removed-then-
    re-added hostname sailed past that check and hit the constraint as an
    unhandled IntegrityError -- a real 500 in production
    (FIG-AI-BACKEND-4), not simulated."""

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="Account A", slug="a"))
            db.flush()
            db.add(Site(id="site-1", account_id="a", hostname="launchvault.ca"))
            db.commit()
        app = FastAPI()
        app.include_router(router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account",
                          side_effect=lambda request, db: db.get(Account, request.headers.get("x-test-account"))
                          if request.headers.get("x-test-account") else None)
        self.auth.start()
        self.patch_hostname = patch("app.webapp.public_hostname", side_effect=lambda raw: raw.strip().lower())
        self.patch_hostname.start()
        self.patch_billing = patch.object(config, "BILLING_ENABLED", False)
        self.patch_billing.start()
        self.client = TestClient(app)
        self.headers = {"x-test-account": "a"}

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.patch_hostname.stop()
        self.patch_billing.stop()
        self.engine.dispose()

    def test_removing_then_re_adding_the_same_hostname_revives_the_old_row(self):
        removed = self.client.delete("/api/projects/site-1", headers=self.headers)
        self.assertEqual(removed.status_code, 200, removed.text)

        added = self.client.post("/api/projects", headers=self.headers, json={"hostname": "Launchvault.ca"})
        self.assertEqual(added.status_code, 200, added.text)
        self.assertEqual(added.json()["id"], "site-1", "should revive the removed row, not fork a new one")

        with Session(self.engine) as db:
            rows = db.query(Site).filter(Site.hostname == "launchvault.ca").all()
            self.assertEqual(len(rows), 1, "must not leave two rows for one hostname")
            self.assertTrue(rows[0].is_active)

    def test_re_adding_an_already_active_project_still_409s(self):
        added = self.client.post("/api/projects", headers=self.headers, json={"hostname": "launchvault.ca"})
        self.assertEqual(added.status_code, 409)

    def test_a_reactivated_project_keeps_its_client_name_if_none_is_given_again(self):
        with Session(self.engine) as db:
            db.query(Site).filter(Site.id == "site-1").update({"client_name": "Launch Vault"})
            db.commit()
        self.client.delete("/api/projects/site-1", headers=self.headers)

        added = self.client.post("/api/projects", headers=self.headers, json={"hostname": "launchvault.ca"})
        self.assertEqual(added.status_code, 200, added.text)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Site, "site-1").client_name, "Launch Vault")


class JsRenderingHealthTests(unittest.TestCase):
    """app.pages._js_rendering_health -- a pure function, so no app/DB needed.
    Only .pages is read, so a lightweight stand-in for Scan is enough."""

    def scan(self, *flags):
        page_objs = [SimpleNamespace(js_dependent=f) for f in flags]
        return SimpleNamespace(pages=page_objs)

    def test_no_scan_yet(self):
        h = pages._js_rendering_health(None)
        self.assertEqual(h["state"], "Never run")
        self.assertTrue(h["ok"])

    def test_a_clean_scan_reports_all_server_rendered(self):
        h = pages._js_rendering_health(self.scan(False, False, False))
        self.assertEqual(h["state"], "All server-rendered")
        self.assertTrue(h["ok"])

    def test_flagged_pages_are_counted_and_reported_not_ok(self):
        h = pages._js_rendering_health(self.scan(True, False, True, False))
        self.assertEqual(h["state"], "2 of 4 may need JS")
        self.assertFalse(h["ok"])
        self.assertIn("2 of 4", h["note"])

    def test_a_scan_with_no_pages_at_all_does_not_divide_by_zero(self):
        h = pages._js_rendering_health(self.scan())
        self.assertEqual(h["state"], "All server-rendered")


class NotificationHrefsPointAtTheRightProjectTests(unittest.TestCase):
    """Each notification names a real project (site_id) -- its action link
    must point at that project's own /projects/{id}/... page, not a generic
    link that used to silently default server-side to the account's first
    site regardless of which project the notification was actually about."""

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.add(Site(id="site-1", account_id="a", hostname="one.example"))
            db.add(Site(id="site-2", account_id="a", hostname="two.example"))
            db.commit()
        self.db = Session(self.engine)
        self.account = self.db.get(Account, "a")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_a_pending_approval_links_to_its_own_projects_seo_page(self):
        from app.models import Change
        self.db.add(Change(site_id="site-2", kind="meta", title="Fix meta description"))
        self.db.commit()
        feed = pages.notifications(self.db, self.account)["feed"]
        approval = next(f for f in feed if f["kind"] == "approval")
        self.assertEqual(approval["href"], "/projects/site-2/seo")

    def test_a_failed_scan_links_to_its_own_projects_history_page(self):
        from app.models import Scan
        self.db.add(Scan(site_id="site-1", status="failed", error="dns_failed"))
        self.db.commit()
        feed = pages.notifications(self.db, self.account)["feed"]
        sync = next(f for f in feed if f["kind"] == "sync")
        self.assertEqual(sync["href"], "/projects/site-1/history")

    def test_two_different_projects_notifications_link_to_two_different_places(self):
        from app.models import Change
        self.db.add(Change(site_id="site-1", kind="meta", title="Fix A"))
        self.db.add(Change(site_id="site-2", kind="meta", title="Fix B"))
        self.db.commit()
        feed = pages.notifications(self.db, self.account)["feed"]
        hrefs = {f["href"] for f in feed if f["kind"] == "approval"}
        self.assertEqual(hrefs, {"/projects/site-1/seo", "/projects/site-2/seo"})


if __name__ == "__main__":
    unittest.main()
