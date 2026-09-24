"""The job queue's recovery of orphaned work. No network, in-memory database."""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"
os.environ["FIG_DB_STRICT"] = "1"

import contextlib
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import jobs
from app.models import Account, Base, Finding, Job, Page, Scan, Site

NOW = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)


def naive(delta: timedelta) -> datetime:
    return (NOW - delta).replace(tzinfo=None)


class ReclaimTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a"))
            db.add(Site(id="s", account_id="a", hostname="a.example"))
            db.commit()

        @contextlib.contextmanager
        def scope():
            with Session(self.engine) as db:
                yield db
                db.commit()
        self.patch = patch.object(jobs, "session_scope", scope)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.engine.dispose()

    def running_job(self, name, claimed_ago, attempts=1, scan_status="running", partial=False):
        with Session(self.engine) as db:
            scan = Scan(id=f"scan-{name}", site_id="s", status=scan_status, trigger="manual")
            db.add(scan)
            db.flush()
            if partial:
                db.add(Page(scan_id=scan.id, url="https://a.example/"))
                db.add(Finding(scan_id=scan.id, check="x", layer="craft", severity="low", summary="s"))
            db.add(Job(id=f"job-{name}", kind="scan", status="running", attempts=attempts,
                       payload={"scan_id": scan.id}, claimed_at=naive(claimed_ago),
                       created_at=naive(claimed_ago)))
            db.commit()

    def state(self, name):
        with Session(self.engine) as db:
            job, scan = db.get(Job, f"job-{name}"), db.get(Scan, f"scan-{name}")
            return job.status, scan.status, job.error, len(scan.pages), len(scan.findings)

    def test_a_recent_orphan_is_requeued_clean(self):
        self.running_job("o", timedelta(minutes=45), partial=True)
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 1, "failed": 0})
        job, scan, err, pages, findings = self.state("o")
        self.assertEqual((job, scan), ("queued", "queued"))
        self.assertIn("restarted", err)
        self.assertEqual((pages, findings), (0, 0))       # the rerun starts from nothing

    def test_a_running_job_that_is_still_fresh_is_left_alone(self):
        self.running_job("live", timedelta(minutes=3))
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 0})
        self.assertEqual(self.state("live")[:2], ("running", "running"))

    def test_an_orphan_out_of_attempts_is_failed_with_a_reason(self):
        self.running_job("spent", timedelta(minutes=45), attempts=3)
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 1})
        job, scan, err, *_ = self.state("spent")
        self.assertEqual((job, scan), ("failed", "failed"))
        self.assertTrue(err)

    def test_a_day_old_orphan_is_failed_not_rerun(self):
        self.running_job("old", timedelta(hours=26))
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 1})
        self.assertEqual(self.state("old")[:2], ("failed", "failed"))

    def test_a_finished_scan_is_never_downgraded(self):
        self.running_job("done", timedelta(hours=26), scan_status="done")
        jobs.reclaim_stale(NOW)
        self.assertEqual(self.state("done")[:2], ("failed", "done"))

    def test_queued_and_finished_jobs_are_untouched(self):
        with Session(self.engine) as db:
            db.add(Job(id="q", kind="scan", status="queued", payload={}, claimed_at=None))
            db.add(Job(id="f", kind="scan", status="done", payload={}, claimed_at=naive(timedelta(days=3))))
            db.commit()
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 0})
        with Session(self.engine) as db:
            self.assertEqual(db.get(Job, "q").status, "queued")
            self.assertEqual(db.get(Job, "f").status, "done")

    def test_it_is_idempotent(self):
        self.running_job("o", timedelta(minutes=45))
        jobs.reclaim_stale(NOW)
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 0})

    def test_an_abandoned_job_releases_the_accounts_reserved_quota(self):
        with Session(self.engine) as db:
            db.get(Account, "a").plan = "standard"
            db.get(Account, "a").scans_used_this_period = 1
            db.commit()
        self.running_job("spent", timedelta(minutes=45), attempts=3)
        self.assertEqual(jobs.reclaim_stale(NOW), {"requeued": 0, "failed": 1})
        with Session(self.engine) as db:
            self.assertEqual(db.get(Account, "a").scans_used_this_period, 0)


class QuotaTests(unittest.TestCase):
    """Plan-based scan quota reservation and release (PLAN-DECISIONS.md:
    "a bulk audit consumes one scan per website", "failed jobs release
    reserved quota", "monitoring counts toward the same quota" -- the last
    is why the reservation lives in `enqueue_scan` itself, the one function
    every caller -- manual audit, audit_all, the Watch scheduler -- goes
    through)."""

    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def seed(self, plan=None, scans_used=0):
        with Session(self.engine) as db:
            db.add(Account(id="a", name="A", slug="a", plan=plan, scans_used_this_period=scans_used))
            db.add(Site(id="s", account_id="a", hostname="a.example"))
            db.commit()

    def used(self):
        with Session(self.engine) as db:
            return db.get(Account, "a").scans_used_this_period

    def test_enqueue_scan_reserves_one_scan_for_a_plan_account(self):
        self.seed(plan="standard", scans_used=5)
        with Session(self.engine) as db:
            jobs.enqueue_scan(db, "s")
            db.commit()
        self.assertEqual(self.used(), 6)

    def test_enqueue_scan_does_not_touch_the_counter_without_a_plan(self):
        self.seed(plan=None)
        with Session(self.engine) as db:
            jobs.enqueue_scan(db, "s")
            db.commit()
        self.assertEqual(self.used(), 0)

    def test_enqueue_estate_caps_at_the_remaining_quota(self):
        self.seed(plan="standard", scans_used=98)   # 2 remaining of 100
        with Session(self.engine) as db:
            db.add(Site(id="s2", account_id="a", hostname="b.example"))
            db.add(Site(id="s3", account_id="a", hostname="c.example"))
            db.commit()
        with Session(self.engine) as db:
            scans = jobs.enqueue_estate(db, "a")
            db.commit()
        self.assertEqual(len(scans), 2)
        self.assertEqual(self.used(), 100)

    def test_enqueue_estate_is_uncapped_without_a_plan(self):
        self.seed(plan=None)
        with Session(self.engine) as db:
            db.add(Site(id="s2", account_id="a", hostname="b.example"))
            db.commit()
        with Session(self.engine) as db:
            scans = jobs.enqueue_estate(db, "a")
            db.commit()
        self.assertEqual(len(scans), 2)

    def test_a_finalized_failed_scan_releases_its_reserved_quota(self):
        self.seed(plan="standard", scans_used=0)
        with Session(self.engine) as db:
            scan = jobs.enqueue_scan(db, "s")
            db.commit()
            site_id = scan.site_id
        self.assertEqual(self.used(), 1)
        with Session(self.engine) as db:
            jobs._release_quota(db, site_id)
            db.commit()
        self.assertEqual(self.used(), 0)

    def test_release_quota_never_goes_negative(self):
        self.seed(plan="standard", scans_used=0)
        with Session(self.engine) as db:
            jobs._release_quota(db, "s")
            db.commit()
        self.assertEqual(self.used(), 0)


if __name__ == "__main__":
    unittest.main()
