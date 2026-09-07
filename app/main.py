"""App assembly.

    uvicorn app.main:app --reload

With nothing configured that gives you a working product on SQLite: the
dashboard at /app, the API at /v1, docs at /docs. Point DATABASE_URL at
Supabase and add the Stripe and Anthropic keys and the same code runs for
real.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.api import hostname_of, router as api_router
from app.auth import require_account
from app.billing import router as billing_router
from app.dashboard import router as dashboard_router
from app.db import IS_SQLITE, get_session, init_db
from app.jobs import queue_depth, start_workers, stop_workers
from app.models import Account, Site
from app.pipeline import is_cached
from app.rules.scoring import verdict

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("fig")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    start_workers()
    log.info("FIG up - dashboard /app, API /v1, db %s",
             "sqlite" if IS_SQLITE else "postgres")
    if config.DEV_NO_AUTH:
        log.warning("FIG_DEV_NO_AUTH=1 - the dashboard is open with no sign-in")
    yield
    stop_workers()


app = FastAPI(
    title="FIG",
    version="0.2.0",
    description=(
        "Reads a site for the patterns that make it read machine-made, whether its "
        "sections are in an order that makes sense, what a crawler can reach, and "
        "what a model has to quote. Findings are probabilistic and educational: this "
        "never claims a page 'is' AI-written."
    ),
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(config.ROOT / "static")), name="static")
app.include_router(api_router)
app.include_router(billing_router)
app.include_router(dashboard_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/app")


@app.get("/health")
def health(session: Session = Depends(get_session)):
    return {
        "status": "ok",
        "db": "sqlite" if IS_SQLITE else "postgres",
        "queue": queue_depth(session),
        "ai_explain": config.AI_EXPLAIN_ENABLED,
        "billing": config.BILLING_ENABLED,
        "dev_no_auth": config.DEV_NO_AUTH,
    }


# --- the public one-off read --------------------------------------------


class ScanRequest(BaseModel):
    url: str


@app.post("/scan", tags=["public"])
def scan_url(body: ScanRequest, session: Session = Depends(get_session),
             account: Account = Depends(require_account)):
    """The free one-off read the marketing site's demo calls.

    Cached per domain (CLAUDE.md's two-tier model): if fifty people ask about
    the same site inside the cache window it is crawled once, and the stored
    result is returned. Ownership is never required here — studying any public
    site to learn from it is the whole point of the free tier.
    """
    host = hostname_of(body.url)
    site = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.hostname == host)
    ).first()
    if site is None:
        site = Site(account_id=account.id, hostname=host, is_active=False)
        session.add(site)
        session.flush()

    latest = site.latest_scan()
    if latest and is_cached(site):
        return _scan_payload(latest, site, cached=True)

    from app.jobs import enqueue_scan
    scan = enqueue_scan(session, site.id, trigger="demo", max_pages=6)
    session.commit()
    return {"scan_id": scan.id, "hostname": host, "status": "queued",
            "poll": f"/scan/{scan.id}"}


@app.get("/scan/{scan_id}", tags=["public"])
def scan_result(scan_id: str, session: Session = Depends(get_session)):
    from app.models import Scan
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "no such scan")
    site = session.get(Site, scan.site_id)
    if scan.status != "done":
        return {"scan_id": scan.id, "hostname": site.hostname, "status": scan.status,
                "error": scan.error}
    return _scan_payload(scan, site, cached=False)


def _scan_payload(scan, site, cached: bool) -> dict:
    return {
        "scan_id": scan.id,
        "hostname": site.hostname,
        "status": scan.status,
        "cached": cached,
        "pages": scan.pages_crawled,
        "score": scan.score,
        "verdict": verdict(scan.score) if scan.score is not None else None,
        "layers": {"craft": scan.score_craft, "structure": scan.score_structure,
                   "search": scan.score_search, "answers": scan.score_answers},
        "findings": [
            {"check": f.check, "layer": f.layer, "severity": f.severity,
             "summary": f.summary, "why": f.why, "fix": f.fix,
             "evidence": f.evidence, "page": f.page_url}
            for f in scan.findings
        ],
    }
