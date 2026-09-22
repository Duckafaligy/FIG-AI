"""One scan, end to end:

    validate -> resolve base -> robots.txt -> discover -> fetch -> rules
             -> explain -> score -> persist

Every stage appends to a trace stored on the scan (`Scan.trace`, served at
GET /v1/scans/{id}/trace), so how a read went -- which scheme answered, what
robots.txt allowed, every page read or skipped and why, what the AI step cost
-- can be inspected after the fact rather than reconstructed from logs.

The only optional step is `explain`, and it runs on already-flagged structured
data. Pull the API key and everything here still works; findings keep the
explanation their rule shipped with.
"""
from __future__ import annotations

import logging
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.config import AI_EXPLAIN_ENABLED, DOMAIN_CACHE_HOURS, MAX_PAGES_PER_SCAN
from app.models import Finding, Page, PublicRead, Scan, Site
from app.rules.checks import AI_CRAWLER_TOKENS, Flag, check_ai_crawler_access, check_llms_txt, run_all_checks
from app.rules.scoring import summarise
from app.rules.sections import roles_for
from app.scraper import CrawlReport, ScrapeError, crawl, robots_rules_for
from app.validation import ValidationError, validate_target

log = logging.getLogger("fig.pipeline")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; compare like with like."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


def is_cached(site: Site) -> bool:
    """The free path re-reads a domain at most once a week (CLAUDE.md's
    per-domain cache). If fifty people watch the same site it is crawled once."""
    last = _aware(site.last_scanned_at)
    if last is None:
        return False
    return _now() - last < timedelta(hours=DOMAIN_CACHE_HOURS)


class Trace:
    """The stage-by-stage record of one scan. JSON-safe by construction."""

    def __init__(self) -> None:
        self._t0 = time.monotonic()
        self.stages: list[dict] = []

    # Positional-only (the `/`), so a detail can carry its own `status` or `ms`
    # -- robots.txt has both -- without colliding with the stage's.

    def add(self, stage: str, status: str, started: float, /, **detail) -> None:
        """A stage this module timed itself."""
        self.stages.append({"stage": stage, "status": status, "ms": _ms(started),
                            "detail": detail})

    def record(self, stage: str, status: str, ms: int, /, **detail) -> None:
        """A stage timed by the code that ran it (the crawler)."""
        self.stages.append({"stage": stage, "status": status, "ms": ms, "detail": detail})

    def as_json(self) -> dict:
        return {"version": 1, "total_ms": _ms(self._t0), "stages": list(self.stages)}


# --- grouping for the AI step --------------------------------------------


def group_flags(flags: list[Flag]) -> list[list[Flag]]:
    """One group per distinct (layer, check), in first-seen order. A check
    that fired on twelve pages is one problem to explain, not twelve calls."""
    groups: dict[tuple[str, str], list[Flag]] = {}
    for flag in flags:
        groups.setdefault((flag.layer, flag.check), []).append(flag)
    return list(groups.values())


def explanation_payload(group: list[Flag]) -> dict:
    """What ai_explain sees for one distinct finding: the rule's own summary,
    how widespread it is, and a sample of the evidence the rule already quoted.
    Small structured data -- never page content beyond that."""
    first = group[0]
    worst = max(group, key=lambda f: f.weight)
    evidence: list[str] = []
    for flag in group:
        for item in flag.evidence or []:
            text = str(item)[:200]
            if text not in evidence:
                evidence.append(text)
            if len(evidence) >= 6:
                break
        if len(evidence) >= 6:
            break
    pages = sorted({_path(f.page_url) for f in group if f.page_url})
    return {
        "layer": first.layer, "check": first.check, "severity": worst.severity,
        "summary": first.summary, "occurrences": len(group),
        "pages_affected": len(pages), "example_pages": pages[:5], "evidence": evidence,
    }


# --- the scan ------------------------------------------------------------


