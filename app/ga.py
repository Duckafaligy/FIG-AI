"""Google Analytics 4 Data API client — the piece the OAuth plumbing in
app/oauth.py was missing. That module gets a token as far as encrypted
storage; this module is what turns a stored token into real numbers.

Nothing here estimates or fabricates a value: a site with no connected
integration, an expired refresh token, or a failed API call all return
`None`, and `app/pages.py` keeps that as `null` rather than guessing.

Google authorization is account-scoped. Reporting selections are explicitly
stored on each Site; the old shared Integration.endpoint is never used as a
reporting fallback. Unselected projects return unavailable, not another site's
numbers.
"""
from __future__ import annotations

import logging
import re
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.models import Integration, Site
from app.secrets_store import SecretsNotConfigured, read_secret, update_secret

log = logging.getLogger("fig.ga")

TOKEN_URL = "https://oauth2.googleapis.com/token"
ADMIN_API = "https://analyticsadmin.googleapis.com/v1beta"
DATA_API = "https://analyticsdata.googleapis.com/v1beta"
PLATFORM = "google_analytics"

# (GA4 metric name, display label) — order drives both the API request and
# the panel's row order.
METRICS = [
    ("sessions", "Sessions"),
    ("averageSessionDuration", "Avg. engagement time"),
    ("bounceRate", "Bounce rate"),
    ("engagedSessions", "Engaged sessions"),
]


def _integration(session: Session, site: Site) -> Integration | None:
    # Authorization is shared; Site.ga_property selects the reporting source.
    integ = session.scalars(select(Integration).where(
        Integration.account_id == site.account_id, Integration.platform == PLATFORM)).first()
    return integ if integ and integ.is_connected() else None


def is_connected(session: Session, site: Site) -> bool:
    return _integration(session, site) is not None


def _access_token(session: Session, integ: Integration) -> str | None:
    """A valid access token, refreshing it against Google if expired. The
    refreshed token is written back so this only round-trips once per hour
    rather than on every call."""
    try:
        creds = read_secret(session, integ.credential_ref)
    except (SecretsNotConfigured, KeyError) as exc:
        log.warning("ga: cannot read stored token for account %s: %s", integ.account_id, exc)
        return None

    if creds.get("expires_at", 0) > time.time() + 60:
        return creds.get("access_token")

    refresh_token = creds.get("refresh_token")
    if not refresh_token:
        integ.last_error = "Google Analytics needs to be reconnected (no refresh token)"
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
        log.warning("ga: token refresh request failed for account %s: %s", integ.account_id, exc)
        return None
    if resp.status_code != 200:
        log.warning("ga: token refresh rejected for account %s: %s %s",
                    integ.account_id, resp.status_code, resp.text[:200])
        integ.last_error = f"Google Analytics token refresh failed: HTTP {resp.status_code}"
        session.commit()
        return None

    tokens = resp.json()
    creds["access_token"] = tokens.get("access_token", creds.get("access_token"))
    creds["expires_at"] = time.time() + tokens.get("expires_in", 0)
    update_secret(session, integ.credential_ref, creds)
    session.commit()
    return creds["access_token"]


def available_properties(session: Session, site: Site) -> list[dict]:
    """Real authorized choices. Refuse incomplete discovery rather than save
    an arbitrary id. Bounded pagination avoids an unbounded provider request.
    API: developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/accountSummaries/list
    """
    integ = _integration(session, site)
    if integ is None:
        raise ValueError("Connect Google Analytics in workspace settings first.")
    token = _access_token(session, integ)
    if not token:
        raise ValueError("Google Analytics authorization is unavailable. Reconnect and retry.")
    choices: dict[str, dict] = {}
    page_token = ""
    seen = set()
    for _ in range(20):
        params = {"pageSize": 200}
        if page_token:
            params["pageToken"] = page_token
        try:
            resp = httpx.get(f"{ADMIN_API}/accountSummaries", params=params,
                             headers={"Authorization": f"Bearer {token}"}, timeout=15.0)
            if resp.status_code != 200:
                raise ValueError("Google Analytics could not list properties. Check permissions and retry.")
            data = resp.json()
            for account in data.get("accountSummaries", []):
                for prop in account.get("propertySummaries", []):
                    name = prop.get("property", "")
                    if isinstance(name, str) and re.fullmatch(r"properties/\d+", name):
                        choices[name] = {"id": name, "name": prop.get("displayName") or name,
                                         "account": account.get("displayName") or ""}
            page_token = data.get("nextPageToken", "")
        except (httpx.HTTPError, TypeError, AttributeError) as exc:
            raise ValueError("Google Analytics property discovery is unavailable. Retry shortly.") from exc
        if not page_token:
            return list(choices.values())
        if page_token in seen:
            break
        seen.add(page_token)
    raise ValueError("Google returned an incomplete property list. Retry before selecting a property.")


def _fmt(key: str, raw: str) -> str:
    value = float(raw)
    if key == "averageSessionDuration":
        minutes, seconds = divmod(int(value), 60)
        return f"{minutes}m {seconds}s"
    if key == "bounceRate":
        return f"{value * 100:.0f}%"
    return f"{value:,.0f}"


def _pct_change(current: float, previous: float) -> float | None:
    if previous <= 0:
        return None
    return round((current - previous) / previous * 100, 1)


