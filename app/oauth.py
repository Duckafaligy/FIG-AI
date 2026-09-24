"""OAuth connections between FIG and a site's external platforms.

Mounted unconditionally in app/main.py (like billing_router) because a
platform's redirect URI has to be a stable address regardless of whether the
workspace API (`/api`) is enabled -- Google's servers don't know or care about
FIG_WORKSPACE_API. Session-cookie auth (`current_account`, the same resolver
`app/webapp.py` uses, FIG_DEV_NO_AUTH fallback included) decides who is
connecting.

One consent screen now covers two Google platforms: Analytics (read-only)
and Search Console (read-only) share the same OAuth client -- GOOGLE_SCOPE
requests both scopes together, and google_callback connects whichever the
user's account actually grants, as two independent Integration rows (each
can be reconnected or fail separately later; see app/ga.py and
app/search_console.py). Unlike every platform below, Google is
account-scoped, not site-scoped (2026-09-23): one connection per workspace,
not one per project -- see Integration's docstring in app/models.py.
Shopify and Webflow follow this same three-step shape once they have a
client id/secret, except WordPress, which uses Application Passwords
instead of OAuth and needs no /start or /callback at all:

    1. /start   -- build the platform's authorize URL, redirect the browser.
    2. /callback -- verify `state`, exchange `code` for a token server-side
       (never in browser JS), store it via app.secrets_store, upsert
       Integration, send the browser back to the frontend.

Wix does not: new Wix apps can't use a code-exchange flow at all (see the
"wix" section below for the real one -- an install-approval redirect with
no code, and no server-side token exchange because Wix mints tokens on
demand from client credentials).

The access/refresh tokens this writes are read-only for both Google
platforms -- nothing here can write to a site. A write-capable adapter
(Shopify, WordPress, ...) follows the same pattern but its Integration row
also needs `scopes` set deliberately, per the "nothing is written without
approval" rule in app/publishing.py.
"""
from __future__ import annotations

import logging
import time
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
import base64
import hashlib
import hmac as hmac_module
import json
import re

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.auth import current_account
from app.db import get_session
from app.models import Account, Integration, Site, _now
from app.secrets_store import SecretsNotConfigured, delete_secret, store_secret

