"""Launch regressions. Isolated SQLite and fake providers only."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["SENTRY_DSN"] = ""

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app import auth, billing, ga, search_console, pages
from app.models import Base, Account, Site
from app.db import get_session, _add_missing_columns
from app.webapp import router


class LaunchHardeningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Account(id="a", name="A", slug="a"), Account(id="b", name="B", slug="b")])
        self.db.flush()
        self.db.add_all([Site(id="one", account_id="a", hostname="one.example"), Site(id="two", account_id="a", hostname="two.example"), Site(id="foreign", account_id="b", hostname="foreign.example")])
        self.db.commit()
        app = FastAPI()
        app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        self.auth = patch("app.webapp.current_account", side_effect=lambda req, db: db.get(Account, "a") if req.headers.get("x-test-user") else None)
        self.auth.start()
        self.client = TestClient(app)
        self.headers = {"x-test-user": "a"}

    def tearDown(self):
        self.client.close()
        self.auth.stop()
        self.db.close()
        self.engine.dispose()

    def test_confirmed_signup_keeps_company_and_starts_empty(self):
        user = auth.link_user(self.db, {"id": "new", "email": "new@example.com", "user_metadata": {"company": " My company "}})
        account = self.db.get(Account, user.account_id)
        self.assertEqual(account.name, "My company")
        self.assertEqual(pages.sites_of(self.db, account), [])
        auth.link_user(self.db, {"id": "new", "email": "new@example.com", "user_metadata": {"company": "Do not rename"}})
        self.assertEqual(account.name, "My company")

    def test_new_direct_checkout_never_contacts_stripe(self):
        with patch("app.billing._stripe") as stripe:
            with self.assertRaises(HTTPException) as caught:
                billing.start_checkout(self.db, self.db.get(Account, "a"))
            self.assertEqual(caught.exception.status_code, 409)
            stripe.assert_not_called()

    def test_ga_selection_is_owned_and_validated(self):
        path = "/api/projects/one/analytics-property"
        choices = [{"id": "properties/123", "name": "Real property", "account": "A"}]
        with patch("app.ga.available_properties", return_value=choices) as discover:
            self.assertEqual(self.client.patch(path, json={"property": "properties/123"}).status_code, 401)
            self.assertEqual(self.client.patch("/api/projects/foreign/analytics-property", headers=self.headers, json={"property": "properties/123"}).status_code, 404)
            discover.assert_not_called()
            self.assertEqual(self.client.patch(path, headers=self.headers, json={"property": "properties/999"}).status_code, 422)
            self.assertEqual(self.client.patch(path, headers=self.headers, json={"property": "properties/123"}).status_code, 200)
        self.db.expire_all()
        self.assertEqual(self.db.get(Site, "one").ga_property, "properties/123")
        self.assertIsNone(self.db.get(Site, "two").ga_property)
        with patch("app.ga.available_properties", side_effect=AssertionError("clearing needs no provider")):
            self.assertEqual(self.client.patch(path, headers=self.headers, json={"property": None}).status_code, 200)

    def test_ga_unselected_never_uses_old_shared_property(self):
        integration = SimpleNamespace(endpoint="properties/999")
        with patch("app.ga._integration", return_value=integration), patch("app.ga._access_token", return_value="fake"), patch("app.ga.httpx.post") as report:
            self.assertIsNone(ga.fetch_overview_metrics(self.db, self.db.get(Site, "one")))
            report.assert_not_called()

    def test_ga_reports_use_each_selected_property(self):
        self.db.get(Site, "one").ga_property = "properties/123"
        self.db.get(Site, "two").ga_property = "properties/456"
        response = SimpleNamespace(status_code=200, json=lambda: {"rows": []})
        with patch("app.ga._integration", return_value=SimpleNamespace(endpoint="properties/999")), patch("app.ga._access_token", return_value="fake"), patch("app.ga.httpx.post", return_value=response) as report:
            ga.fetch_overview_metrics(self.db, self.db.get(Site, "one"))
            ga.fetch_overview_metrics(self.db, self.db.get(Site, "two"))
            self.assertIn("properties/123:runReport", report.call_args_list[0].args[0])
            self.assertIn("properties/456:runReport", report.call_args_list[1].args[0])

    def test_ga_discovery_paginates_real_options(self):
        responses = [SimpleNamespace(status_code=200, json=lambda: {"accountSummaries": [{"propertySummaries": [{"property": "properties/123", "displayName": "One"}]}], "nextPageToken": "next"}), SimpleNamespace(status_code=200, json=lambda: {"accountSummaries": [{"propertySummaries": [{"property": "properties/456", "displayName": "Two"}]}]})]
        with patch("app.ga._integration", return_value=object()), patch("app.ga._access_token", return_value="fake"), patch("app.ga.httpx.get", side_effect=responses) as get:
            choices = ga.available_properties(self.db, self.db.get(Site, "one"))
            self.assertEqual([row["id"] for row in choices], ["properties/123", "properties/456"])
            self.assertEqual(get.call_args_list[1].kwargs["params"]["pageToken"], "next")

    def test_search_console_never_falls_back_to_another_site(self):
        self.assertIsNone(search_console._pick_site_url(["sc-domain:other.example"], "one.example"))

    def test_ga_column_migrates_existing_sites_without_losing_data(self):
        from app import db
        legacy = create_engine("sqlite://")
        try:
            with legacy.begin() as conn:
                conn.execute(text("CREATE TABLE sites (id VARCHAR PRIMARY KEY, hostname VARCHAR)"))
                conn.execute(text("INSERT INTO sites VALUES ('keep', 'keep.example')"))
            with patch.object(db, "engine", legacy):
                _add_missing_columns()
                _add_missing_columns()
            self.assertIn("ga_property", {column["name"] for column in inspect(legacy).get_columns("sites")})
            with legacy.connect() as conn:
                self.assertEqual(tuple(conn.execute(text("SELECT hostname, ga_property FROM sites")).one()), ("keep.example", None))
        finally:
            legacy.dispose()

    def test_settings_has_no_invented_allowances_or_active_subscription(self):
        result = self.client.get("/api/settings", headers=self.headers).json()
        self.assertFalse(result["plan"]["subscribed"])
        self.assertFalse(result["plan"]["checkout_available"])
        self.assertEqual(result["plan"]["state"], "Not subscribed")
        self.assertTrue(all(row["cap"] is None for row in result["usage"]))

    def test_frontend_signup_contract(self):
        from pathlib import Path
        source = (Path(__file__).parent / "frontend/components/auth-form.tsx").read_text(encoding="utf-8")
        self.assertIn('window.location.replace("/projects")', source)
        self.assertIn('full_name: fullName, company', source)
        self.assertNotIn('name="website"', source)


if __name__ == "__main__":
    unittest.main()