def fetch_overview_metrics(session: Session, site: Site) -> list[dict] | None:
    """The `ga` panel on the overview page. `None` means "not connected or
    not readable right now" — the caller keeps that as null."""
    integ = _integration(session, site)
    if integ is None:
        return None
    token = _access_token(session, integ)
    if token is None:
        return None
    prop = site.ga_property
    if not prop or not re.fullmatch(r"properties/\d+", prop):
        return None

    body = {
        "dateRanges": [
            {"startDate": "30daysAgo", "endDate": "today", "name": "current"},
            {"startDate": "60daysAgo", "endDate": "31daysAgo", "name": "previous"},
        ],
        "dimensions": [{"name": "dateRange"}],
        "metrics": [{"name": key} for key, _ in METRICS],
    }
    try:
        resp = httpx.post(f"{DATA_API}/{prop}:runReport",
                          headers={"Authorization": f"Bearer {token}"}, json=body, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("ga: report request failed for site %s: %s", site.id, exc)
        return None
    if resp.status_code != 200:
        log.warning("ga: report rejected for site %s: %s %s",
                    site.id, resp.status_code, resp.text[:300])
        integ.last_error = f"GA4 report failed: HTTP {resp.status_code}"
        session.commit()
        return None

    rows = {row["dimensionValues"][0]["value"]: row["metricValues"]
            for row in resp.json().get("rows", [])}
    current, previous = rows.get("current"), rows.get("previous")
    if current is None:
        return [{"value": None, "label": label, "delta": None} for _, label in METRICS]

    integ.last_error = None
    session.commit()
    panel = []
    for i, (key, label) in enumerate(METRICS):
        cur_raw = current[i]["value"]
        prev_raw = previous[i]["value"] if previous else None
        delta = _pct_change(float(cur_raw), float(prev_raw)) if prev_raw is not None else None
        panel.append({"value": _fmt(key, cur_raw), "label": label, "delta": delta})
    return panel


def _report_target(session: Session, site: Site):
    """(integration, token, property) when a report can be requested, else None."""
    integ = _integration(session, site)
    if integ is None:
        return None
    prop = site.ga_property
    if not prop or not re.fullmatch(r"properties/\d+", prop):
        return None
    token = _access_token(session, integ)
    return (integ, token, prop) if token else None


def _rows(report: dict) -> list[tuple[list[str], list[str]]]:
    return [([d["value"] for d in r.get("dimensionValues", [])],
             [m["value"] for m in r.get("metricValues", [])])
            for r in report.get("rows", [])]


def fetch_detail(session: Session, site: Site) -> dict | None:
    """The project Analytics page: sessions per day for the last 60 days
    (split into this 30 and the 30 before), top landing pages and channel
    groups for the last 30. One batchRunReports call. `None` means not
    connected or not readable right now; nothing is filled in."""
    target = _report_target(session, site)
    if target is None:
        return None
    integ, token, prop = target
    last30 = [{"startDate": "29daysAgo", "endDate": "today"}]
    body = {"requests": [
        {"dateRanges": [{"startDate": "59daysAgo", "endDate": "today"}],
         "dimensions": [{"name": "date"}], "metrics": [{"name": "sessions"}],
         "orderBys": [{"dimension": {"dimensionName": "date"}}], "limit": 100},
        {"dateRanges": last30, "dimensions": [{"name": "landingPage"}],
         "metrics": [{"name": "sessions"}, {"name": "engagementRate"}],
         "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}], "limit": 10},
        {"dateRanges": last30, "dimensions": [{"name": "sessionDefaultChannelGroup"}],
         "metrics": [{"name": "sessions"}],
         "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}], "limit": 8},
    ]}
    try:
        resp = httpx.post(f"{DATA_API}/{prop}:batchRunReports",
                          headers={"Authorization": f"Bearer {token}"}, json=body, timeout=15.0)
    except httpx.HTTPError as exc:
        log.warning("ga: detail request failed for site %s: %s", site.id, exc)
        return None
    if resp.status_code != 200:
        log.warning("ga: detail rejected for site %s: %s %s",
                    site.id, resp.status_code, resp.text[:300])
        integ.last_error = f"GA4 report failed: HTTP {resp.status_code}"
        session.commit()
        return None
    reports = resp.json().get("reports", [])
    if len(reports) != 3:
        return None
    daily_rows, page_rows, channel_rows = (_rows(r) for r in reports)

    # GA leaves out days with no sessions, so the 60 days are laid out here
    # and missing ones are real zeros.
    # ponytail: days counted in UTC, the property's own timezone can shift the edge by one day.
    today = time.gmtime()
    end = time.mktime((today.tm_year, today.tm_mon, today.tm_mday, 12, 0, 0, 0, 0, -1))
    days = [time.strftime("%Y%m%d", time.localtime(end - 86400 * i)) for i in range(59, -1, -1)]
    by_day = {d[0]: int(float(m[0])) for d, m in daily_rows}
    counts = [by_day.get(d, 0) for d in days]
    return {
        "days": [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in days[30:]],
        "current": counts[30:],
        "previous": counts[:30],
        "pages": [{"path": d[0], "sessions": int(float(m[0])),
                   "engaged": round(float(m[1]) * 100)} for d, m in page_rows],
        "channels": [{"name": d[0], "sessions": int(float(m[0]))} for d, m in channel_rows],
    }
