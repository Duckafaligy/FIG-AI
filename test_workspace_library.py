"""Isolated workspace API contract tests. Never uses the configured database."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"
os.environ["FIG_DEV_NO_AUTH"] = "0"

import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
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

    def test_someone_elses_post_looks_the_same_as_a_missing_one(self):
        foreign = self.create(account="b", site="site-b").json()["id"]
        theirs = self.client.get("/api/content/" + foreign, headers=self.headers)
        missing = self.client.get("/api/content/no-such-post", headers=self.headers)
        self.assertEqual(theirs.status_code, missing.status_code)
        self.assertEqual(theirs.text, missing.text)
        moved = self.client.post("/api/content/" + foreign + "/move", headers=self.headers, json={"to": "in_progress"})
        gone = self.client.post("/api/content/no-such-post/move", headers=self.headers, json={"to": "in_progress"})
        self.assertEqual(moved.text, gone.text)

    def test_pagination_and_validation(self):
        for title in ["One", "Two", "100% literal"]:
            self.create(title)
        self.assertEqual(len(self.client.get("/api/content?limit=2", headers=self.headers).json()["items"]), 2)
        self.assertEqual(self.client.get("/api/content?q=%25", headers=self.headers).json()["total"], 1)
        self.assertEqual(self.client.get("/api/content?state=invalid", headers=self.headers).status_code, 422)
        self.assertEqual(self.client.get("/api/content?limit=500", headers=self.headers).status_code, 422)


if __name__ == "__main__":
    unittest.main()
