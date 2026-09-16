"""App assembly. This process is an API: it serves JSON, never HTML.

    uvicorn app.main:app --reload

    /v1      the partner API -- fig_live_* key auth, versioned, stable
    /scan    the free public read -- no account; capped per browser, per
             network and per day
    /api     the workspace API the Next.js frontend reads -- mounted only when
             FIG_WORKSPACE_API=1, so the backend can run disconnected from it
    /health  liveness, plus what is and is not configured
    /docs    the OpenAPI schema

With nothing configured this runs on SQLite with ai_explain and billing off.
Point DATABASE_URL at Supabase and add the Anthropic and Stripe keys and the
same code runs for real.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.api import router as api_router
from app.billing import router as billing_router
from app.db import IS_SQLITE, get_session, init_db
from app.jobs import queue_depth, start_workers, stop_workers
from app.oauth import router as oauth_router
from app.public import router as public_router
from app.webapp import router as webapp_router

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("fig")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    start_workers()
    log.info("FIG API up - db %s, ai_explain %s, workspace API %s",
             "sqlite" if IS_SQLITE else "postgres",
             config.AI_MODEL if config.AI_EXPLAIN_ENABLED else "off",
             "on" if config.WORKSPACE_API_ENABLED else "off (disconnected from the frontend)")
    if config.DEV_NO_AUTH:
        log.warning("FIG_DEV_NO_AUTH=1 - the workspace API is open with no sign-in")
    if config.WORKSPACE_API_ENABLED:
        if not config.DEV_NO_AUTH and not config.AUTH_READY:
            log.error("sign-in is required but Supabase Auth is not configured "
                      "(set SUPABASE_URL and SUPABASE_ANON_KEY) - nobody can get in")
        if config.SESSION_EPHEMERAL:
            log.warning("FIG_SESSION_SECRET is unset - sessions are signed with a "
                        "per-process key, so a restart signs everyone out")
    yield
    stop_workers()


app = FastAPI(
    title="FIG",
    version="0.3.0",
    description=(
        "Reads a site for the patterns that make it read machine-made, whether its "
        "sections are in an order that makes sense, what a crawler can reach, and "
        "what a model has to quote. Findings are probabilistic and educational: this "
        "never claims a page 'is' AI-written."
    ),
    lifespan=lifespan,
)

# Browser origins are only needed by the frontend: the Next.js app and the
# marketing demo. With the workspace API off the backend is disconnected from
# both, so no browser origin is allowed at all. Server-to-server and curl
# callers never needed CORS in the first place. Origins stay explicit -- a
# wildcard is not permitted alongside credentials.
if config.WORKSPACE_API_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(set(config.SITE_ORIGINS) | set(config.CORS_ORIGINS)),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

# Installed even when disconnected: `require_account` reads request.session,
# and Starlette raises rather than returning nothing when the middleware is
# absent. The cookie is signed and HttpOnly, and holds only our own User id.
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    session_cookie="fig_session",
    max_age=config.SESSION_MAX_AGE,
    same_site="lax",
    https_only=config.PUBLIC_URL.startswith("https://"),
)

app.include_router(api_router)
app.include_router(billing_router)
app.include_router(public_router)
app.include_router(oauth_router)
if config.WORKSPACE_API_ENABLED:
    app.include_router(webapp_router)


@app.get("/", include_in_schema=False)
def root():
    """Point a bare hit at the docs rather than a dead page."""
    return {
        "service": "fig-api",
        "version": app.version,
        "docs": "/docs",
        "partner_api": "/v1",
        "public_read": "/scan",
        "workspace_api": "/api" if config.WORKSPACE_API_ENABLED else None,
    }


@app.get("/health")
def health(session: Session = Depends(get_session)):
    return {
        "status": "ok",
        "db": "sqlite" if IS_SQLITE else "postgres",
        "queue": queue_depth(session),
        "ai_explain": config.AI_EXPLAIN_ENABLED,
        "ai_model": config.AI_MODEL if config.AI_EXPLAIN_ENABLED else None,
        "billing": config.BILLING_ENABLED,
        "workspace_api": config.WORKSPACE_API_ENABLED,
        "dev_no_auth": config.DEV_NO_AUTH,
        "secrets_configured": bool(config.SECRET_ENCRYPTION_KEY),
        "google_oauth": config.GOOGLE_OAUTH_ENABLED,
    }
