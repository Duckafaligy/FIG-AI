"""Google Search Console client — the other half of the Google OAuth grant
app/oauth.py now requests alongside Analytics. Same shape as app/ga.py on
purpose: read the stored token, refresh it if expired, discover which
verified property matches this site, pull real numbers. No connected
integration means None, same as everywhere else in this codebase — nothing
here estimates a number to make a panel look alive.

This is the piece that finally gives the trend-chart wiring
(components/dashboard-shell.tsx:LiveTrendChart, wired 2026-09-17) something
real to draw for an actual signed-up user: Search Analytics' `date`
dimension is a genuine daily time series, unlike GA's current-vs-prior-30-
day snapshot. Until now every trend chart's `fill`-gated series in
app/pages.py was demo-account-only for exactly this reason.
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.models import Integration, Site
from app.secrets_store import SecretsNotConfigured, read_secret, update_secret

log = logging.getLogger("fig.search_console")

TOKEN_URL = "https://oauth2.googleapis.com/token"
SITES_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites"
QUERY_URL_TMPL = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics:query"
PLATFORM = "google_search_console"


def _integration(session: Session, site: Site) -> Integration | None:
    integ = session.scalars(select(Integration).where(
        Integration.site_id == site.id, Integration.platform == PLATFORM)).first()
    return integ if integ and integ.is_connected() else None


def is_connected(session: Session, site: Site) -> bool:
    return _integration(session, site) is not None


def _access_token(session: Session, integ: Integration) -> str | None:
    try:
        creds = read_secret(session, integ.credential_ref)
    except (SecretsNotConfigured, KeyError) as exc:
        log.warning("gsc: cannot read stored token for site %s: %s", integ.site_id, exc)
        return None

    if creds.get("expires_at", 0) > time.time() + 60:
        return creds.get("access_token")

    refresh_token = creds.get("refresh_token")
    if not refresh_token:
        integ.last_error = "Search Console needs to be reconnected (no refresh token)"
        session.commit()
        return None

    try:
        resp = httpx.post(TOKEN_URL, data={
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("gsc: token refresh request failed for site %s: %s", integ.site_id, exc)
        return None
    if resp.status_code != 200:
        log.warning("gsc: token refresh rejected for site %s: %s %s",
                    integ.site_id, resp.status_code, resp.text[:200])
        integ.last_error = f"Search Console token refresh failed: HTTP {resp.status_code}"
        session.commit()
        return None

    tokens = resp.json()
    creds["access_token"] = tokens.get("access_token", creds.get("access_token"))
    creds["expires_at"] = time.time() + tokens.get("expires_in", 0)
    update_secret(session, integ.credential_ref, creds)
    session.commit()
    return creds["access_token"]


def _pick_site_url(urls: list[str], hostname: str) -> str | None:
    """Which of the account's verified Search Console properties is this FIG
    site? Pure and DB-free so it's directly testable. Tries an exact host
    match first (domain property, then https/http URL-prefix properties,
    with and without www); falls back to the first verified property the
    account can see, since there's no picker UI yet."""
    if not urls:
        return None
    host = hostname.lower().removeprefix("www.")
    candidates = {
        f"sc-domain:{host}",
        f"https://{host}/", f"https://www.{host}/",
        f"http://{host}/", f"http://www.{host}/",
    }
    return next((u for u in urls if u in candidates), None) or urls[0]


def _matching_site_url(token: str, integ: Integration, session: Session, hostname: str) -> str | None:
    """Cached on Integration.endpoint once found, same pattern app/ga.py
    uses for a GA4 property."""
    if integ.endpoint:
        return integ.endpoint
    try:
        resp = httpx.get(SITES_URL, headers={"Authorization": f"Bearer {token}"}, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("gsc: site discovery failed for site %s: %s", integ.site_id, exc)
        return None
    if resp.status_code != 200:
        log.warning("gsc: site discovery rejected for site %s: %s %s",
                    integ.site_id, resp.status_code, resp.text[:200])
        return None
    entries = resp.json().get("siteEntry", [])
    urls = [e["siteUrl"] for e in entries if e.get("siteUrl")]
    match = _pick_site_url(urls, hostname)
    if match is None:
        integ.last_error = "No Search Console property visible to this Google account"
        session.commit()
        return None
    integ.endpoint = match
    session.commit()
    return match


def _query(token: str, site_url: str, body: dict) -> dict | None:
    try:
        resp = httpx.post(QUERY_URL_TMPL.format(site=quote(site_url, safe="")),
                          headers={"Authorization": f"Bearer {token}"}, json=body, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("gsc: query failed for %s: %s", site_url, exc)
        return None
    if resp.status_code != 200:
        log.warning("gsc: query rejected for %s: %s %s", site_url, resp.status_code, resp.text[:300])
        return None
    return resp.json()


def _shape_daily(rows: list[dict]) -> list[dict]:
    """Pure: raw searchAnalytics rows (dimensions=["date"]) into a
    date-sorted list. Direct-testable, no network."""
    return sorted(
        [{"date": r["keys"][0], "clicks": int(r.get("clicks", 0)),
          "impressions": int(r.get("impressions", 0))}
         for r in rows],
        key=lambda r: r["date"],
    )


def _shape_queries(rows: list[dict]) -> list[dict]:
    """Pure: raw searchAnalytics rows (dimensions=["query"]) into a
    clicks-sorted list. Direct-testable, no network."""
    return sorted(
        [{"query": r["keys"][0], "clicks": int(r.get("clicks", 0)),
          "impressions": int(r.get("impressions", 0)),
          "position": round(r.get("position", 0), 1)}
         for r in rows],
        key=lambda r: r["clicks"], reverse=True,
    )


def fetch_search_data(session: Session, site: Site, days: int = 30) -> dict | None:
    """Real daily clicks/impressions and top queries for the last `days`
    days. `None` means not connected or not readable right now -- callers
    keep that as null. Search Console's data lags 1-3 days behind today, so
    the window ends 3 days back rather than today."""
    integ = _integration(session, site)
    if integ is None:
        return None
    token = _access_token(session, integ)
    if token is None:
        return None
    site_url = _matching_site_url(token, integ, session, site.hostname)
    if site_url is None:
        return None

    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=days - 1)

    daily_raw = _query(token, site_url, {
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["date"], "rowLimit": days,
    })
    if daily_raw is None:
        integ.last_error = "Search Console query failed"
        session.commit()
        return None

    queries_raw = _query(token, site_url, {
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["query"], "rowLimit": 10,
    })

    integ.last_error = None
    session.commit()

    return {
        "daily": _shape_daily(daily_raw.get("rows", [])),
        "queries": _shape_queries((queries_raw or {}).get("rows", [])),
    }
