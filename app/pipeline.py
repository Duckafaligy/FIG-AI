"""One scan, end to end: crawl → rules → score → persist.

The only optional step is ai_explain, and it runs last, on already-flagged
structured data. Pull the API key and everything here still works — the
findings just keep the explanation the rule shipped with.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import AI_EXPLAIN_ENABLED, DOMAIN_CACHE_HOURS, MAX_PAGES_PER_SCAN
from app.models import Finding, Page, Scan, Site
from app.rules.checks import Flag, run_all_checks
from app.rules.scoring import summarise
from app.rules.sections import roles_for
from app.scraper import ScrapeError, crawl

log = logging.getLogger("fig.pipeline")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; compare like with like."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_cached(site: Site) -> bool:
    """The free path re-reads a domain at most once a week (CLAUDE.md's
    per-domain cache). If fifty people watch the same site it is crawled once."""
    last = _aware(site.last_scanned_at)
    if last is None:
        return False
    return _now() - last < timedelta(hours=DOMAIN_CACHE_HOURS)


def run_scan(session: Session, scan_id: str, max_pages: int = MAX_PAGES_PER_SCAN) -> Scan:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise ValueError(f"no scan {scan_id}")

    site = session.get(Site, scan.site_id)
    scan.status = "running"
    scan.started_at = _now()
    scan.pages_requested = max_pages
    session.commit()

    try:
        signals = crawl(site.hostname, max_pages=max_pages)
    except ScrapeError as exc:
        scan.status = "failed"
        scan.error = str(exc)
        scan.finished_at = _now()
        session.commit()
        return scan

    if not signals:
        scan.status = "failed"
        scan.error = "nothing could be read at this hostname"
        scan.finished_at = _now()
        session.commit()
        return scan

    all_flags: list[Flag] = []
    for sig in signals:
        session.add(Page(
            scan_id=scan.id,
            url=sig.url,
            path=_path(sig.url),
            title=sig.title[:300] if sig.title else None,
            status_code=sig.status_code,
            word_count=sig.word_count,
            section_roles=roles_for(sig),
        ))
        all_flags.extend(run_all_checks(sig))

    all_flags = _explain(all_flags)

    for f in all_flags:
        session.add(Finding(
            scan_id=scan.id,
            page_url=f.page_url or None,
            check=f.check,
            layer=f.layer,
            severity=f.severity,
            weight=f.weight,
            summary=f.summary,
            why=f.why or None,
            fix=f.fix or None,
            evidence=list(f.evidence) if f.evidence else None,
            count=f.count,
            ai_written=getattr(f, "ai_written", False),
        ))

    result = summarise(all_flags, pages=len(signals))
    scan.score = result["overall"]
    scan.score_craft = result["layers"]["craft"]
    scan.score_structure = result["layers"]["structure"]
    scan.score_search = result["layers"]["search"]
    scan.score_answers = result["layers"]["answers"]
    scan.pages_crawled = len(signals)
    scan.status = "done"
    scan.finished_at = _now()

    site.last_scanned_at = scan.finished_at
    session.commit()
    _record_public(session, scan, all_flags)
    log.info("scan %s done: %s pages, score %s", scan.id, len(signals), scan.score)
    return scan


def _explain(flags: list[Flag]) -> list[Flag]:
    """The single optional LLM step. Never sees a page — only the already
    structured flags. Any failure leaves the rule-written text in place."""
    if not AI_EXPLAIN_ENABLED or not flags:
        return flags
    try:
        from app.ai_explain import explain_flags
        payload = [
            {"check": f.check, "summary": f.summary, "evidence": f.evidence[:4], "count": f.count}
            for f in flags
        ]
        written = explain_flags(payload)
        for flag, text in zip(flags, written):
            if isinstance(text, dict):
                if text.get("why"):
                    flag.why = text["why"]
                if text.get("fix"):
                    flag.fix = text["fix"]
                flag.ai_written = True
    except Exception as exc:                      # noqa: BLE001 — never fatal
        log.warning("ai_explain skipped: %s", exc)
    return flags


def _path(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).path or "/"


def _record_public(session: Session, scan: Scan, flags: list[Flag]) -> None:
    """Fill in the public feed row, if this scan came from the free read.

    Done here rather than when the result is fetched, so a read still shows up
    after the visitor has closed the tab.
    """
    from sqlalchemy import select
    from app.models import PublicRead

    row = session.scalars(
        select(PublicRead).where(PublicRead.scan_id == scan.id)).first()
    if row is None:
        return
    row.score = scan.score
    row.pages = scan.pages_crawled
    top = max(flags, key=lambda f: f.weight, default=None)
    if top is not None:
        row.top_check = top.check
        row.top_layer = top.layer
    session.commit()