log = logging.getLogger("fig.oauth")
router = APIRouter(prefix="/oauth", tags=["oauth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
# One consent screen, both scopes: Search Console reuses this same OAuth
# client rather than needing its own registration (see CLAUDE.md) -- Google
# accepts a space-separated scope list and grants whichever of these the
# account has access to. A refusal on one property doesn't block the other.
GOOGLE_SCOPE = ("https://www.googleapis.com/auth/analytics.readonly "
                "https://www.googleapis.com/auth/webmasters.readonly")
PLATFORM = "google_analytics"
PLATFORM_GSC = "google_search_console"

# How long a user has to complete the Google login screen before the state
# token is treated as expired rather than replayed.
STATE_MAX_AGE = 600


def _serializer() -> URLSafeTimedSerializer:
    # Reuses the session-signing secret rather than adding a second one to
    # configure -- this state token and the session cookie have the same
    # threat model (forged on this server's behalf) and the same lifetime
    # expectations (short-lived, process-local is fine).
    return URLSafeTimedSerializer(config.SESSION_SECRET, salt="fig-oauth-state")


def _return(base: str | None = None, **params: str) -> RedirectResponse:
    return RedirectResponse(f"{base or config.OAUTH_RETURN_URL}?{urlencode(params)}")


def _site_return_url(site_id: str) -> str:
    """Where a site-scoped platform's callback sends the browser once it
    knows which project it connected -- that project's own Settings/
    connectors page (/projects/{id}/settings, 2026-09-23's URL structure)."""
    return f"{config.FRONTEND_URL}/projects/{site_id}/settings"


# Google is the one platform whose Connect button lives on account-wide
# Settings, not a project's own -- every other platform's callback lands
# back on that project's own /projects/{site_id}/settings (_site_return_url
# above), but Google has no per-project page to return to at all. Redirect
# there instead of the shared default.
GOOGLE_RETURN_URL = f"{config.FRONTEND_URL}/projects/settings"


def _owned_site(session: Session, request: Request, site_id: str) -> Site:
    account = current_account(request, session)
    if account is None:
        raise HTTPException(401, "sign in required")
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site in this workspace")
    return site


@router.get("/google/start")
def google_start(request: Request, session: Session = Depends(get_session)):
    """Redirects the browser to Google's consent screen. Account-scoped, not
    site-scoped (2026-09-23): one Google connection per workspace, not one
    per project -- Google's own OAuth grant is already per-account, and an
    agency managing several client sites from one Google login only ever
    needed to go through consent once. See Integration's docstring in
    app/models.py for the trade-off this accepts.

    One consent screen covers both Google platforms: GOOGLE_SCOPE requests
    Analytics and Search Console together, and google_callback below
    connects whichever of the two Google actually granted."""
    if not config.GOOGLE_OAUTH_ENABLED:
        raise HTTPException(503, "Google OAuth is not configured on this server "
                                 "(set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)")
    account = current_account(request, session)
    if account is None:
        raise HTTPException(401, "sign in required")

    state = _serializer().dumps({"account_id": account.id})
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
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error=error)

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="expired_state")
    except BadSignature:
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="invalid_state")

    account = session.get(Account, payload.get("account_id"))
    if account is None:
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="account_not_found")

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
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="token_request_failed")

    if resp.status_code != 200:
        log.warning("google token exchange rejected: %s %s", resp.status_code, resp.text[:300])
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="token_exchange_failed")

    tokens = resp.json()
    if not tokens.get("refresh_token"):
        # Happens when a user who already granted consent goes through this
        # again without `prompt=consent` actually forcing a new grant screen
        # -- Google only hands back a refresh token on the first consent.
        log.warning("google token exchange for account %s returned no refresh_token", account.id)

    granted = tokens.get("scope", "")
    # A dict per platform actually granted -- a token dict per Integration,
    # duplicated rather than shared, so each can refresh independently later
    # without one platform's refresh racing the other's stored copy.
    to_connect: list[tuple[str, str]] = []
    if "analytics.readonly" in granted:
        to_connect.append((PLATFORM, "analytics_read"))
    if "webmasters.readonly" in granted:
        to_connect.append((PLATFORM_GSC, "search_console_read"))
    if not to_connect:
        # Google always echoes back what it actually granted; an empty
        # match here means the consent screen showed neither scope, most
        # often because the underlying API isn't enabled for the project.
        log.warning("google token exchange for account %s granted no scope FIG asked for: %r",
                   account.id, granted)
        return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="no_scope_granted")

    connected_platforms = []
    for platform, scope_label in to_connect:
        try:
            ref = store_secret(session, {
                "access_token": tokens.get("access_token", ""),
                "refresh_token": tokens.get("refresh_token", ""),
                "expires_at": time.time() + tokens.get("expires_in", 0),
                "scope": granted,
            })
        except SecretsNotConfigured as exc:
            log.error("cannot store google tokens for account %s: %s", account.id, exc)
            return _return(GOOGLE_RETURN_URL, integration=PLATFORM, error="secrets_not_configured")

        integ = session.scalars(select(Integration).where(
            Integration.account_id == account.id, Integration.platform == platform)).first()
        if integ is None:
            integ = Integration(account_id=account.id, platform=platform)
            session.add(integ)
        # Reconnecting stores a fresh token; the one it replaces would be left
        # orphaned in the secrets table, so remove it.
        if integ.credential_ref and integ.credential_ref != ref:
            delete_secret(session, integ.credential_ref)
        integ.credential_ref = ref
        integ.credential_hint = "connected"
        integ.scopes = [scope_label]
        integ.connected_at = _now()
        integ.last_error = None
        connected_platforms.append(platform)

    session.commit()
    return _return(GOOGLE_RETURN_URL, integration=",".join(connected_platforms), connected="1")


# --- shopify --------------------------------------------------------------
# Real, unlike the rest of this module's write-capable claims: only the
# CONNECT step exists here. The write adapter itself does not -- there is no
# real Shopify store to verify field names, API version or response shapes
# against, the same bar `app/wordpress.py` had to clear before it could claim
# anything (see that module and CLAUDE.md). `app/publishing.py:publish()`
# already refuses out loud for every platform except WordPress, so a
# connected Shopify integration is honest on its own: "Connected", and
# nothing pretends to publish through it yet.