def run_scan(session: Session, scan_id: str, max_pages: int = MAX_PAGES_PER_SCAN) -> Scan:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise ValueError(f"no scan {scan_id}")
    site = session.get(Site, scan.site_id)

    trace = Trace()
    scan.status = "running"
    scan.started_at = _now()
    scan.pages_requested = max_pages
    scan.error = None
    scan.trace = trace.as_json()
    session.commit()

    # 1. Validation. Sites provisioned through /v1 were already checked, but a
    # hostname's DNS can change after it was added, and older rows predate
    # the validation system entirely.
    started = time.monotonic()
    try:
        target, resolution = validate_target(site.hostname)
    except ValidationError as exc:
        trace.add("validate", "failed", started, input=site.hostname,
                  code=exc.code, error=exc.message)
        return _fail(session, scan, trace, exc.message)
    trace.add("validate", "ok", started, input=site.hostname, hostname=target.hostname,
              notes=target.notes, addresses=resolution.addresses, public=True)

    # 2-5. The crawl: base resolution, robots.txt, discovery, fetching.
    report = CrawlReport()
    try:
        signals = crawl(target.hostname, max_pages=max_pages, report=report)
    except ScrapeError as exc:
        _record_crawl(trace, report, failure=exc)
        return _fail(session, scan, trace, str(exc))
    _record_crawl(trace, report)
    if not signals:
        return _fail(session, scan, trace, "nothing could be read at this hostname")

    # 6. Rules. Deterministic, $0.
    started = time.monotonic()
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
            js_dependent=sig.js_dependent,
            js_dependent_reason=sig.js_dependent_reason or None,
        ))
        all_flags.extend(run_all_checks(sig))

    # Site-level, once per scan -- not one PageSignal to check against, so
    # not part of run_all_checks(). robots_rules_for() reuses crawl()'s
    # already-cached parse; no second robots.txt fetch.
    rules = robots_rules_for(report.base_url or target.hostname)
    blocked = [name for name in AI_CRAWLER_TOKENS if not rules.allowed(name, "/")]
    for flag in (check_ai_crawler_access(blocked), check_llms_txt(report.llms_txt_present)):
        if flag is not None:
            all_flags.append(flag)

    trace.add("rules", "ok", started, pages=len(signals), flags=len(all_flags),
              distinct_checks=len({f.check for f in all_flags}),
              by_layer=dict(Counter(f.layer for f in all_flags)),
              by_check=dict(Counter(f.check for f in all_flags).most_common()))

    # 7. Explain. The one optional LLM step.
    started = time.monotonic()
    explain_status, explain_detail = _explain(group_flags(all_flags), target.hostname)
    trace.add("explain", explain_status, started, **explain_detail)

    # 8. Score.
    started = time.monotonic()
    result = summarise(all_flags, pages=len(signals))
    scan.score = result["overall"]
    scan.score_craft = result["layers"]["craft"]
    scan.score_structure = result["layers"]["structure"]
    scan.score_search = result["layers"]["search"]
    scan.score_answers = result["layers"]["answers"]
    trace.add("score", "ok", started, overall=result["overall"], verdict=result["verdict"],
              layers=result["layers"], counts=result["counts"])

    # 9. Persist.
    started = time.monotonic()
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
    scan.pages_crawled = len(signals)
    scan.status = "done"
    scan.finished_at = _now()
    site.last_scanned_at = scan.finished_at
    session.commit()
    trace.add("persist", "ok", started, pages=len(signals), findings=len(all_flags),
              ai_written=sum(1 for f in all_flags if getattr(f, "ai_written", False)))
    scan.trace = trace.as_json()
    session.commit()

    _record_public(session, scan, all_flags)
    log.info("scan %s done: %s pages, score %s, %s ms", scan.id, len(signals), scan.score,
             scan.trace["total_ms"])
    return scan


def _fail(session: Session, scan: Scan, trace: Trace, error: str) -> Scan:
    scan.status = "failed"
    scan.error = error
    scan.finished_at = _now()
    scan.trace = trace.as_json()
    session.commit()
    log.info("scan %s failed: %s", scan.id, error)
    return scan


def _record_crawl(trace: Trace, report: CrawlReport, failure: ScrapeError | None = None) -> None:
    if not report.base_url:
        trace.record("resolve_base", "failed", report.resolve_ms,
                     attempts=report.base_attempts,
                     error=str(failure) if failure else "no base URL",
                     code=failure.code if failure else "")
        return
    trace.record("resolve_base", "ok", report.resolve_ms, base_url=report.base_url,
                 attempts=report.base_attempts)

    robots = report.robots
    trace.record("robots", "ok", robots.get("ms", 0), **robots)

    trace.record("discover", "ok", report.discovery_ms, sitemaps=report.sitemaps,
                 sitemap_urls=report.sitemap_urls, same_site_urls=report.same_site_urls)

    outcomes = Counter(p["outcome"] for p in report.pages)
    trace.record("fetch", "ok" if outcomes.get("ok") else "failed", report.fetch_ms,
                 read=outcomes.get("ok", 0),
                 skipped={k: v for k, v in outcomes.items() if k != "ok"},
                 stopped=report.stopped, pages=report.pages)


def _explain(groups: list[list[Flag]], site: str = "") -> tuple[str, dict]:
    """The single optional LLM step. Never sees a page — only one structured
    item per distinct finding. Any failure leaves the rule-written text in
    place. Returns (status, detail) for the trace."""
    detail: dict = {
        "enabled": AI_EXPLAIN_ENABLED,
        "model": config.AI_MODEL if AI_EXPLAIN_ENABLED else None,
        "distinct_findings": len(groups),
        "occurrences": sum(len(g) for g in groups),
    }
    if not AI_EXPLAIN_ENABLED:
        detail["reason"] = ("no ANTHROPIC_API_KEY, or FIG_AI_EXPLAIN=0 -- findings keep "
                            "the text their rule ships with")
        return "skipped", detail
    if not groups:
        return "skipped", detail

    try:
        from app.ai_explain import explain_flags
        written, usage = explain_flags([explanation_payload(g) for g in groups], site=site)
    except Exception as exc:                      # noqa: BLE001 — never fatal
        log.warning("ai_explain skipped: %s", exc)
        detail["error"] = f"{type(exc).__name__}: {exc}"
        return "failed", detail

    explained = 0
    for group, text in zip(groups, written):
        if not (isinstance(text, dict) and (text.get("why") or text.get("fix"))):
            continue
        explained += 1
        for flag in group:
            if text.get("why"):
                flag.why = text["why"]
            if text.get("fix"):
                flag.fix = text["fix"]
            flag.ai_written = True

    detail.update(usage.as_dict())
    detail.update(explained=explained, kept_rule_text=len(groups) - explained)
    if explained == len(groups):
        return "ok", detail
    return ("partial" if explained else "failed"), detail


def _path(url: str) -> str:
    return urlparse(url).path or "/"


def _record_public(session: Session, scan: Scan, flags: list[Flag]) -> None:
    """Fill in the public feed row, if this scan came from the free read.

    Done here rather than when the result is fetched, so a read still shows up
    after the visitor has closed the tab.
    """
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
