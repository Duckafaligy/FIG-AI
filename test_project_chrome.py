"""The project sidebar payload. Isolated SQLite only."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["SENTRY_DSN"] = ""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.models import Account, Base, Change, ContentPost, Finding, Integration, Job, Scan, Site
from app.webapp import router


class ProjectChromeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        now = datetime.now(timezone.utc)
        with Session(self.engine) as db:
            db.add_all([Account(id="a", name="A", slug="a", plan="premium", scans_used_this_period=12),
                        Account(id="b", name="B", slug="b")])
            db.flush()
            db.add_all([Site(id="s", account_id="a", hostname="northgate.studio", client_name="Northgate"),
                        Site(id="t", account_id="b", hostname="other.example")])
            db.flush()
            db.add(Scan(id="sc", site_id="s", status="done", finished_at=now, score=83))
            db.flush()
            db.add_all([
                # two rows for one check count once
                Finding(scan_id="sc", check="meta_description_length", layer="search", summary="x"),
                Finding(scan_id="sc", check="meta_description_length", layer="search", summary="x"),
                Finding(scan_id="sc", check="heading_skips", layer="structure", summary="x"),
                Finding(scan_id="sc", check="missing_llms_txt", layer="answers", summary="x"),
                Change(site_id="s", kind="meta", title="Meta", state="proposed"),
                Change(site_id="s", kind="meta", title="Title", state="published"),
                ContentPost(site_id="s", title="Brief", state="queued", category="blog"),
                Integration(site_id="s", platform="github", credential_ref="r", connected_at=now),
                Integration(account_id="a", platform="google_search_console", credential_ref="r",
                            connected_at=now, last_error="token expired"),
                Integration(account_id="b", platform="google_analytics", credential_ref="r", connected_at=now),
                # workspace B's failure, which A must never see
                Scan(id="bs", site_id="t", status="failed", created_at=now),
                Job(kind="scan", status="failed", payload={"scan_id": "bs"}, error="B's private error",
                    finished_at=now),
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

    def test_counts_and_connections_are_real_and_scoped(self):
        body = self.client.get("/api/project-chrome?project=northgate.studio").json()
        self.assertEqual(body["project"], {"id": "s", "hostname": "northgate.studio", "name": "Northgate", "score": 83})
        self.assertEqual(body["badges"]["seo"], 2)          # distinct checks in search + structure
        self.assertEqual(body["badges"]["geo"], 1)
        self.assertEqual(body["badges"]["publish"], 1)      # proposed only
        self.assertEqual(body["badges"]["library"], 1)
        self.assertEqual(body["connections"], [{"platform": "github", "ok": True},
                                               {"platform": "google_search_console", "ok": False}])
        self.assertEqual(body["usage"], {"used": 12, "cap": 250})

    def test_another_workspaces_failures_stay_out_of_yours(self):
        chrome = self.client.get("/api/project-chrome?project=northgate.studio").json()
        self.assertEqual(chrome["badges"]["notifications"], 1)   # this project's one proposed change, nothing of B's
        body = self.client.get("/api/notifications").text
        self.assertNotIn("B's private error", body)
        self.auth.stop()
        self.auth = patch("app.webapp.current_account", side_effect=lambda req, db: db.get(Account, "b"))
        self.auth.start()
        self.assertIn("B's private error", self.client.get("/api/notifications").text)

    def test_library_filters_by_domain_or_id(self):
        for project in ("northgate.studio", "s"):
            body = self.client.get(f"/api/content?project={project}").json()
            self.assertEqual([p["title"] for p in body["items"]], ["Brief"], project)

    def test_another_workspaces_project_is_404(self):
        self.assertEqual(self.client.get("/api/project-chrome?project=other.example").status_code, 404)


if __name__ == "__main__":
    unittest.main()