SHOPIFY_TOKEN_SCOPE = "read_content,write_content"
PLATFORM_SHOPIFY = "shopify"

# {store}.myshopify.com only -- Shopify's own recommended validation before
# ever building a URL from a caller-supplied shop, on both /start (a typed
# or copy-pasted value) and /callback (echoed back by Shopify, but checked
# again rather than trusted, since it reaches this handler as a plain query
# param like anything else).
SHOPIFY_SHOP_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com$")


def _valid_shop(shop: str) -> str | None:
    shop = (shop or "").strip().lower()
    return shop if SHOPIFY_SHOP_RE.match(shop) else None


@router.get("/shopify/start")
def shopify_start(request: Request, site_id: str = Query(...), shop: str = Query(...),
                  session: Session = Depends(get_session)):
    """Redirects to the merchant's own store, not a fixed URL -- Shopify's
    OAuth authorize endpoint lives on https://{shop}.myshopify.com, so the
    caller has to say which store, unlike Google's one authorize URL for
    everyone."""
    if not config.SHOPIFY_OAUTH_ENABLED:
        raise HTTPException(503, "Shopify OAuth is not configured on this server "
                                 "(set SHOPIFY_CLIENT_ID / SHOPIFY_CLIENT_SECRET)")
    shop_domain = _valid_shop(shop)
    if shop_domain is None:
        raise HTTPException(422, "shop must look like your-store.myshopify.com")
    site = _owned_site(session, request, site_id)

    state = _serializer().dumps({"site_id": site.id, "account_id": site.account_id,
                                 "shop": shop_domain})
    params = {
        "client_id": config.SHOPIFY_CLIENT_ID,
        "scope": SHOPIFY_TOKEN_SCOPE,
        "redirect_uri": config.SHOPIFY_OAUTH_REDIRECT_URI,
        "state": state,
    }
    return RedirectResponse(f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}")


@router.get("/shopify/callback")
def shopify_callback(request: Request, code: str = Query(default=""),
                     shop: str = Query(default=""), hmac: str = Query(default=""),
                     state: str = Query(default=""), error: str = Query(default=""),
                     session: Session = Depends(get_session)):
    """Shopify lands the browser here after the merchant approves the app.

    Two checks Google's callback doesn't need, both required by Shopify's
    own security guidance for apps using this (non-embedded) OAuth flow:
    the shop param is re-validated (never trust a query param just because
    it looks like the one /start sent), and the whole query string's HMAC is
    verified against the app's client secret, proving the redirect really
    came from Shopify and was not forged by pointing a browser at this URL
    directly with a guessed or stolen `code`.
    """
    if error:
        return _return(integration=PLATFORM_SHOPIFY, error=error)

    shop_domain = _valid_shop(shop)
    if shop_domain is None:
        return _return(integration=PLATFORM_SHOPIFY, error="invalid_shop")

    # Shopify's documented scheme: every query param except hmac/signature,
    # sorted, joined as k=v with &, HMAC-SHA256'd with the client secret.
    # Constant-time compare -- this is exactly the kind of check a timing
    # side-channel could otherwise weaken.
    to_verify = {k: v for k, v in request.query_params.items()
                if k not in ("hmac", "signature")}
    message = "&".join(f"{k}={v}" for k, v in sorted(to_verify.items()))
    expected = hmac_module.new(config.SHOPIFY_CLIENT_SECRET.encode(),
                               message.encode(), hashlib.sha256).hexdigest()
    if not hmac or not hmac_module.compare_digest(expected, hmac):
        log.warning("shopify callback HMAC did not verify for shop %s", shop_domain)
        return _return(integration=PLATFORM_SHOPIFY, error="invalid_hmac")

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(integration=PLATFORM_SHOPIFY, error="expired_state")
    except BadSignature:
        return _return(integration=PLATFORM_SHOPIFY, error="invalid_state")

    if payload.get("shop") != shop_domain:
        # The store that approved the app isn't the one /start was sent for.
        return _return(integration=PLATFORM_SHOPIFY, error="shop_mismatch")

    site = session.get(Site, payload.get("site_id"))
    if site is None or site.account_id != payload.get("account_id"):
        return _return(integration=PLATFORM_SHOPIFY, error="site_not_found")

    try:
        resp = httpx.post(f"https://{shop_domain}/admin/oauth/access_token", data={
            "client_id": config.SHOPIFY_CLIENT_ID,
            "client_secret": config.SHOPIFY_CLIENT_SECRET,
            "code": code,
        }, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("shopify token exchange request failed: %s", exc)
        return _return(integration=PLATFORM_SHOPIFY, error="token_request_failed")

    if resp.status_code != 200:
        log.warning("shopify token exchange rejected: %s %s", resp.status_code, resp.text[:300])
        return _return(integration=PLATFORM_SHOPIFY, error="token_exchange_failed")

    tokens = resp.json()
    access_token = tokens.get("access_token", "")
    if not access_token:
        return _return(integration=PLATFORM_SHOPIFY, error="no_access_token")

    try:
        # Offline access tokens (the default here -- no "online" access
        # requested) don't expire the way Google's do, so there is no
        # refresh_token or expires_at to carry alongside it.
        ref = store_secret(session, {"access_token": access_token,
                                     "shop": shop_domain,
                                     "scope": tokens.get("scope", "")})
    except SecretsNotConfigured as exc:
        log.error("cannot store shopify token for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM_SHOPIFY, error="secrets_not_configured")

    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM_SHOPIFY)).first()
    if integ is None:
        integ = Integration(site_id=site.id, platform=PLATFORM_SHOPIFY)
        session.add(integ)
    if integ.credential_ref and integ.credential_ref != ref:
        delete_secret(session, integ.credential_ref)
    integ.endpoint = shop_domain
    integ.credential_ref = ref
    integ.credential_hint = shop_domain
    integ.scopes = tokens.get("scope", "").split(",")
    integ.connected_at = _now()
    integ.last_error = None
    session.commit()
    return _return(_site_return_url(integ.site_id), integration=PLATFORM_SHOPIFY, connected="1")


