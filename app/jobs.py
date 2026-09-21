"""The scan queue.

A DB table and a couple of worker threads. Deliberately boring — the point is
that an estate scan of 200 sites is a queue depth, not a 40-minute HTTP
request. Swapping this for Celery later means replacing the consumer, not the
pipeline.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import WORKER_COUNT
from app.db import session_scope
from app.models import Job, Scan, Site

log = logging.getLogger("fig.jobs")

_stop = threading.Event()
_threads: list[threading.Thread] = []
_claim_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- enqueue ------------------------------------------------------------


def enqueue_scan(session, site_id: str, trigger: str = "manual",
                 max_pages: int | None = None) -> Scan:
    """Create the Scan row immediately so the caller has something to poll,
    then queue the work."""
    scan = Scan(site_id=site_id, status="queued", trigger=trigger)
    session.add(scan)
    session.flush()
    session.add(Job(kind="scan", payload={"scan_id": scan.id, "max_pages": max_pages}))
    return scan


def enqueue_estate(session, account_id: str, trigger: str = "manual") -> list[Scan]:
    """Every active site on an account. This is the call an agency makes."""
    sites = session.scalars(
        select(Site).where(Site.account_id == account_id, Site.is_active.is_(True))
    ).all()
    return [enqueue_scan(session, s.id, trigger=trigger) for s in sites]


# --- consume ------------------------------------------------------------


def _claim() -> str | None:
    """Take the oldest runnable job. The lock keeps two local threads off the
    same row; on Postgres this becomes SELECT ... FOR UPDATE SKIP LOCKED."""
    with _claim_lock, session_scope() as s:
        job = s.scalars(
            select(Job)
            .where(Job.status == "queued", Job.run_after <= _now().replace(tzinfo=None))
            .order_by(Job.run_after.asc())
            .limit(1)
        ).first()
        if job is None:
            return None
        job.status = "running"
        job.claimed_at = _now()
        job.attempts += 1
        return job.id


def _run(job_id: str) -> None:
    from app.pipeline import run_scan
    from app.config import MAX_PAGES_PER_SCAN

    with session_scope() as s:
        job = s.get(Job, job_id)
        payload = dict(job.payload or {})
        kind = job.kind

    try:
        if kind == "scan":
            max_pages = payload.get("max_pages") or MAX_PAGES_PER_SCAN
            with session_scope() as s:
                run_scan(s, payload["scan_id"], max_pages=max_pages)
        else:
            raise ValueError(f"unknown job kind {kind!r}")
        status, err = "done", None
    except Exception as exc:                       # noqa: BLE001
        log.exception("job %s failed", job_id)
        status, err = "failed", f"{type(exc).__name__}: {exc}"

    with session_scope() as s:
        job = s.get(Job, job_id)
        if status == "failed" and job.attempts < job.max_attempts:
            # Back off and let it round again rather than losing the work.
            job.status = "queued"
            job.error = err
            job.run_after = (_now() + timedelta(seconds=20 * job.attempts)).replace(tzinfo=None)
        else:
            job.status = status
            job.error = err
            job.finished_at = _now()
            if status == "failed":
                scan_id = (job.payload or {}).get("scan_id")
                if scan_id:
                    scan = s.get(Scan, scan_id)
                    if scan and scan.status not in ("done",):
                        scan.status = "failed"
                        scan.error = err


# A worker that dies mid-scan (a Render restart or deploy kills the process)
# leaves its job "running" forever, and the scan spins for whoever is waiting.
# Nothing else ever puts it right, so this does. The age threshold, not "every
# running job at startup", is deliberate: on a rolling deploy the old instance
# is still legitimately running jobs while the new one boots.
STALE_AFTER = timedelta(minutes=20)      # no honest scan runs this long
ABANDON_AFTER = timedelta(hours=6)       # too old to be worth running again
RECLAIM_EVERY = 300.0


def reclaim_stale(now: datetime | None = None) -> dict:
    """Recover jobs whose worker is gone. Returns {"requeued": n, "failed": n}.

    A recent orphan with attempts left goes back in the queue, with any partial
    pages and findings dropped so the rerun starts clean. One that is out of
    attempts, or so old that whoever asked is long gone, is failed with an
    honest reason instead of retried.
    """
    now = now or _now()
    naive_now = now.replace(tzinfo=None)
    cutoff = naive_now - STALE_AFTER
    out = {"requeued": 0, "failed": 0}
    note = "the worker stopped before finishing (the service restarted mid-scan)"
    with session_scope() as s:
        stale = s.scalars(select(Job).where(
            Job.status == "running", Job.claimed_at < cutoff)).all()
        for job in stale:
            scan_id = (job.payload or {}).get("scan_id")
            scan = s.get(Scan, scan_id) if scan_id else None
            too_old = job.claimed_at < naive_now - ABANDON_AFTER
            if job.attempts < job.max_attempts and not too_old:
                job.status, job.error, job.run_after = "queued", note, naive_now
                if scan is not None and scan.status != "done":
                    scan.pages = []
                    scan.findings = []
                    scan.status = "queued"
                out["requeued"] += 1
            else:
                job.status, job.error, job.finished_at = "failed", note, now
                if scan is not None and scan.status != "done":
                    scan.status, scan.error = "failed", note
                out["failed"] += 1
    if out["requeued"] or out["failed"]:
        log.warning("reclaimed stale jobs: %s", out)
    return out


def _loop(name: str) -> None:
    log.info("worker %s up", name)
    last_reclaim = 0.0
    while not _stop.is_set():
        # One worker does the housekeeping; a failure here must never stop it
        # taking jobs.
        if name == "w1" and time.monotonic() - last_reclaim >= RECLAIM_EVERY:
            last_reclaim = time.monotonic()
            try:
                reclaim_stale()
            except Exception:                      # noqa: BLE001
                log.exception("reclaim_stale failed")
        job_id = _claim()
        if job_id is None:
            _stop.wait(1.0)
            continue
        _run(job_id)
    log.info("worker %s down", name)


def start_workers(count: int = WORKER_COUNT) -> None:
    if _threads:
        return
    _stop.clear()
    for i in range(max(1, count)):
        t = threading.Thread(target=_loop, args=(f"w{i + 1}",), daemon=True,
                             name=f"fig-worker-{i + 1}")
        t.start()
        _threads.append(t)


def stop_workers(timeout: float = 5.0) -> None:
    _stop.set()
    for t in _threads:
        t.join(timeout=timeout)
    _threads.clear()


def queue_depth(session) -> dict:
    rows = session.execute(
        select(Job.status, Job.id).where(Job.status.in_(("queued", "running")))
    ).all()
    depth = {"queued": 0, "running": 0}
    for status, _ in rows:
        depth[status] = depth.get(status, 0) + 1
    return depth


def wait_for_idle(timeout: float = 120.0) -> bool:
    """Used by the seeder and by tests. Returns False if it timed out."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with session_scope() as s:
            d = queue_depth(s)
        if d["queued"] == 0 and d["running"] == 0:
            return True
        time.sleep(0.4)
    return False
