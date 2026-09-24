"""app/db.py:_migrate_site_scoped_google_integrations -- the data migration
for accounts that connected Google Analytics/Search Console before
2026-09-23, when those Integration rows moved from site_id-scoped to
account_id-scoped (see Integration's docstring in app/models.py). Without
this, a real production refresh token sits in a row the new account-scoped
lookup can never find again.

No network: SQLite in-memory, engine and SessionLocal both patched so
session_scope() (which the migration function uses internally) operates on
the test database.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import config, db as app_db
from app.models import Account, Base, Integration, Secret, Site
from app.secrets_store import read_secret, store_secret


class MigrateGoogleIntegrationsTests(unittest.TestCase):
    def setUp(self):
        self.key = patch.object(config, "SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.key.start()
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.patches = [
            patch.object(app_db, "engine", self.engine),
            patch.object(app_db, "SessionLocal", self.SessionLocal),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.key.stop()
        self.engine.dispose()

    def db(self):
        return Session(self.engine)

    def test_a_single_old_row_is_promoted_in_place(self):
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.commit()
            ref = store_secret(session, {"refresh_token": "real-token"})
            session.add(Integration(id="integ-1", site_id="site-1", platform="google_analytics",
                                    credential_ref=ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db._migrate_site_scoped_google_integrations()

        with self.db() as session:
            rows = session.scalars(select(Integration)).all()
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.id, "integ-1")
            self.assertIsNone(row.site_id)
            self.assertEqual(row.account_id, "a")
            # The credential itself survives -- this is a re-scope, not a reconnect.
            self.assertEqual(read_secret(session, row.credential_ref), {"refresh_token": "real-token"})

    def test_the_most_recently_connected_of_several_old_rows_wins(self):
        now = datetime.now(timezone.utc)
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.add(Site(id="site-2", account_id="a", hostname="two.example"))
            session.commit()
            old_ref = store_secret(session, {"refresh_token": "old"})
            new_ref = store_secret(session, {"refresh_token": "new"})
            session.add(Integration(id="integ-old", site_id="site-1", platform="google_analytics",
                                    credential_ref=old_ref, connected_at=now - timedelta(days=10)))
            session.add(Integration(id="integ-new", site_id="site-2", platform="google_analytics",
                                    credential_ref=new_ref, connected_at=now))
            session.commit()
            self.assertEqual(session.scalar(select(func.count()).select_from(Secret)), 2)

        app_db._migrate_site_scoped_google_integrations()

        with self.db() as session:
            rows = session.scalars(select(Integration)).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].id, "integ-new")
            self.assertEqual(read_secret(session, rows[0].credential_ref), {"refresh_token": "new"})
            # The older row's secret is gone too, not left orphaned.
            self.assertEqual(session.scalar(select(func.count()).select_from(Secret)), 1)

    def test_old_rows_are_dropped_not_merged_when_an_account_scoped_row_already_exists(self):
        """A real reconnect already happened since the deploy -- the account-
        scoped row it created is authoritative, and the stale rows plus their
        secrets are removed, not guessed at."""
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.commit()
            old_ref = store_secret(session, {"refresh_token": "old"})
            real_ref = store_secret(session, {"refresh_token": "reconnected"})
            session.add(Integration(id="integ-old", site_id="site-1", platform="google_analytics",
                                    credential_ref=old_ref, connected_at=datetime.now(timezone.utc)))
            session.add(Integration(id="integ-real", account_id="a", platform="google_analytics",
                                    credential_ref=real_ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db._migrate_site_scoped_google_integrations()

        with self.db() as session:
            rows = session.scalars(select(Integration)).all()
            self.assertEqual([r.id for r in rows], ["integ-real"])
            self.assertEqual(read_secret(session, rows[0].credential_ref), {"refresh_token": "reconnected"})
            self.assertEqual(session.scalar(select(func.count()).select_from(Secret)), 1)

    def test_a_row_pointing_at_a_deleted_site_is_removed(self):
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.commit()
            ref = store_secret(session, {"refresh_token": "orphaned"})
            session.add(Integration(id="integ-1", site_id="does-not-exist", platform="google_analytics",
                                    credential_ref=ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db._migrate_site_scoped_google_integrations()

        with self.db() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Integration)), 0)

    def test_running_twice_is_a_no_op_the_second_time(self):
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.commit()
            ref = store_secret(session, {"refresh_token": "real-token"})
            session.add(Integration(id="integ-1", site_id="site-1", platform="google_analytics",
                                    credential_ref=ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db._migrate_site_scoped_google_integrations()
        app_db._migrate_site_scoped_google_integrations()   # must not raise or touch anything further

        with self.db() as session:
            rows = session.scalars(select(Integration)).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].account_id, "a")

    def test_init_db_actually_calls_this_migration(self):
        """Not just that the function works in isolation -- that startup
        really reaches it. Disabling this call would leave every real
        pre-2026-09-23 Google connection orphaned with nothing to fix it."""
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.commit()
            ref = store_secret(session, {"refresh_token": "real-token"})
            session.add(Integration(id="integ-1", site_id="site-1", platform="google_analytics",
                                    credential_ref=ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db.init_db()

        with self.db() as session:
            row = session.get(Integration, "integ-1")
            self.assertIsNone(row.site_id)
            self.assertEqual(row.account_id, "a")

    def test_site_scoped_cms_integrations_are_left_alone(self):
        """Only Google Analytics/Search Console are affected -- WordPress,
        Shopify, Webflow, Wix and GitHub stay site_id-scoped by design."""
        with self.db() as session:
            session.add(Account(id="a", name="A", slug="a"))
            session.add(Site(id="site-1", account_id="a", hostname="one.example"))
            session.commit()
            ref = store_secret(session, {"password": "hunter2"})
            session.add(Integration(id="integ-wp", site_id="site-1", platform="wordpress",
                                    credential_ref=ref, connected_at=datetime.now(timezone.utc)))
            session.commit()

        app_db._migrate_site_scoped_google_integrations()

        with self.db() as session:
            row = session.get(Integration, "integ-wp")
            self.assertIsNotNone(row)
            self.assertEqual(row.site_id, "site-1")
            self.assertIsNone(row.account_id)


class AddMissingUniqueConstraintTests(unittest.TestCase):
    def test_skipped_on_sqlite_not_attempted(self):
        """SQLite has no ADD CONSTRAINT for an existing table -- if the
        dialect gate were removed, this would raise rather than quietly do
        nothing, so a real sqlite engine proves the gate."""
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        with patch.object(app_db, "engine", engine):
            app_db._add_missing_unique_constraints()   # must not raise
        engine.dispose()

    def test_runs_on_postgres(self):
        """Verified against the actual SQL text emitted, since no real
        Postgres is reachable here."""
        from unittest.mock import MagicMock
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            from sqlalchemy import text as sql_text
            conn.execute(sql_text("CREATE TABLE integrations (id VARCHAR PRIMARY KEY, "
                                  "account_id VARCHAR, platform VARCHAR NOT NULL)"))
        object.__setattr__(engine.dialect, "name", "postgresql")
        executed = []
        fake_conn = MagicMock()
        fake_conn.execute.side_effect = lambda stmt: executed.append(str(stmt))
        fake_begin = MagicMock()
        fake_begin.__enter__.return_value = fake_conn
        fake_begin.__exit__.return_value = False
        with patch.object(app_db, "engine", engine), \
                patch.object(engine, "begin", return_value=fake_begin):
            app_db._add_missing_unique_constraints()
        self.assertEqual(len(executed), 1)
        self.assertIn("ALTER TABLE integrations ADD CONSTRAINT "
                      "uq_integration_account_platform UNIQUE (account_id, platform)", executed[0])
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