# --- webflow ----------------------------------------------------------------
# Same limitation as Shopify: the CONNECT step is real, the write adapter is
# not. No live Webflow site to verify CMS collection field names or API
# behavior against yet -- app/publishing.py:publish() already refuses out
# loud for any platform but WordPress, so this is honest on its own.
#
# Shaped like Google, not Shopify: one fixed authorize URL (the person picks
# which of their own Webflow sites to authorize on Webflow's own consent
# screen -- /start doesn't need to know that in advance), offline-style
# tokens with no refresh dance, and state is the only CSRF check needed
# (no extra callback signature the way Shopify's HMAC is).

WEBFLOW_AUTH_URL = "https://webflow.com/oauth/authorize"
WEBFLOW_TOKEN_URL = "https://api.webflow.com/oauth/access_token"
WEBFLOW_SITES_URL = "https://api.webflow.com/v2/sites"
# CMS (Webflow's blog/collection items) and Pages -- the closest match to
# what the WordPress adapter actually does (post/page content). Verify
# against the live app registration screen before relying on these exact
# names; Webflow's Data API scope names have shifted before.
WEBFLOW_SCOPE = "cms:read cms:write pages:read pages:write sites:read"
PLATFORM_WEBFLOW = "webflow"


@router.get("/webflow/start")
def webflow_start(request: Request, site_id: str = Query(...),
                  session: Session = Depends(get_session)):
    if not config.WEBFLOW_OAUTH_ENABLED:
        raise HTTPException(503, "Webflow OAuth is not configured on this server "
                                 "(set WEBFLOW_CLIENT_ID / WEBFLOW_CLIENT_SECRET)")
    site = _owned_site(session, request, site_id)

    state = _serializer().dumps({"site_id": site.id, "account_id": site.account_id})
    params = {
        "response_type": "code",
        "client_id": config.WEBFLOW_CLIENT_ID,
        "redirect_uri": config.WEBFLOW_OAUTH_REDIRECT_URI,
        "scope": WEBFLOW_SCOPE,
        "state": state,
    }
    return RedirectResponse(f"{WEBFLOW_AUTH_URL}?{urlencode(params)}")


