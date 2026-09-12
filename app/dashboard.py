"""The dashboard.

Rebuilt to the Figma design: a dark rail, a search-and-project top bar, and a
grid of cards. Every page renders through `dash/shell.html` so the rail and
top bar are defined once.

While FIG_DEV_NO_AUTH is on there is no sign-in: every request resolves to the
demo account so the thing can be opened and used immediately.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config, dashdata, publishing, reporting, roadmap
from app.api import hostname_of
from app.auth import (current_account, end_session, link_user, mint_key,
                      session_user, start_session, verify_access_token)
from app.billing import price_quote, sync_quantity
from app.db import get_session
from app.jobs import enqueue_estate, enqueue_scan, queue_depth
from app.models import Account, ApiKey, Integration, Site
from app.rules.scoring import verdict

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(config.ROOT / "templates"))


class NeedsSignIn(Exception):
    """Raised by _account and turned into a redirect by the handler in
    main.py, so a signed-out browser lands on /login rather than on a 401."""


def _account(request: Request, session: Session) -> Account:
    account = current_account(request, session)
    if account is None:
        raise NeedsSignIn()
    return account


def _ctx(request: Request, session: Session, account: Account, page: str) -> dict:
    """Everything the shell needs on every page."""
    sites = [s for s in account.sites if s.is_active]
    latest = [s.latest_scan() for s in sites]
    alerts = sum(1 for sc in latest if sc for f in sc.findings if f.severity == "high")
    return {
        "request": request,
        "account": account,
        "page": page,
        "dev_no_auth": config.DEV_NO_AUTH,
        "user": session_user(request, session),
        "project": f"{account.name}'s project",
        "counts": {
            "sites": len(sites),
            "alerts": min(alerts, 99),
            "running": sum(1 for s in sites
                           if any(x.status in ("queued", "running") for x in s.scans)),
        },
        "trial": {"on_trial": account.on_trial(), "days": account.trial_days_left()},
        "public_url": config.PUBLIC_URL,
    }


# --- overview ------------------------------------------------------------


@router.get("/app")
def overview(request: Request, session: Session = Depends(get_session),
             days: int = Query(default=7)):
    account = _account(request, session)
    if days not in (1, 7, 30, 90):
        days = 7
    ctx = _ctx(request, session, account, "overview")
    ctx["d"] = dashdata.overview(session, account, days=days)
    return templates.TemplateResponse("dash/overview.html", ctx)


# --- sites ---------------------------------------------------------------


@router.get("/app/sites")
def sites_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "sites")
    ctx["e"] = reporting.estate(session, account)
    return templates.TemplateResponse("dash/sites.html", ctx)


@router.get("/app/sites/{site_id}")
def site_detail(site_id: str, request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")

    scan = site.latest_scan()
    pending = any(s.status in ("queued", "running") for s in site.scans)
    findings = list(scan.findings) if scan else []
    grouped = {k: sorted([f for f in findings if f.layer == k],
                         key=lambda f: (-f.weight, f.check))
               for k, _l, _s in reporting.LAYER_META}
    history = reporting.site_history(site)

    ctx = _ctx(request, session, account, "sites")
    ctx.update(site=site, scan=scan, pending=pending, findings=findings,
               grouped=grouped, layer_meta=reporting.LAYER_META, history=history,
               chart=reporting.chart(history),
               delta=reporting.site_delta(site),
               pages=reporting.page_rows(session, scan) if scan else [],
               scores={k: getattr(scan, f"score_{k}") for k in reporting.LAYERS}
                      if scan else {},
               verdict=verdict(scan.score) if scan and scan.score is not None else None)
    return templates.TemplateResponse("dash/site.html", ctx)


@router.post("/app/sites")
def add_site_form(request: Request, hostname: str = Form(...),
                  client_name: str = Form(default=""),
                  session: Session = Depends(get_session)):
    account = _account(request, session)
    host = hostname_of(hostname)
    site = session.scalars(
        select(Site).where(Site.account_id == account.id, Site.hostname == host)
    ).first()
    if site is None:
        site = Site(account_id=account.id, hostname=host,
                    client_name=client_name.strip() or None)
        session.add(site)
        session.flush()
    else:
        site.is_active = True
    enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return RedirectResponse(f"/app/sites/{site.id}", status_code=303)


@router.post("/app/sites/{site_id}/scan")
def scan_site_form(site_id: str, request: Request,
                   session: Session = Depends(get_session)):
    account = _account(request, session)
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")
    enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return RedirectResponse(f"/app/sites/{site_id}", status_code=303)


@router.post("/app/audit-all")
def audit_all(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    enqueue_estate(session, account.id, trigger="manual")
    session.commit()
    return RedirectResponse("/app/history", status_code=303)


# --- the layer reports ---------------------------------------------------


@router.get("/app/seo")
def seo_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "seo")
    ctx["v"] = reporting.layer_view(session, account, "search")
    ctx["d"] = dashdata.overview(session, account)
    ctx["pub"] = publishing.queue(session, account, layer="search")
    return templates.TemplateResponse("dash/layer.html", ctx)


@router.get("/app/geo")
def geo_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "geo")
    ctx["v"] = reporting.layer_view(session, account, "answers")
    ctx["d"] = dashdata.overview(session, account)
    ctx["pub"] = publishing.queue(session, account, layer="answers")
    return templates.TemplateResponse("dash/layer.html", ctx)


@router.get("/app/findings")
def findings_view(request: Request, session: Session = Depends(get_session),
                  check: str = ""):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "findings")
    ctx["f"] = reporting.findings_across(session, account, check or None)
    ctx["layer_meta"] = reporting.LAYER_META
    return templates.TemplateResponse("dash/findings.html", ctx)


@router.get("/app/notifications")
def notifications_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "notifications")
    ctx["n"] = reporting.notifications(session, account)
    return templates.TemplateResponse("dash/notifications.html", ctx)


@router.get("/app/history")
def history_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    ctx = _ctx(request, session, account, "history")
    ctx["a"] = reporting.audits(session, account)
    ctx["an"] = reporting.analytics(session, account)
    ctx["depth"] = queue_depth(session)
    return templates.TemplateResponse("dash/history.html", ctx)


# --- settings ------------------------------------------------------------


@router.get("/app/settings")
def settings_view(request: Request, session: Session = Depends(get_session),
                  tab: str = "account", new: str = "", checkout: str = "",
                  msg: str = ""):
    account = _account(request, session)
    if tab not in ("account", "billing", "api", "integrations", "roadmap"):
        tab = "account"

    quote = price_quote(max(account.billable_sites(), account.site_floor, 1))
    quote["billable_sites"] = account.billable_sites()
    quote["site_floor"] = account.site_floor
    quote["enabled"] = config.BILLING_ENABLED
    quote["trial_days_left"] = account.trial_days_left()
    quote["on_trial"] = account.on_trial()

    keys = session.scalars(
        select(ApiKey).where(ApiKey.account_id == account.id)
        .order_by(ApiKey.created_at.desc())
    ).all()

    integrations = session.scalars(
        select(Integration).where(Integration.site_id.in_(
            [s.id for s in account.sites])) if account.sites else select(Integration).where(
            Integration.id == "none")).all()
    by_site = {i.site_id: i for i in integrations}

    ctx = _ctx(request, session, account, "settings")
    ctx.update(tab=tab, quote=quote, keys=keys, new_key=new or None,
               sites=[s for s in account.sites if s.is_active],
               integrations=integrations, integ_by_site=by_site,
               roadmap=roadmap.summary(),
               message=msg or {"done": "Checkout completed.",
                               "cancelled": "Checkout cancelled."}.get(checkout, ""))
    return templates.TemplateResponse("dash/settings.html", ctx)


@router.post("/app/settings/account")
def rename_account(request: Request, name: str = Form(...),
                   session: Session = Depends(get_session)):
    account = _account(request, session)
    cleaned = name.strip()[:80]
    if cleaned:
        account.name = cleaned
        session.commit()
    return RedirectResponse("/app/settings?msg=Saved", status_code=303)


@router.post("/app/keys")
def create_key(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    _row, plaintext = mint_key(session, account, label="dashboard")
    session.commit()
    # Shown once, then never again -- only the hash is kept.
    return RedirectResponse(f"/app/settings?tab=api&new={plaintext}", status_code=303)


@router.post("/app/keys/{key_id}/revoke")
def revoke_key(key_id: str, request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    key = session.get(ApiKey, key_id)
    if key is None or key.account_id != account.id:
        raise HTTPException(404, "no such key")
    key.revoked = True
    session.commit()
    return RedirectResponse("/app/settings?tab=api", status_code=303)


@router.post("/app/billing/checkout")
def billing_checkout(request: Request, session: Session = Depends(get_session)):
    from app.billing import checkout as make_checkout
    account = _account(request, session)
    try:
        result = make_checkout(account=account, session=session)
    except HTTPException as exc:
        return RedirectResponse(f"/app/settings?tab=billing&msg={exc.detail}",
                                status_code=303)
    return RedirectResponse(result["url"], status_code=303)


@router.post("/app/billing/sync")
def billing_sync(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    try:
        result = sync_quantity(session, account)
    except HTTPException as exc:
        return RedirectResponse(f"/app/settings?tab=billing&msg={exc.detail}",
                                status_code=303)
    note = (f"quantity now {result['quantity']}" if result.get("synced")
            else result.get("reason", ""))
    return RedirectResponse(f"/app/settings?tab=billing&msg={note}", status_code=303)


# --- sign in / out -------------------------------------------------------


def _auth_ctx(request: Request, mode: str) -> dict:
    return {
        "request": request,
        "mode": mode,
        "auth_ready": config.AUTH_READY,
        "site_url": config.MARKETING_URL,
        "supabase_url": config.SUPABASE_URL,
        "supabase_anon_key": config.SUPABASE_ANON_KEY,
    }


@router.get("/login")
def login_page(request: Request, session: Session = Depends(get_session)):
    if current_account(request, session) is not None:
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("login.html", _auth_ctx(request, "signin"))


@router.get("/signup")
def signup_page(request: Request, session: Session = Depends(get_session)):
    if current_account(request, session) is not None:
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("login.html", _auth_ctx(request, "signup"))


@router.post("/auth/session")
async def establish_session(request: Request, payload: dict = Body(...),
                            session: Session = Depends(get_session)):
    """Trade a verified Supabase access token for our own session cookie."""
    token = (payload or {}).get("access_token")
    if not token:
        raise HTTPException(400, "access_token is required")
    supabase_user = await verify_access_token(token)
    user = link_user(session, supabase_user, (payload or {}).get("account_name"))
    start_session(request, user)
    return JSONResponse({"ok": True, "next": "/app", "email": user.email})


@router.get("/logout")
@router.post("/logout")
def logout(request: Request):
    end_session(request)
    return RedirectResponse("/login", status_code=303)


# --- the publish console -------------------------------------------------


@router.post("/app/changes/propose")
def propose_changes(request: Request, session: Session = Depends(get_session)):
    """Derive publishable changes from every site's latest audit."""
    account = _account(request, session)
    made = 0
    for site in account.sites:
        if site.is_active:
            made += len(publishing.propose(session, site))
    return RedirectResponse("/app/seo", status_code=303)


