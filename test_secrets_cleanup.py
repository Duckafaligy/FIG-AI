"""Stored credentials are deleted when an integration is disconnected or replaced.

Before this, `disconnect()` deleted the Integration row and left its encrypted
Google token or WordPress password in the `secrets` table for good, so a
privacy policy promising "disconnect removes your token" would have been false.
No network: the WordPress connection test is faked.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, publishing
from app.models import Account, Base, Integration, Secret, Site
from app.secrets_store import read_secret, store_secret


class SecretCleanupTests(unittest.TestCase):
    def setUp(self):
        self.key = patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.key.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Account(id="a", name="A", slug="a"))
        self.db.add(Account(id="b", name="B", slug="b"))
        self.db.add(Site(id="s", account_id="a", hostname="a.example"))
        self.db.commit()
        self.account = self.db.get(Account, "a")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.key.stop()

    def secrets(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Secret))

    def test_disconnect_deletes_the_stored_credential(self):
        ref = store_secret(self.db, {"refresh_token": "1//secret"})
        integ = Integration(site_id="s", platform="google_analytics", credential_ref=ref)
        self.db.add(integ)
        self.db.commit()
        self.assertEqual(self.secrets(), 1)
        publishing.disconnect(self.db, self.account, integ.id)
        self.assertEqual(self.secrets(), 0)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Integration)), 0)

    def test_disconnect_of_a_pending_placeholder_does_not_fail(self):
        integ = Integration(site_id="s", platform="shopify", credential_ref="pending:s:shopify")
        self.db.add(integ)
        self.db.commit()
        publishing.disconnect(self.db, self.account, integ.id)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Integration)), 0)

    def test_someone_elses_integration_cannot_be_disconnected(self):
        from fastapi import HTTPException
        ref = store_secret(self.db, {"k": "v"})
        integ = Integration(site_id="s", platform="wordpress", credential_ref=ref)
        self.db.add(integ)
        self.db.commit()
        with self.assertRaises(HTTPException):
            publishing.disconnect(self.db, self.db.get(Account, "b"), integ.id)
        self.assertEqual(self.secrets(), 1)                  # untouched
        self.assertEqual(read_secret(self.db, ref), {"k": "v"})

    def test_reconnecting_wordpress_replaces_rather_than_accumulates(self):
        with patch.object(publishing.wordpress, "test_connection", return_value=(True, "ok")):
            publishing.connect(self.db, self.account, "s", "wordpress", "https://a.example", "user:pass1234")
            publishing.connect(self.db, self.account, "s", "wordpress", "https://a.example", "user:pass5678")
        self.assertEqual(self.secrets(), 1)
        integ = self.db.scalars(select(Integration)).one()
        self.assertEqual(read_secret(self.db, integ.credential_ref)["application_password"], "pass5678")

    def test_a_failed_reconnect_drops_the_old_credential(self):
        with patch.object(publishing.wordpress, "test_connection", return_value=(True, "ok")):
            publishing.connect(self.db, self.account, "s", "wordpress", "https://a.example", "user:pass1234")
        self.assertEqual(self.secrets(), 1)
        with patch.object(publishing.wordpress, "test_connection", return_value=(False, "401")):
            publishing.connect(self.db, self.account, "s", "wordpress", "https://a.example", "user:wrong")
        self.assertEqual(self.secrets(), 0)                  # nothing points at it, so nothing keeps it


if __name__ == "__main__":
    unittest.main()
