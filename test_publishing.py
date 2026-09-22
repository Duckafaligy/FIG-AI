"""publish()'s dispatch logic: does an approved Change actually reach the
right platform's adapter, with the right arguments, and record the right
outcome -- against a real SQLite database, adapter network calls faked.

This existed as an if/elif on `integ.platform != wordpress.PLATFORM` before
Shopify's adapter landed; refactored to a small `_ADAPTERS` dispatch table
in the same change. No test exercised `publish()` itself before this file --
every existing adapter test called `wordpress.apply_change`/
`shopify.apply_change` directly, which proves each adapter's own HTTP
handling but not that `publish()` actually wires a real Integration's
platform, endpoint and stored credential to the right one.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, publishing
from app.models import Account, Base, Change, Finding, Integration, Scan, Site
from app.secrets_store import store_secret


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PublishDispatchTests(unittest.TestCase):
    def setUp(self):
        self.key = patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.key.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Account(id="a", name="A", slug="a"))
        self.db.add(Site(id="s", account_id="a", hostname="a.example"))
        self.db.add(Scan(id="scan-1", site_id="s", status="done"))
        self.db.commit()
        self.account = self.db.get(Account, "a")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.key.stop()

    def _approved_change(self, *, check: str, kind: str = "meta") -> Change:
        finding = Finding(scan_id="scan-1", check=check, summary=check)
        self.db.add(finding)
        self.db.commit()
        change = Change(site_id="s", finding_id=finding.id, page_url="https://a.example/p",
                        kind=kind, title=check, state="approved")
        self.db.add(change)
        self.db.commit()
        return change

    def _connected(self, platform: str, endpoint: str, creds: dict) -> Integration:
        integ = Integration(site_id="s", platform=platform, endpoint=endpoint,
                            credential_ref=store_secret(self.db, creds), connected_at=_now())
        self.db.add(integ)
        self.db.commit()
        return integ

    def test_a_connected_wordpress_integration_dispatches_to_the_wordpress_adapter(self):
        self._connected("wordpress", "https://a.example",
                        {"username": "jamie", "application_password": "abcd1234"})
        change = self._approved_change(check="missing_title", kind="meta")

        with patch("app.publishing.wordpress.apply_change") as fake:
            fake.return_value = (True, "title updated", "New Title")
            result = publishing.publish(self.db, self.account, change.id)

        self.assertTrue(result["ok"], result)
        fake.assert_called_once()
        args, kwargs = fake.call_args
        self.assertEqual(args[0], "https://a.example")
        self.assertEqual(args[1], "jamie")
        self.assertEqual(args[2], "abcd1234")
        self.assertEqual(kwargs["check"], "missing_title")
        self.db.refresh(change)
        self.assertEqual(change.state, "published")
        self.assertEqual(change.after, "New Title")

    def test_a_connected_shopify_integration_dispatches_to_the_shopify_adapter(self):
        self._connected("shopify", "shop.myshopify.com", {"access_token": "shpat_real"})
        change = self._approved_change(check="missing_h1", kind="heading")

        with patch("app.publishing.shopify.apply_change") as fake:
            fake.return_value = (True, "heading structure fixed", "<h1>Fixed</h1>")
            result = publishing.publish(self.db, self.account, change.id)

        self.assertTrue(result["ok"], result)
        fake.assert_called_once()
        args, kwargs = fake.call_args
        self.assertEqual(args[0], "shop.myshopify.com")
        self.assertEqual(args[1], "shpat_real")
        self.assertEqual(kwargs["check"], "missing_h1")
        self.db.refresh(change)
        self.assertEqual(change.state, "published")
        self.assertEqual(change.after, "<h1>Fixed</h1>")

    def test_a_real_adapter_failure_marks_the_change_failed_with_its_own_message(self):
        self._connected("shopify", "shop.myshopify.com", {"access_token": "shpat_real"})
        change = self._approved_change(check="missing_title")

        with patch("app.publishing.shopify.apply_change") as fake:
            fake.return_value = (False, "Shopify rejected the update: Title can't be blank", None)
            result = publishing.publish(self.db, self.account, change.id)

        self.assertFalse(result["ok"])
        self.db.refresh(change)
        self.assertEqual(change.state, "failed")
        self.assertIn("Title can't be blank", change.error)

    def test_a_connected_webflow_integration_dispatches_to_the_webflow_adapter(self):
        self._connected("webflow", "wf-site-123", {"access_token": "wf_real"})
        change = self._approved_change(check="missing_meta_description", kind="meta")

        with patch("app.publishing.webflow.apply_change") as fake:
            fake.return_value = (True, "meta description updated", "A real description.")
            result = publishing.publish(self.db, self.account, change.id)

        self.assertTrue(result["ok"], result)
        fake.assert_called_once()
        args, kwargs = fake.call_args
        self.assertEqual(args[0], "wf-site-123")
        self.assertEqual(args[1], "wf_real")
        self.assertEqual(kwargs["check"], "missing_meta_description")
        self.db.refresh(change)
        self.assertEqual(change.state, "published")

    def test_a_connected_wix_integration_dispatches_to_the_wix_adapter(self):
        self._connected("wix", None, {"instance_id": "wix-instance-1"})
        change = self._approved_change(check="missing_title", kind="meta")

        with patch.object(config, "WIX_CLIENT_ID", "cid"), \
             patch.object(config, "WIX_CLIENT_SECRET", "csecret"), \
             patch("app.publishing.wix.apply_change") as fake:
            fake.return_value = (True, "title updated", "New Title")
            result = publishing.publish(self.db, self.account, change.id)

        self.assertTrue(result["ok"], result)
        fake.assert_called_once()
        args, kwargs = fake.call_args
        self.assertEqual(args[0], "wix-instance-1")
        self.assertEqual(args[1], "cid")
        self.assertEqual(args[2], "csecret")
        self.assertEqual(kwargs["check"], "missing_title")
        self.db.refresh(change)
        self.assertEqual(change.state, "published")

    def test_an_unwired_platform_refuses_without_touching_any_adapter(self):
        self._connected("wordpress_multisite_alias", "x", {"access_token": "x"})
        change = self._approved_change(check="missing_title")

        with patch("app.publishing.wordpress.apply_change") as wp, \
             patch("app.publishing.shopify.apply_change") as sp, \
             patch("app.publishing.webflow.apply_change") as wf, \
             patch("app.publishing.wix.apply_change") as wx:
            result = publishing.publish(self.db, self.account, change.id)

        self.assertFalse(result["ok"])
        wp.assert_not_called()
        sp.assert_not_called()
        wf.assert_not_called()
        wx.assert_not_called()
        self.db.refresh(change)
        self.assertEqual(change.state, "failed")
        self.assertIn("wordpress_multisite_alias", change.error)
        self.assertIn("not implemented yet", change.error)

    def test_no_integration_at_all_refuses_before_reading_any_credential(self):
        change = self._approved_change(check="missing_title")
        result = publishing.publish(self.db, self.account, change.id)
        self.assertFalse(result["ok"])
        self.db.refresh(change)
        self.assertEqual(change.state, "failed")
        self.assertIn("No CMS is connected", change.error)

    def test_an_unapproved_change_is_refused_before_anything_else(self):
        finding = Finding(scan_id="scan-1", check="missing_title", summary="x")
        self.db.add(finding)
        self.db.commit()
        change = Change(site_id="s", finding_id=finding.id, kind="meta", title="x", state="proposed")
        self.db.add(change)
        self.db.commit()
        result = publishing.publish(self.db, self.account, change.id)
        self.assertFalse(result["ok"])
        self.assertIn("approved", result["reason"])


if __name__ == "__main__":
    unittest.main()
