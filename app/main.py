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
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.api import hostname_of, router as api_router
from app.auth import require_account
from app.billing import router as billing_router
from app.dashboard import NeedsSignIn
from app.frontend import router as frontend_router
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
    elif not config.AUTH_READY:
        log.error("sign-in is required but Supabase Auth is not configured "
                  "(set SUPABASE_URL and SUPABASE_ANON_KEY) - nobody can get in")
    if config.SESSION_EPHEMERAL:
        log.warning("FIG_SESSION_SECRET is unset - sessions are signed with a "
                    "per-process key, so a restart signs everyone out")
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

# The demo runs on the marketing site's origin and calls this API from there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.SITE_ORIGINS,
    allow_credentials=False,          # the public read needs no cookie
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Signed, HttpOnly cookie. The Supabase access token is never put in it --
# only our own User id, resolved server-side on each request.
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    session_cookie="fig_session",
    max_age=config.SESSION_MAX_AGE,
    same_site="lax",
    https_only=config.PUBLIC_URL.startswith("https://"),
)


@app.exception_handler(NeedsSignIn)
async def _needs_sign_in(request, _exc):
    """A signed-out browser gets the login page, not a 401 rendered as text."""
    return RedirectResponse("/login", status_code=303)


app.mount("/static", StaticFiles(directory=str(config.ROOT / "static")), name="static")
app.include_router(api_router)
app.include_router(billing_router)

# The page routes. `frontend.py` replaced the page half of dashboard.py and
# public.py when the frontend was rebuilt to the new designs; those two modules
# are still in the tree for their POST handlers and the public free-read logic,
# but their templates were archived, so they are not mounted. The /v1 API and
# billing above are unaffected.
app.include_router(frontend_router)


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
