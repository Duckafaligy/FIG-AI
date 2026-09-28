"""The project Analytics page. Isolated SQLite and a fake GA response only."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["SENTRY_DSN"] = ""

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import ga
from app.db import get_session
from app.models import Account, Base, Finding, Scan, Site
from app.webapp import router


def _row(dims, mets):
    return {"dimensionValues": [{"value": d} for d in dims],
            "metricValues": [{"value": m} for m in mets]}


def _today(offset=0):
    import time
    return time.strftime("%Y%m%d", time.gmtime(time.time() - 86400 * offset))


BATCH = {"reports": [
    {"rows": [_row([_today(0)], ["40"]), _row([_today(40)], ["7"])]},
    {"rows": [_row(["/work"], ["812", "0.71"]), _row(["/"], ["1466", "0.58"])]},
    {"rows": [_row(["Organic Search"], ["300"]), _row(["Direct"], ["100"])]},
]}


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.flush()
            db.add(Site(id="s", account_id="a", hostname="northgate.studio",
                        ga_property="properties/123"))
            db.flush()
            db.add(Scan(id="sc", site_id="s", status="done",
                        finished_at=datetime.now(timezone.utc)))
            db.flush()
            db.add(Finding(scan_id="sc", page_url="https://northgate.studio/work/",
                           check="meta_description_length", layer="search", summary="Too long"))
            db.commit()
        app = FastAPI()
        app.include_router(router)

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account",
                          side_effect=lambda req, db: db.get(Account, "a"))
        self.auth.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.engine.dispose()

    def get(self):
        return self.client.get("/api/analytics?project=northgate.studio").json()

    def test_not_connected_is_null_not_zero(self):
        with patch("app.ga._integration", return_value=None), \
             patch("app.ga.httpx.post", side_effect=AssertionError("no provider call")):
            body = self.get()
        self.assertFalse(body["connected"])
        self.assertIsNone(body["detail"])
        self.assertIsNone(body["kpis"])

    def test_report_fills_days_and_joins_findings_by_path(self):
        batch = SimpleNamespace(status_code=200, json=lambda: BATCH)
        kpis = [{"value": "412", "label": "Sessions", "delta": 8.4}]
        with patch("app.ga._integration", return_value=SimpleNamespace(last_error=None)), \
             patch("app.ga._access_token", return_value="fake"), \
             patch("app.ga.httpx.post", return_value=batch) as post, \
             patch("app.ga.fetch_overview_metrics", return_value=kpis):
            body = self.get()
        self.assertTrue(post.call_args.args[0].endswith("properties/123:batchRunReports"))
        detail = body["detail"]
        lines = {line["name"]: [p["v"] for p in line["points"]] for line in detail["chart"]["lines"]}
        self.assertEqual(len(lines["Last 30 days"]), 30)
        self.assertEqual(lines["Last 30 days"][-1], 40)     # today
        self.assertEqual(sum(lines["Last 30 days"]), 40)    # the missing days are zeros
        self.assertEqual(sum(lines["30 days before"]), 7)   # day 40 lands in the earlier window
        pages = {p["path"]: p for p in detail["pages"]}
        self.assertEqual(pages["/work"]["engaged"], 71)
        self.assertEqual([f["check"] for f in pages["/work"]["findings"]], ["meta_description_length"])
        self.assertEqual(pages["/"]["findings"], [])
        self.assertEqual([c["share"] for c in detail["channels"]], [75, 25])
        self.assertEqual(body["kpis"], kpis)

    def test_rejected_report_records_the_error_and_shows_nothing(self):
        integ = SimpleNamespace(last_error=None)
        with patch("app.ga._integration", return_value=integ), \
             patch("app.ga._access_token", return_value="fake"), \
             patch("app.ga.httpx.post",
                   return_value=SimpleNamespace(status_code=403, text="denied")):
            body = self.get()
        self.assertIsNone(body["detail"])
        self.assertIn("403", integ.last_error)


if __name__ == "__main__":
    unittest.main()