@router.post("/app/changes/{change_id}/{action}")
def change_action(change_id: str, action: str, request: Request,
                  session: Session = Depends(get_session)):
    account = _account(request, session)
    if action == "approve":
        publishing.approve(session, account, change_id)
    elif action == "reject":
        publishing.reject(session, account, change_id)
    elif action == "publish":
        publishing.publish(session, account, change_id)
    elif action == "revert":
        publishing.revert(session, account, change_id)
    else:
        raise HTTPException(404, "no such action")
    back = request.headers.get("referer") or "/app/seo"
    return RedirectResponse(back, status_code=303)


@router.post("/app/integrations")
def connect_integration(request: Request, site_id: str = Form(...),
                        platform: str = Form(...), endpoint: str = Form(default=""),
                        credential: str = Form(default=""),
                        session: Session = Depends(get_session)):
    account = _account(request, session)
    publishing.connect(session, account, site_id, platform, endpoint, credential)
    return RedirectResponse("/app/settings?tab=integrations", status_code=303)


@router.post("/app/integrations/{integration_id}/disconnect")
def disconnect_integration(integration_id: str, request: Request,
                           session: Session = Depends(get_session)):
    account = _account(request, session)
    publishing.disconnect(session, account, integration_id)
    return RedirectResponse("/app/settings?tab=integrations", status_code=303)
