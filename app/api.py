"""The /v1 API.

This is the primary interface, not an afterthought behind the dashboard. A
partner embedding FIG needs to add a site, trigger a read and pull the result
from inside their own product — the dashboard in this repo is just the first
consumer of these same endpoints.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_account
from app.db import get_session
from app.jobs import enqueue_estate, enqueue_scan, queue_depth
from app.models import Account, Finding, Page, Scan, Site
from app.rules.checks import checklist
from app.rules.scoring import LAYER_LABEL, LAYER_SUB, verdict
from app.validation import ValidationError, assert_public_host, normalise_target
from app.verification import generate_verification_token, verify_via_dns_txt, verify_via_meta_tag

router = APIRouter(prefix="/v1", tags=["v1"])


def _rejected(value: str, exc: ValidationError) -> HTTPException:
    return HTTPException(422, {"code": exc.code, "message": exc.message, "input": value})


def hostname_of(value: str) -> str:
    """The syntax half of the validation system (app/validation.py): reduce
    whatever was typed to a hostname, or 422 with a stable code. No network."""
    try:
        return normalise_target(value).hostname
    except ValidationError as exc:
        raise _rejected(value, exc) from None


def public_hostname(value: str) -> str:
    """Both halves: syntax, then DNS -- the name must resolve, and only to
    public addresses. Used wherever a hostname is about to be crawled."""
    host = hostname_of(value)
    try:
        assert_public_host(host)
    except ValidationError as exc:
        raise _rejected(value, exc) from None
    return host


# --- shapes -------------------------------------------------------------


class SiteIn(BaseModel):
    hostname: str
    label: str | None = None
    client_name: str | None = Field(
        default=None,
        description="Who the partner is delivering this for. Appears on their report, not ours.",
    )
    monitor: bool = False
    monitor_days: int = 30


class SiteOut(BaseModel):
    id: str
    hostname: str
    label: str | None
    client_name: str | None
    is_active: bool
    is_verified: bool
    monitor: bool
    last_scanned_at: datetime | None
    score: int | None
    verdict: str | None

    @classmethod
    def of(cls, s: Site) -> "SiteOut":
        latest = s.latest_scan()
        return cls(
            id=s.id, hostname=s.hostname, label=s.label, client_name=s.client_name,
            is_active=s.is_active, is_verified=s.is_verified, monitor=s.monitor,
            last_scanned_at=s.last_scanned_at,
            score=latest.score if latest else None,
            verdict=verdict(latest.score) if latest and latest.score is not None else None,
        )


class FindingOut(BaseModel):
    check: str
    layer: str
    severity: str
    summary: str
    why: str | None
    fix: str | None
    evidence: list | None
    page_url: str | None
    ai_written: bool = False


class ScanOut(BaseModel):
    id: str
    site_id: str
    hostname: str
    status: str
    trigger: str
    error: str | None
    pages_crawled: int
    score: int | None
    verdict: str | None
    layers: dict | None
    created_at: datetime
    finished_at: datetime | None
    findings: list[FindingOut] | None = None


def scan_out(session: Session, scan: Scan, with_findings: bool = False) -> ScanOut:
    site = session.get(Site, scan.site_id)
    layers = None
    if scan.score is not None:
        layers = {
            "craft": scan.score_craft,
            "structure": scan.score_structure,
            "search": scan.score_search,
            "answers": scan.score_answers,
        }
    out = ScanOut(
        id=scan.id, site_id=scan.site_id, hostname=site.hostname if site else "",
        status=scan.status, trigger=scan.trigger, error=scan.error,
        pages_crawled=scan.pages_crawled, score=scan.score,
        verdict=verdict(scan.score) if scan.score is not None else None,
        layers=layers, created_at=scan.created_at, finished_at=scan.finished_at,
    )
    if with_findings:
        out.findings = [
            FindingOut(check=f.check, layer=f.layer, severity=f.severity, summary=f.summary,
                       why=f.why, fix=f.fix, evidence=f.evidence, page_url=f.page_url,
                       ai_written=f.ai_written)
            for f in scan.findings
        ]
    return out


# --- account ------------------------------------------------------------


@router.get("/account")
def get_account(account: Account = Depends(require_account),
                session: Session = Depends(get_session)):
    n = account.billable_sites()
    return {
        "id": account.id, "name": account.name, "slug": account.slug, "kind": account.kind,
        "white_label": account.white_label, "brand_name": account.brand_name,
        "sites": n, "site_floor": account.site_floor,
        "rate_cents": account.rate_override_cents or Account.rate_for(n),
        "monthly_cents": account.monthly_cents(),
        "queue": queue_depth(session),
    }


@router.get("/layers")
def get_layers():
    """What the four scores mean. Partners rendering their own UI need this."""
    return [
        {"key": k, "label": LAYER_LABEL[k], "sub": LAYER_SUB[k]}
        for k in ("craft", "structure", "search", "answers")
    ]


@router.get("/checklist")
def get_checklist():
    """Every deterministic check FIG runs, and what triggers it — no auth
    required, no scan required. Lets a user (or a partner's UI) see what a
    scan actually looks for, independent of any one result."""
    return checklist()


# --- sites --------------------------------------------------------------


@router.get("/sites", response_model=list[SiteOut])
def list_sites(account: Account = Depends(require_account),
               session: Session = Depends(get_session),
               active_only: bool = Query(default=False)):
    q = select(Site).where(Site.account_id == account.id)
    if active_only:
        q = q.where(Site.is_active.is_(True))
    return [SiteOut.of(s) for s in session.scalars(q).all()]


@router.post("/sites", response_model=SiteOut, status_code=201)
def add_site(body: SiteIn, account: Account = Depends(require_account),
             session: Session = Depends(get_session)):
    """Provisioning. A partner calls this when their own customer turns the
    feature on; the site starts billing from here."""
    host = public_hostname(body.hostname)
    existing = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.hostname == host)
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            session.commit()
        return SiteOut.of(existing)

    site = Site(account_id=account.id, hostname=host, label=body.label,
                client_name=body.client_name, monitor=body.monitor,
                monitor_days=body.monitor_days)
    session.add(site)
    session.commit()
    return SiteOut.of(site)


def _owned(session: Session, account: Account, site_id: str) -> Site:
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")
    return site


@router.get("/sites/{site_id}", response_model=SiteOut)
def get_site(site_id: str, account: Account = Depends(require_account),
             session: Session = Depends(get_session)):
    return SiteOut.of(_owned(session, account, site_id))


@router.delete("/sites/{site_id}")
def deactivate_site(site_id: str, account: Account = Depends(require_account),
                    session: Session = Depends(get_session)):
    """Deactivate rather than delete: the scan history is what makes a
    before-and-after report possible, and billing stops either way."""
    site = _owned(session, account, site_id)
    site.is_active = False
    site.monitor = False
    session.commit()
    return {"id": site.id, "is_active": False}


# --- scans --------------------------------------------------------------


@router.post("/sites/{site_id}/scans", response_model=ScanOut, status_code=202)
def start_scan(site_id: str, account: Account = Depends(require_account),
               session: Session = Depends(get_session),
               max_pages: int | None = Query(default=None, ge=1, le=500)):
    site = _owned(session, account, site_id)
    scan = enqueue_scan(session, site.id, trigger="api", max_pages=max_pages)
    session.commit()
    return scan_out(session, scan)


@router.post("/scans", response_model=list[ScanOut], status_code=202)
def start_estate_scan(account: Account = Depends(require_account),
                      session: Session = Depends(get_session)):
    """Every active site on the account, queued at once. This is the estate
    scan an agency runs across a client list."""
    scans = enqueue_estate(session, account.id, trigger="api")
    session.commit()
    return [scan_out(session, s) for s in scans]


def _owned_scan(session: Session, account: Account, scan_id: str) -> Scan:
    scan = session.get(Scan, scan_id)
    site = session.get(Site, scan.site_id) if scan is not None else None
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such scan")
    return scan


@router.get("/scans/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: str, account: Account = Depends(require_account),
             session: Session = Depends(get_session),
             findings: bool = Query(default=True)):
    scan = _owned_scan(session, account, scan_id)
    return scan_out(session, scan, with_findings=findings)


@router.get("/scans/{scan_id}/trace")
def get_scan_trace(scan_id: str, account: Account = Depends(require_account),
                   session: Session = Depends(get_session)):
    """How the scan went, stage by stage: validation, robots.txt, discovery,
    every page read or skipped and why, rules, the AI step's model and token
    cost, scoring. Null for scans that ran before tracing existed."""
    scan = _owned_scan(session, account, scan_id)
    return {"scan_id": scan.id, "status": scan.status, "error": scan.error,
            "trace": scan.trace}


@router.get("/scans/{scan_id}/pages")
def get_scan_pages(scan_id: str, account: Account = Depends(require_account),
                   session: Session = Depends(get_session)):
    _owned_scan(session, account, scan_id)
    pages = session.scalars(select(Page).where(Page.scan_id == scan_id)).all()
    return [
        {"url": p.url, "path": p.path, "title": p.title, "status": p.status_code,
         "words": p.word_count, "sections": p.section_roles}
        for p in pages
    ]


# --- estate roll-up ------------------------------------------------------


@router.get("/report")
def estate_report(account: Account = Depends(require_account),
                  session: Session = Depends(get_session)):
    """One payload a partner can render as their own client-facing report:
    every site, worst first, with the headline findings for each."""
    sites = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.is_active.is_(True))
    ).all()

    rows = []
    for s in sites:
        latest = s.latest_scan()
        top = []
        if latest:
            seen: set[str] = set()
            for f in latest.findings:
                if f.check in seen:
                    continue
                seen.add(f.check)
                top.append({"check": f.check, "layer": f.layer, "severity": f.severity,
                            "summary": f.summary, "fix": f.fix})
                if len(top) == 3:
                    break
        rows.append({
            "site_id": s.id, "hostname": s.hostname, "client": s.client_name,
            "score": latest.score if latest else None,
            "verdict": verdict(latest.score) if latest and latest.score is not None else None,
            "layers": {
                "craft": latest.score_craft, "structure": latest.score_structure,
                "search": latest.score_search, "answers": latest.score_answers,
            } if latest else None,
            "pages": latest.pages_crawled if latest else 0,
            "scanned_at": latest.finished_at if latest else None,
            "top_findings": top,
        })

    rows.sort(key=lambda r: (r["score"] is None, r["score"] if r["score"] is not None else 999))
    scored = [r["score"] for r in rows if r["score"] is not None]
    return {
        "account": {"name": account.name, "slug": account.slug,
                    "brand": account.brand_name if account.white_label else "FIG",
                    "white_label": account.white_label},
        "sites": len(rows),
        "scanned": len(scored),
        "average_score": round(sum(scored) / len(scored)) if scored else None,
        "rows": rows,
    }


# --- ownership proof -----------------------------------------------------


class VerifyStart(BaseModel):
    method: str = "dns_txt"


@router.post("/sites/{site_id}/verification")
def start_verification(site_id: str, body: VerifyStart,
                       account: Account = Depends(require_account),
                       session: Session = Depends(get_session)):
    """Only needed to schedule monitoring — never for a one-off read. Locking
    one-off reads behind ownership would kill studying any public site to
    learn from it, which is the whole free tier."""
    if body.method not in ("dns_txt", "meta_tag"):
        raise HTTPException(400, "method must be 'dns_txt' or 'meta_tag'")
    site = _owned(session, account, site_id)
    token = generate_verification_token()
    site.verification_token = token
    site.verification_method = body.method
    session.commit()
    if body.method == "dns_txt":
        how = f"Add a DNS TXT record on {site.hostname} with the value: {token}"
    else:
        how = f'Add <meta name="ai-tell-verification" content="{token}"> to the homepage <head>.'
    return {"hostname": site.hostname, "method": body.method, "token": token,
            "instructions": how}


@router.post("/sites/{site_id}/verification/confirm")
def confirm_verification(site_id: str, account: Account = Depends(require_account),
                         session: Session = Depends(get_session)):
    site = _owned(session, account, site_id)
    if not site.verification_token:
        raise HTTPException(404, "no pending verification for this site")
    if site.verification_method == "dns_txt":
        ok = verify_via_dns_txt(site.hostname, site.verification_token)
    else:
        ok = verify_via_meta_tag(f"https://{site.hostname}", site.verification_token)
    if ok:
        site.is_verified = True
        site.verified_at = datetime.utcnow()
        session.commit()
    return {"hostname": site.hostname, "verified": ok}
