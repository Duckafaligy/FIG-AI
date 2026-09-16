"""OAuth connections between FIG and a site's external platforms.

Mounted unconditionally in app/main.py (like billing_router) because a
platform's redirect URI has to be a stable address regardless of whether the
workspace API (`/api`) is enabled -- Google's servers don't know or care about
FIG_WORKSPACE_API. Session-cookie auth (`current_account`, the same resolver
`app/webapp.py` uses, FIG_DEV_NO_AUTH fallback included) decides who is
connecting.

Only Google (Analytics, read-only) is wired up. Every CMS platform in
CLAUDE.md's roadmap follows this same three-step shape once it has a
client id/secret, except WordPress, which uses Application Passwords instead
of OAuth and needs no /start or /callback at all:

    1. /start   -- build the platform's authorize URL, redirect the browser.
    2. /callback -- verify `state`, exchange `code` for a token server-side
       (never in browser JS), store it via app.secrets_store, upsert
       Integration, send the browser back to the frontend.

The access/refresh tokens this writes are for GA4 read access only --
nothing here can write to a site. A write-capable adapter (Shopify, WordPress,
...) follows the same pattern but its Integration row also needs `scopes`
set deliberately, per the "nothing is written without approval" rule in
app/publishing.py.
"""
from __future__ import annotations

import logging
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.auth import current_account
from app.db import get_session
from app.models import Integration, Site, _now
from app.secrets_store import SecretsNotConfigured, store_secret

log = logging.getLogger("fig.oauth")
router = APIRouter(prefix="/oauth", tags=["oauth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
PLATFORM = "google_analytics"

# How long a user has to complete the Google login screen before the state
# token is treated as expired rather than replayed.
STATE_MAX_AGE = 600


def _serializer() -> URLSafeTimedSerializer:
    # Reuses the session-signing secret rather than adding a second one to
    # configure -- this state token and the session cookie have the same
    # threat model (forged on this server's behalf) and the same lifetime
    # expectations (short-lived, process-local is fine).
    return URLSafeTimedSerializer(config.SESSION_SECRET, salt="fig-oauth-state")


def _return(**params: str) -> RedirectResponse:
    return RedirectResponse(f"{config.OAUTH_RETURN_URL}?{urlencode(params)}")


def _owned_site(session: Session, request: Request, site_id: str) -> Site:
    account = current_account(request, session)
    if account is None:
        raise HTTPException(401, "sign in required")
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site in this workspace")
    return site


@router.get("/google/start")
def google_start(request: Request, site_id: str = Query(...),
                  session: Session = Depends(get_session)):
    """Redirects the browser to Google's consent screen. The site has to
    belong to whoever is signed in -- this is what stops one user connecting
    analytics onto a site they don't own."""
    if not config.GOOGLE_OAUTH_ENABLED:
        raise HTTPException(503, "Google OAuth is not configured on this server "
                                 "(set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)")
    site = _owned_site(session, request, site_id)

    state = _serializer().dumps({"site_id": site.id, "account_id": site.account_id})
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",  # ask for a refresh token, not just a session-length one
        "prompt": "consent",       # otherwise a returning user gets no refresh token at all
        "include_granted_scopes": "true",
        "state": state,
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
def google_callback(request: Request, code: str = Query(default=""),
                    state: str = Query(default=""), error: str = Query(default=""),
                    session: Session = Depends(get_session)):
    """Google lands the browser here after the consent screen. Runs
    server-side only -- the authorization code and the resulting token never
    reach frontend JS."""
    if error:
        return _return(integration=PLATFORM, error=error)

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(integration=PLATFORM, error="expired_state")
    except BadSignature:
        return _return(integration=PLATFORM, error="invalid_state")

    site = session.get(Site, payload.get("site_id"))
    if site is None or site.account_id != payload.get("account_id"):
        return _return(integration=PLATFORM, error="site_not_found")

    try:
        resp = httpx.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("google token exchange request failed: %s", exc)
        return _return(integration=PLATFORM, error="token_request_failed")

    if resp.status_code != 200:
        log.warning("google token exchange rejected: %s %s", resp.status_code, resp.text[:300])
        return _return(integration=PLATFORM, error="token_exchange_failed")

    tokens = resp.json()
    if not tokens.get("refresh_token"):
        # Happens when a user who already granted consent goes through this
        # again without `prompt=consent` actually forcing a new grant screen
        # -- Google only hands back a refresh token on the first consent.
        log.warning("google token exchange for site %s returned no refresh_token", site.id)

    try:
        ref = store_secret(session, {
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_at": time.time() + tokens.get("expires_in", 0),
            "scope": tokens.get("scope", GOOGLE_SCOPE),
        })
    except SecretsNotConfigured as exc:
        log.error("cannot store google tokens for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM, error="secrets_not_configured")

    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM)).first()
    if integ is None:
        integ = Integration(site_id=site.id, platform=PLATFORM)
        session.add(integ)
    integ.credential_ref = ref
    integ.credential_hint = "connected"
    integ.scopes = ["analytics_read"]
    integ.connected_at = _now()
    integ.last_error = None
    session.commit()

    return _return(integration=PLATFORM, connected="1")
