"""Scheduled Watches.

`Site.monitor` (on/off) and `Site.monitor_days` (how often) have existed on
the model since the two-tier product design in CLAUDE.md, but nothing read
them until this module. A verified, monitored site gets an automatic
re-scan every `monitor_days` on top of whatever manual scans a person runs
-- the point being that a redesign three months from now that quietly
reintroduces generic patterns gets caught by the next Watch, not never.

A watch is a queue depth, not a special code path: `sweep()` just calls
`app.jobs.enqueue_scan`, the same entry point a manual "audit" button uses.
APScheduler only decides *when* to call it.

`FIG_WATCH_ENABLED` is off by default so a local dev run or a test doesn't
start silently enqueueing scans against real sites.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func, select

from app import config
from app.db import session_scope
from app.jobs import enqueue_scan
from app.models import Scan, Site

log = logging.getLogger("fig.scheduler")

_scheduler: BackgroundScheduler | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; compare like with like."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _due(site: Site) -> bool:
    last = _aware(site.last_scanned_at)
    if last is None:
        return True
    return _now() - last >= timedelta(days=site.monitor_days)


def _has_pending_scan(session, site_id: str) -> bool:
    """A sweep can run again before a slow scan from the last one finishes.
    Without this, every tick in between would queue another duplicate scan
    for the same site until the first one completes."""
    count = session.scalar(
        select(func.count()).select_from(Scan)
        .where(Scan.site_id == site_id, Scan.status.in_(("queued", "running")))
    )
    return bool(count)


def sweep() -> int:
    """Enqueue a scan for every verified, active, monitored site that is
    due. Returns how many were queued. Called on a timer, and safe to call
    directly for a manual run or a test."""
    queued = 0
    with session_scope() as s:
        sites = s.scalars(
            select(Site).where(
                Site.monitor.is_(True),
                Site.is_verified.is_(True),
                Site.is_active.is_(True),
            )
        ).all()
        for site in sites:
            if not _due(site) or _has_pending_scan(s, site.id):
                continue
            enqueue_scan(s, site.id, trigger="watch")
            queued += 1
    if queued:
        log.info("watch sweep queued %d scan(s)", queued)
    return queued


def start() -> None:
    global _scheduler
    if not config.WATCH_ENABLED or _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        sweep, "interval", hours=config.WATCH_SWEEP_HOURS,
        id="watch-sweep", next_run_time=_now(),
    )
    _scheduler.start()
    log.info("watch scheduler started, sweeping every %sh", config.WATCH_SWEEP_HOURS)


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
