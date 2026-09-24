"""app/ga.py and app/search_console.py against the account-scoped Google
Integration (2026-09-23). No real network: httpx calls are faked.

The two modules degrade differently once one Integration is shared by every
site in an account (see Integration's docstring in app/models.py):
  - ga.py has no per-site matching at all, so every site in the account
    necessarily sees the same cached GA4 property -- a documented trade-off,
    not tested for "correctness" here since there isn't a correct answer to
    assert against.
  - search_console.py matches a property to each site's own hostname at
    read time instead of caching one match on the shared row, so it stays
    correct per site -- that claim IS testable, and is the point of this
    file: two sites in the same account, sharing one Integration, must each
    get their OWN matching property.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import time
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, ga, search_console
from app.models import Account, Base, Integration, Site, _now
from app.secrets_store import store_secret


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class AccountScopedIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.key = patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.key.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Account(id="a", name="A", slug="a"))
        self.db.add(Site(id="site-1", account_id="a", hostname="one.example"))
        self.db.add(Site(id="site-2", account_id="a", hostname="two.example"))
        self.db.commit()
        ref = store_secret(self.db, {
            "access_token": "tok", "refresh_token": "1//tok",
            "expires_at": time.time() + 3600,   # far future: skips the refresh call
        })
        self.db.add(Integration(account_id="a", platform="google_analytics",
                                credential_ref=ref, connected_at=_now()))
        self.db.add(Integration(account_id="a", platform="google_search_console",
                                credential_ref=ref, connected_at=_now()))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.key.stop()

    def site(self, site_id):
        return self.db.get(Site, site_id)

    # -- both modules find the account-scoped row from either site --------

    def test_ga_finds_the_account_level_integration_from_either_site(self):
        self.assertTrue(ga.is_connected(self.db, self.site("site-1")))
        self.assertTrue(ga.is_connected(self.db, self.site("site-2")))

    def test_search_console_finds_the_account_level_integration_from_either_site(self):
        self.assertTrue(search_console.is_connected(self.db, self.site("site-1")))
        self.assertTrue(search_console.is_connected(self.db, self.site("site-2")))

    def test_a_site_scoped_row_from_before_the_migration_is_no_longer_matched(self):
        """The pre-2026-09-23 shape (site_id set, account_id null) must not
        satisfy the new account-scoped lookup -- proves this is a real
        change of query, not an addition alongside the old one."""
        with Session(self.engine) as db:
            db.add(Account(id="b", name="B", slug="b"))
            db.add(Site(id="site-b", account_id="b", hostname="b.example"))
            db.commit()
            ref = store_secret(db, {"access_token": "x", "refresh_token": "y",
                                    "expires_at": time.time() + 3600})
            db.add(Integration(site_id="site-b", platform="google_analytics",
                               credential_ref=ref, connected_at=_now()))
            db.commit()
            self.assertFalse(ga.is_connected(db, db.get(Site, "site-b")))

    # -- search console stays correct per site sharing one connection -----

    def test_search_console_matches_each_sites_own_hostname_not_a_cached_one(self):
        verified = {
            "siteEntry": [
                {"siteUrl": "sc-domain:one.example"},
                {"siteUrl": "sc-domain:two.example"},
            ]
        }
        with patch("app.search_console.httpx.get", return_value=FakeResp(200, verified)) as get, \
                patch("app.search_console.httpx.post") as query:
            query.return_value = FakeResp(200, {"rows": []})
            result_1 = search_console.fetch_search_data(self.db, self.site("site-1"))
            result_2 = search_console.fetch_search_data(self.db, self.site("site-2"))
        self.assertIsNotNone(result_1)
        self.assertIsNotNone(result_2)
        # Each fetch queried its OWN matching property, not one cached from
        # the other site's call -- the actual claim this file exists to prove.
        queried_sites = [c.args[0] for c in query.call_args_list]
        self.assertTrue(any("one.example" in u for u in queried_sites))
        self.assertTrue(any("two.example" in u for u in queried_sites))
        # And the shared Integration row was never used to cache either
        # match -- the mechanism that would have made this wrong.
        integ = self.db.scalars(select(Integration).where(
            Integration.platform == "google_search_console")).one()
        self.assertIsNone(integ.endpoint)
        self.assertEqual(get.call_count, 2)          # fetched fresh both times, not cached


if __name__ == "__main__":
    unittest.main()
