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

    def test_pagination_and_validation(self):
        for title in ["One", "Two", "100% literal"]:
            self.create(title)
        self.assertEqual(len(self.client.get("/api/content?limit=2", headers=self.headers).json()["items"]), 2)
        self.assertEqual(self.client.get("/api/content?q=%25", headers=self.headers).json()["total"], 1)
        self.assertEqual(self.client.get("/api/content?state=invalid", headers=self.headers).status_code, 422)
        self.assertEqual(self.client.get("/api/content?limit=500", headers=self.headers).status_code, 422)


if __name__ == "__main__":
    unittest.main()