@router.get("/webflow/callback")
def webflow_callback(request: Request, code: str = Query(default=""),
                     state: str = Query(default=""), error: str = Query(default=""),
                     session: Session = Depends(get_session)):
    if error:
        return _return(integration=PLATFORM_WEBFLOW, error=error)

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(integration=PLATFORM_WEBFLOW, error="expired_state")
    except BadSignature:
        return _return(integration=PLATFORM_WEBFLOW, error="invalid_state")

    site = session.get(Site, payload.get("site_id"))
    if site is None or site.account_id != payload.get("account_id"):
        return _return(integration=PLATFORM_WEBFLOW, error="site_not_found")

    try:
        resp = httpx.post(WEBFLOW_TOKEN_URL, data={
            "client_id": config.WEBFLOW_CLIENT_ID,
            "client_secret": config.WEBFLOW_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("webflow token exchange request failed: %s", exc)
        return _return(integration=PLATFORM_WEBFLOW, error="token_request_failed")

    if resp.status_code != 200:
        log.warning("webflow token exchange rejected: %s %s", resp.status_code, resp.text[:300])
        return _return(integration=PLATFORM_WEBFLOW, error="token_exchange_failed")

    tokens = resp.json()
    access_token = tokens.get("access_token", "")
    if not access_token:
        return _return(integration=PLATFORM_WEBFLOW, error="no_access_token")

    # Webflow's consent screen is where the site gets picked, not /start --
    # the token itself doesn't say which site(s) it can reach, so a write
    # adapter needs this to know what to call GET/PATCH against. No picker
    # yet if more than one was granted: first one wins, same limitation
    # app/ga.py and app/search_console.py already document for Google.
    try:
        sites_resp = httpx.get(WEBFLOW_SITES_URL,
                               headers={"Authorization": f"Bearer {access_token}"}, timeout=15.0)
        webflow_site_id = (sites_resp.json().get("sites") or [{}])[0].get("id", "") \
            if sites_resp.status_code == 200 else ""
    except httpx.HTTPError as exc:
        log.warning("webflow site discovery failed for site %s: %s", site.id, exc)
        webflow_site_id = ""

    try:
        ref = store_secret(session, {"access_token": access_token,
                                     "scope": tokens.get("scope", WEBFLOW_SCOPE)})
    except SecretsNotConfigured as exc:
        log.error("cannot store webflow token for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM_WEBFLOW, error="secrets_not_configured")

    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM_WEBFLOW)).first()
    if integ is None:
        integ = Integration(site_id=site.id, platform=PLATFORM_WEBFLOW)
        session.add(integ)
    if integ.credential_ref and integ.credential_ref != ref:
        delete_secret(session, integ.credential_ref)
    integ.credential_ref = ref
    integ.credential_hint = "connected"
    integ.endpoint = webflow_site_id or None
    integ.scopes = tokens.get("scope", WEBFLOW_SCOPE).split(" ")
    integ.connected_at = _now()
    integ.last_error = None
    session.commit()
    return _return(_site_return_url(integ.site_id), integration=PLATFORM_WEBFLOW, connected="1")


# --- wix ----------------------------------------------------------------
# A genuinely different shape from the three above, not just a variant: new
# Wix apps can no longer use a redirect-with-authorization-code flow at all
# ("custom authentication" was retired for new apps -- see
# dev.wix.com/docs/api-reference/app-management/oauth-2/introduction). The
# current model is Wix's "external install flow": FIG sends the browser to a
# fixed installer URL, the site owner approves the install on Wix's own
# screen, and Wix redirects back with `instanceId` + `signedInstance` rather
# than a `code` -- there is nothing to exchange server-side, because Wix's
# client-credentials model mints access tokens on demand from
# client_id/client_secret/instance_id whenever one is actually needed (see
# app/config.py). `state` still carries site_id/account_id exactly like the
# other three, appended to postInstallationUrl and echoed back unchanged --
# Wix's own docs recommend exactly this pattern.
#
# `signedInstance` is the only thing standing between "Wix said this
# instanceId" and "a query string claims this instanceId" -- the raw
# `instanceId` query param is explicitly documented as untrusted on its own.
# Verified locally (HMAC-SHA256 over the still-base64url-encoded data string,
# using the app secret, constant-time compared) per Wix's documented
# algorithm, same shape as Shopify's callback HMAC check above.

WIX_INSTALLER_URL = "https://www.wix.com/app-installer"
PLATFORM_WIX = "wix"


def _wix_verify_signed_instance(signed_instance: str, secret: str) -> dict:
    """Raises ValueError if the signature doesn't verify. Returns the decoded
    payload (has `instanceId`, `siteOwnerId`, ...) on success."""
    try:
        signature_b64, data_b64 = signed_instance.split(".", 1)
    except ValueError:
        raise ValueError("malformed signedInstance")

    def _b64url_decode(s: str) -> bytes:
        return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

    expected = hmac_module.new(secret.encode(), data_b64.encode(), hashlib.sha256).digest()
    given = _b64url_decode(signature_b64)
    if not hmac_module.compare_digest(expected, given):
        raise ValueError("signedInstance did not verify")
    return json.loads(_b64url_decode(data_b64))


@router.get("/wix/start")
def wix_start(request: Request, site_id: str = Query(...),
             session: Session = Depends(get_session)):
    """Redirects to Wix's fixed app-installer URL. There's no per-merchant
    domain to pick (unlike Shopify) and no consent-screen redirect_uri to
    register in advance (unlike Google/Webflow) -- `postInstallationUrl` is
    just passed as a query param, with FIG's signed `state` riding along on
    it so /callback can tell which site this install was for."""
    if not config.WIX_OAUTH_ENABLED:
        raise HTTPException(503, "Wix is not configured on this server "
                                 "(set WIX_CLIENT_ID / WIX_CLIENT_SECRET / WIX_SHARE_URL_ID)")
    site = _owned_site(session, request, site_id)

    state = _serializer().dumps({"site_id": site.id, "account_id": site.account_id})
    callback_url = f"{config.WIX_OAUTH_REDIRECT_URI}?state={state}"
    params = {
        "appId": config.WIX_CLIENT_ID,
        "shareUrlId": config.WIX_SHARE_URL_ID,
        "postInstallationUrl": quote(callback_url, safe=""),
    }
    # Not urlencode() -- postInstallationUrl is already percent-encoded above
    # and urlencode() would double-encode it.
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{WIX_INSTALLER_URL}?{query}")


@router.get("/wix/callback")
def wix_callback(request: Request, instanceId: str = Query(default=""),
                 signedInstance: str = Query(default=""),
                 state: str = Query(default=""),
                 session: Session = Depends(get_session)):
    """Wix's postInstallationUrl. Missing instanceId/signedInstance means the
    install failed or was cancelled -- Wix's own docs describe this as the
    signal, there's no separate `error` param the way the other three have."""
    if not instanceId or not signedInstance:
        return _return(integration=PLATFORM_WIX, error="install_failed")

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(integration=PLATFORM_WIX, error="expired_state")
    except BadSignature:
        return _return(integration=PLATFORM_WIX, error="invalid_state")

    site = session.get(Site, payload.get("site_id"))
    if site is None or site.account_id != payload.get("account_id"):
        return _return(integration=PLATFORM_WIX, error="site_not_found")

    try:
        instance_data = _wix_verify_signed_instance(signedInstance, config.WIX_CLIENT_SECRET)
    except ValueError as exc:
        log.warning("wix signedInstance did not verify for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM_WIX, error="invalid_signed_instance")

    # The verified payload's instanceId is the trusted one -- the raw query
    # param is not (see module docstring above).
    verified_instance_id = instance_data.get("instanceId", "")
    if not verified_instance_id:
        return _return(integration=PLATFORM_WIX, error="no_instance_id")

    try:
        ref = store_secret(session, {"instance_id": verified_instance_id})
    except SecretsNotConfigured as exc:
        log.error("cannot store wix instance id for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM_WIX, error="secrets_not_configured")

    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM_WIX)).first()
    if integ is None:
        integ = Integration(site_id=site.id, platform=PLATFORM_WIX)
        session.add(integ)
    if integ.credential_ref and integ.credential_ref != ref:
        delete_secret(session, integ.credential_ref)
    integ.credential_ref = ref
    integ.credential_hint = "connected"
    integ.connected_at = _now()
    integ.last_error = None
    session.commit()
    return _return(_site_return_url(integ.site_id), integration=PLATFORM_WIX, connected="1")


# --- github ----------------------------------------------------------------
# For a self-hosted / Git-deployed site with no CMS API at all -- see
# app/config.py's GITHUB_* block for why this is a classic OAuth App, not a
# GitHub App, and app/github_repo.py for the write adapter this connects to.
# Otherwise the standard three-step shape, plus one thing Shopify's /start
# also needs that Google/Webflow's doesn't: a caller-supplied value the
# OAuth grant itself doesn't carry -- there it's `shop`, here it's `repo`
# (owner/name), carried in `state` and stored on Integration.endpoint at
# callback, the same place Shopify stores its shop domain.

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_SCOPE = "repo"
PLATFORM_GITHUB = "github"

GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _valid_repo(repo: str) -> str | None:
    repo = (repo or "").strip()
    return repo if GITHUB_REPO_RE.match(repo) else None


@router.get("/github/start")
def github_start(request: Request, site_id: str = Query(...), repo: str = Query(...),
                 session: Session = Depends(get_session)):
    if not config.GITHUB_OAUTH_ENABLED:
        raise HTTPException(503, "GitHub OAuth is not configured on this server "
                                 "(set GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET)")
    repo_name = _valid_repo(repo)
    if repo_name is None:
        raise HTTPException(422, "repo must look like owner/name")
    site = _owned_site(session, request, site_id)

    state = _serializer().dumps({"site_id": site.id, "account_id": site.account_id,
                                 "repo": repo_name})
    params = {
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": config.GITHUB_OAUTH_REDIRECT_URI,
        "scope": GITHUB_SCOPE,
        "state": state,
    }
    return RedirectResponse(f"{GITHUB_AUTH_URL}?{urlencode(params)}")


@router.get("/github/callback")
def github_callback(request: Request, code: str = Query(default=""),
                    state: str = Query(default=""), error: str = Query(default=""),
                    session: Session = Depends(get_session)):
    if error:
        return _return(integration=PLATFORM_GITHUB, error=error)

    try:
        payload = _serializer().loads(state, max_age=STATE_MAX_AGE)
    except SignatureExpired:
        return _return(integration=PLATFORM_GITHUB, error="expired_state")
    except BadSignature:
        return _return(integration=PLATFORM_GITHUB, error="invalid_state")

    site = session.get(Site, payload.get("site_id"))
    if site is None or site.account_id != payload.get("account_id"):
        return _return(integration=PLATFORM_GITHUB, error="site_not_found")
    repo_name = payload.get("repo", "")

    try:
        # GitHub's token endpoint defaults to form-urlencoded; without this
        # header it returns access_token=...&scope=...&token_type=bearer,
        # which .json() below would choke on.
        resp = httpx.post(GITHUB_TOKEN_URL, headers={"Accept": "application/json"}, data={
            "client_id": config.GITHUB_CLIENT_ID,
            "client_secret": config.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": config.GITHUB_OAUTH_REDIRECT_URI,
        }, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("github token exchange request failed: %s", exc)
        return _return(integration=PLATFORM_GITHUB, error="token_request_failed")

    if resp.status_code != 200:
        log.warning("github token exchange rejected: %s %s", resp.status_code, resp.text[:300])
        return _return(integration=PLATFORM_GITHUB, error="token_exchange_failed")

    tokens = resp.json()
    if tokens.get("error"):
        # GitHub answers a bad/expired code with HTTP 200 and an error body,
        # not a non-200 status -- checked separately from the request itself.
        log.warning("github token exchange returned an error body: %s", tokens.get("error"))
        return _return(integration=PLATFORM_GITHUB, error="token_exchange_failed")
    access_token = tokens.get("access_token", "")
    if not access_token:
        return _return(integration=PLATFORM_GITHUB, error="no_access_token")

    try:
        ref = store_secret(session, {"access_token": access_token,
                                     "scope": tokens.get("scope", GITHUB_SCOPE)})
    except SecretsNotConfigured as exc:
        log.error("cannot store github token for site %s: %s", site.id, exc)
        return _return(integration=PLATFORM_GITHUB, error="secrets_not_configured")

    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM_GITHUB)).first()
    if integ is None:
        integ = Integration(site_id=site.id, platform=PLATFORM_GITHUB)
        session.add(integ)
    if integ.credential_ref and integ.credential_ref != ref:
        delete_secret(session, integ.credential_ref)
    integ.endpoint = repo_name
    integ.credential_ref = ref
    integ.credential_hint = repo_name
    integ.scopes = tokens.get("scope", GITHUB_SCOPE).split(",")
    integ.connected_at = _now()
    integ.last_error = None
    session.commit()
    return _return(_site_return_url(integ.site_id), integration=PLATFORM_GITHUB, connected="1")
