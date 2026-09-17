"""The public half: the free read, and the feed of recent reads.

Two constraints shape this file.

**Cost.** A public read crawls somebody's real site and calls Claude. Both
cost money and neither should be loopable, so reads are capped per device and
per IP before any work is queued.

**The rule in CLAUDE.md.** No public leaderboard naming real sites. The feed
is therefore anonymous by default — a score, a page count, which pattern came
up, how long ago — and the domain appears only when the person who ran the
read ticks the box to share it. Nobody else's site gets named because a
stranger pointed this at it.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.api import public_hostname
from app.auth import demo_account
from app.db import get_session
from app.jobs import enqueue_scan
from app.models import Account, Finding, PublicRead, Scan, Site
from app.rules.scoring import LAYER_LABEL, verdict

router = APIRouter(tags=["public"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None)


def device_hash(request: Request, device_id: str | None) -> str:
    """A stable, one-way handle for rate limiting.

    The raw device cookie and the IP are hashed together and never stored, so
    the limits work without keeping anything that identifies a visitor.
    """
    raw = f"{device_id or ''}|{request.client.host if request.client else ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def ip_hash(request: Request) -> str:
    ip = ""
    if config.TRUST_PROXY:
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip and request.client:
        ip = request.client.host
    return hashlib.sha256((ip or "unknown").encode()).hexdigest()[:32]


def _count_since(session: Session, column, value: str, since: datetime) -> int:
    return session.scalar(
        select(func.count()).select_from(PublicRead)
        .where(column == value, PublicRead.created_at >= _naive(since))
    ) or 0


def check_limits(session: Session, dev: str, ip: str) -> None:
    day = _count_since(session, PublicRead.device_hash, dev, _now() - timedelta(days=1))
    if day >= config.PUBLIC_SCANS_PER_DAY:
        raise HTTPException(429, (
            f"That is {config.PUBLIC_SCANS_PER_DAY} free reads from this browser today. "
            "The limit is what keeps the free read free — a plan lifts it."))
    hour = _count_since(session, PublicRead.ip_hash, ip, _now() - timedelta(hours=1))
    if hour >= config.PUBLIC_SCANS_PER_HOUR_IP:
        raise HTTPException(429, "Too many reads from this network in the last hour.")
    everyone = session.scalar(
        select(func.count()).select_from(PublicRead)
        .where(PublicRead.created_at >= _naive(_now() - timedelta(days=1)))
    ) or 0
    if everyone >= config.PUBLIC_SCANS_GLOBAL_PER_DAY:
        raise HTTPException(429, "The free read has reached its daily ceiling. "
                                 "Try again tomorrow.")


# --- request/response shapes -------------------------------------------


class ReadRequest(BaseModel):
    url: str
    device_id: str | None = None
    share: bool = Field(
        default=False,
        description="Show this domain publicly in the recent-reads feed. "
                    "Off by default: nobody else's site gets named here.",
    )


def _public_account(session: Session) -> Account:
    """Public reads are parked on the demo account and marked inactive, so
    they never enter anyone's billable site count."""
    account = demo_account(session) or session.scalars(select(Account)).first()
    if account is None:
        raise HTTPException(503, "no account configured")
    return account


@router.post("/scan")
def start_public_read(body: ReadRequest, request: Request,
                      session: Session = Depends(get_session)):
    host = public_hostname(body.url)
    dev = device_hash(request, body.device_id)
    ip = ip_hash(request)
    check_limits(session, dev, ip)

    account = _public_account(session)
    site = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.hostname == host)
    ).first()
    if site is None:
        site = Site(account_id=account.id, hostname=host, is_active=False,
                    label="public read")
        session.add(site)
        session.flush()

    scan = enqueue_scan(session, site.id, trigger="demo",
                        max_pages=config.PUBLIC_SCAN_MAX_PAGES)
    session.add(PublicRead(scan_id=scan.id, hostname=host,
                           show_hostname=bool(body.share),
                           device_hash=dev, ip_hash=ip))
    session.commit()
    return {"scan_id": scan.id, "hostname": host, "status": "queued",
            "poll": f"/scan/{scan.id}"}


@router.get("/scan/{scan_id}")
def public_read_result(scan_id: str, session: Session = Depends(get_session)):
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "no such read")
    site = session.get(Site, scan.site_id)

    # Free-tier reads (trigger="demo", see start_public_read above) were
    # always meant to be public. An account-owned scan -- someone's real,
    # possibly-paying site -- only becomes public once its Site has opted
    # in. Same 404 either way: "not found" doesn't confirm a private scan
    # exists at that id.
    if scan.trigger != "demo" and not (site and site.reports_public):
        raise HTTPException(404, "no such read")

    if scan.status != "done":
        return {"scan_id": scan.id, "hostname": site.hostname if site else "",
                "status": scan.status, "error": scan.error}

    return {
        "scan_id": scan.id,
        "hostname": site.hostname if site else "",
        "status": "done",
        "pages": scan.pages_crawled,
        "score": scan.score,
        "verdict": verdict(scan.score) if scan.score is not None else None,
        "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
        "layers": {"craft": scan.score_craft, "structure": scan.score_structure,
                   "search": scan.score_search, "answers": scan.score_answers},
        "findings": [
            {"check": f.check, "layer": f.layer, "layer_label": LAYER_LABEL.get(f.layer, f.layer),
             "severity": f.severity, "summary": f.summary, "why": f.why,
             "fix": f.fix, "evidence": f.evidence or [], "page": f.page_url}
            for f in scan.findings
        ],
    }


@router.get("/reads/recent")
def recent_reads(session: Session = Depends(get_session), limit: int = 24):
    """Anonymous by default. A domain appears only where the person who ran
    the read chose to share it."""
    rows = session.scalars(
        select(PublicRead)
        .where(PublicRead.score.isnot(None))
        .order_by(PublicRead.created_at.desc())
        .limit(min(max(limit, 1), 60))
    ).all()

    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "site": r.hostname if r.show_hostname else None,
            "shared": r.show_hostname,
            "pages": r.pages,
            "score": r.score,
            "verdict": verdict(r.score) if r.score is not None else None,
            "top_check": r.top_check,
            "top_layer": LAYER_LABEL.get(r.top_layer or "", r.top_layer),
            "at": r.created_at.isoformat() if r.created_at else None,
        })

    total = session.scalar(select(func.count()).select_from(PublicRead)
                           .where(PublicRead.score.isnot(None))) or 0
    avg = session.scalar(select(func.avg(PublicRead.score))
                         .where(PublicRead.score.isnot(None)))
    common = session.execute(
        select(Finding.check, func.count().label("n"))
        .join(Scan, Scan.id == Finding.scan_id)
        .where(Scan.trigger == "demo")
        .group_by(Finding.check).order_by(func.count().desc()).limit(5)
    ).all()

    return {
        "reads": out,
        "total": total,
        "average_score": round(avg) if avg is not None else None,
        "most_common": [{"check": c, "count": n} for c, n in common],
    }
