"""The project Overview payload. Isolated SQLite, no network."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["SENTRY_DSN"] = ""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.models import Account, Base, Finding, Integration, Scan, Site
from app.webapp import router


class ProjectOverviewTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        now = datetime.now(timezone.utc)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.flush()
            db.add(Site(id="s", account_id="a", hostname="northgate.studio", client_name="Northgate"))
            db.flush()
            db.add_all([Scan(id="old", site_id="s", status="done", score=79, finished_at=now - timedelta(days=7), created_at=now - timedelta(days=7)),
                        Scan(id="new", site_id="s", status="done", score=83, pages_crawled=12, finished_at=now,
                             score_craft=86, score_structure=81, score_search=84, score_answers=76,
                             trace={"stages": [{"stage": "rules", "status": "ok", "detail": {"site_checks": True}}]})])
            db.flush()
            f = lambda check, layer, sev, url="": Finding(scan_id="new", check=check, layer=layer, severity=sev,
                                                          summary=check, page_url=url or None, why="w", fix="f")
            db.add_all([
                f("meta_description_length", "search", "medium", "https://northgate.studio/work"),
                f("meta_description_length", "search", "medium", "https://northgate.studio/about/"),
                f("heading_skips", "structure", "medium", "https://northgate.studio/journal"),
                f("missing_llms_txt", "answers", "low"),
                Finding(scan_id="new", check="ai_crawlers_blocked", layer="answers", severity="high",
                        summary="blocked", evidence=["GPTBot", "CCBot"]),
                Integration(site_id="s", platform="github", credential_ref="r", connected_at=now),
            ])
            db.commit()
        app = FastAPI()
        app.include_router(router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account", side_effect=lambda req, db: db.get(Account, "a"))
        self.auth.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.engine.dispose()

    def get(self):
        with patch("app.search_console.fetch_search_data", return_value=None), \
             patch("app.ga.is_connected", return_value=False):
            return self.client.get("/api/project-overview?project=northgate.studio").json()

    def test_findings_are_grouped_ranked_and_marked_by_what_github_can_apply(self):
        body = self.get()
        checks = [r["check"] for r in body["findings"]]
        self.assertEqual(checks[0], "ai_crawlers_blocked")          # high first
        meta = next(r for r in body["findings"] if r["check"] == "meta_description_length")
        self.assertEqual(meta["pages"], ["/work", "/about"])        # one row, both pages
        self.assertTrue(meta["fixable"])                            # github_repo META_CHECKS
        self.assertFalse(next(r for r in body["findings"] if r["check"] == "heading_skips")["fixable"])
        self.assertEqual(body["platform"], "github")

    def test_scan_tiles_and_headline_come_from_counts(self):
        body = self.get()
        self.assertEqual(body["scan"]["score"], 83)
        self.assertEqual(body["scan"]["previous"], 79)
        self.assertEqual([l["findings"] for l in body["scan"]["layers"]], [0, 1, 1, 2])
        self.assertEqual(body["headline"], "Four findings across three layers.")
        self.assertEqual(body["sub"], "One fix can go out through a GitHub pull request; the rest need a person.")
        self.assertEqual(body["tiles"]["geo"]["crawlers_allowed"], body["tiles"]["geo"]["crawlers_total"] - 2)
        self.assertFalse(body["tiles"]["geo"]["llms_txt"])
        self.assertIsNone(body["tiles"]["seo"]["clicks"])           # not connected: unknown, not zero
        self.assertIsNone(body["tiles"]["analytics"])


    def _forget_site_checks(self):
        """An older scan: no trace marker and no site-level findings."""
        with Session(self.engine) as db:
            db.get(Scan, "new").trace = None
            for f in db.scalars(select(Finding).where(Finding.check.in_(["ai_crawlers_blocked", "missing_llms_txt"]))):
                db.delete(f)
            db.commit()

    def test_a_scan_that_never_ran_the_site_checks_claims_nothing(self):
        self._forget_site_checks()
        geo = self.get()["tiles"]["geo"]
        self.assertIsNone(geo["crawlers_allowed"])
        self.assertIsNone(geo["llms_txt"])


    def test_seo_lists_every_search_and_structure_check_with_its_state(self):
        with patch("app.search_console.is_connected", return_value=False):
            body = self.client.get("/api/project-seo?project=northgate.studio").json()
        states = {c["title"]: c["state"] for c in body["checks"]}
        self.assertEqual(states["Meta description"], "flag")
        self.assertEqual(states["Heading level skips"], "flag")
        self.assertEqual(states["Canonical link"], "pass")
        meta = next(c for c in body["checks"] if c["title"] == "Meta description")
        self.assertEqual(meta["pages"], ["/about", "/work"])
        self.assertTrue(meta["fixable"])
        self.assertNotIn("answers", {c["layer"] for c in body["checks"]})
        self.assertIsNone(body["traffic"])                              # not connected: unknown
        self.assertEqual(body["headline"], "Search checks, without Search Console yet.")

    def test_seo_totals_come_from_search_console_days(self):
        data = {"daily": [{"date": "2026-09-01", "clicks": 30, "impressions": 1000},
                          {"date": "2026-09-02", "clicks": 10, "impressions": 1000}], "queries": []}
        with patch("app.search_console.is_connected", return_value=True),              patch("app.search_console.fetch_search_data", return_value=data):
            body = self.client.get("/api/project-seo?project=northgate.studio").json()
        self.assertEqual((body["traffic"]["clicks"], body["traffic"]["impressions"], body["traffic"]["ctr"]), (40, 2000, 2.0))


    def test_geo_marks_the_blocked_crawlers_and_llms_txt(self):
        body = self.client.get("/api/project-geo?project=northgate.studio").json()
        blocked = [c["token"] for c in body["crawlers"] if c["allowed"] is False]
        self.assertEqual(sorted(blocked), ["CCBot", "GPTBot"])
        self.assertFalse(body["llms_txt"])
        self.assertEqual(body["headline"], "robots.txt blocks two AI crawlers.")
        self.assertEqual({c["layer"] for c in body["checks"]}, {"answers"})

    def test_a_site_level_finding_proves_the_checks_ran(self):
        with Session(self.engine) as db:
            db.get(Scan, "new").trace = None
            db.commit()
        body = self.client.get("/api/project-geo?project=northgate.studio").json()
        self.assertTrue(body["site_checked"])
        self.assertFalse(body["llms_txt"])

    def test_geo_claims_nothing_when_the_site_checks_never_ran(self):
        self._forget_site_checks()
        body = self.client.get("/api/project-geo?project=northgate.studio").json()
        self.assertTrue(all(c["allowed"] is None for c in body["crawlers"]))
        self.assertIsNone(body["llms_txt"])
        states = {c["title"]: c["state"] for c in body["checks"]}
        self.assertEqual(states["AI crawlers blocked"], "unchecked")


    def test_publish_lists_what_the_platform_cannot_apply(self):
        body = self.client.get("/api/changes?project=northgate.studio").json()
        checks = {r["check"] for r in body["not_queueable"]}
        self.assertIn("heading_skips", checks)                  # GitHub can't restructure headings
        self.assertNotIn("meta_description_length", checks)     # it can rewrite this
        self.assertEqual(body["platform"], "github")


    def test_propose_only_offers_what_the_connected_platform_can_apply(self):
        body = self.client.post("/api/changes/propose", params={"project": "northgate.studio"}).json()
        rows = self.client.get("/api/changes?project=northgate.studio").json()["rows"]
        self.assertEqual({r["kind"] for r in rows}, {"meta"})       # GitHub: meta description only here
        self.assertEqual(body["changes"], 2)                        # /work and /about

    def test_with_nothing_connected_propose_skips_what_no_platform_can_do(self):
        from app.models import Finding
        with Session(self.engine) as db:
            for i in db.scalars(select(Integration)):
                db.delete(i)
            db.add(Finding(scan_id="new", check="missing_alt", layer="search", severity="medium", summary="alt"))
            db.commit()
        self.client.post("/api/changes/propose", params={"project": "northgate.studio"})
        body = self.client.get("/api/changes?project=northgate.studio").json()
        kinds = {r["kind"] for r in body["rows"]}
        self.assertNotIn("alt", kinds)                                   # no adapter writes alt text
        self.assertIn("missing_alt", {r["check"] for r in body["not_queueable"]})
        self.assertNotIn("meta_description_length", {r["check"] for r in body["not_queueable"]})


    def test_notifications_split_what_needs_you_from_what_happened(self):
        self.client.post("/api/changes/propose", params={"project": "northgate.studio"})
        with Session(self.engine) as db:
            db.add(Integration(account_id="a", platform="google_search_console", credential_ref="r",
                               connected_at=datetime.now(timezone.utc), last_error="token expired"))
            db.commit()
        body = self.client.get("/api/project-notifications?project=northgate.studio").json()
        titles = [n["title"] for n in body["needs"]]
        self.assertIn("Two changes waiting for approval", titles)
        self.assertIn("Search Console needs reconnecting", titles)
        self.assertIn("One high-severity finding on the latest scan", titles)
        self.assertEqual(body["recent"][0]["title"], "Scan finished: score 79 → 83")

    def test_history_headline_and_series_come_from_scans(self):
        body = self.client.get("/api/project-history?project=northgate.studio").json()
        self.assertEqual([p["score"] for p in body["series"]], [79, 83])
        self.assertTrue(body["headline"].startswith("Up 4 points since "))
        self.assertEqual(body["counts"]["Scan"], 2)
        self.assertNotIn("actor", body["log"][0])


if __name__ == "__main__":
    unittest.main()
