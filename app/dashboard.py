"""The dashboard.

Server-rendered, and deliberately a thin client over the same /v1 calls a
partner would make — if something is possible here it is possible through the
API, which is the half that actually gets embedded.

While FIG_DEV_NO_AUTH is on there is no sign-in: every request resolves to the
demo account so the thing can be opened and used immediately.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.api import estate_report, hostname_of
from app.auth import (current_account, end_session, link_user, mint_key,
                      session_user, start_session, verify_access_token)
from app.billing import price_quote, sync_quantity
from app.db import get_session
from app.jobs import enqueue_estate, enqueue_scan, queue_depth
from app.models import Account, ApiKey, Page, Scan, Site
from app.rules.scoring import LAYER_LABEL, LAYER_SUB, verdict

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(config.ROOT / "templates"))

LAYER_META = [(k, LAYER_LABEL[k], LAYER_SUB[k])
              for k in ("craft", "structure", "search", "answers")]


class NeedsSignIn(Exception):
    """Raised by _account and turned into a redirect by the handler in
    main.py, so a signed-out browser lands on /login rather than on a 401."""


def _account(request: Request, session: Session) -> Account:
    account = current_account(request, session)
    if account is None:
        raise NeedsSignIn()
    return account


def _ctx(request: Request, session: Session, account: Account, page: str) -> dict:
    return {
        "request": request,
        "account": account,
        "page": page,
        "dev_no_auth": config.DEV_NO_AUTH,
        # A white-labelled account never sees FIG chrome — the same rule that
        # applies to anything the end client is shown.
        "brand": account.brand_name if account.white_label else "FIG",
        "public_url": config.PUBLIC_URL,
        "user": session_user(request, session),
    }


# --- estate -------------------------------------------------------------


@router.get("/app")
def estate(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    report = estate_report(account=account, session=session)
    counts = {"clean": 0, "check": 0, "fix": 0, "none": 0}
    for row in report["rows"]:
        counts[row["verdict"] or "none"] = counts.get(row["verdict"] or "none", 0) + 1

    ctx = _ctx(request, session, account, "estate")
    ctx.update(report=report, counts=counts, queue=queue_depth(session),
               quote=price_quote(max(account.billable_sites(), 1)))
    return templates.TemplateResponse("estate.html", ctx)


@router.post("/app/sites")
def add_site_form(request: Request, hostname: str = Form(...), client_name: str = Form(default=""),
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


@router.post("/app/scan-estate")
def scan_estate_form(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    enqueue_estate(session, account.id, trigger="manual")
    session.commit()
    return RedirectResponse("/app/queue", status_code=303)


@router.post("/app/sites/{site_id}/scan")
def scan_site_form(request: Request, site_id: str, session: Session = Depends(get_session)):
    account = _account(request, session)
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")
    enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return RedirectResponse(f"/app/sites/{site_id}", status_code=303)


# --- one site -----------------------------------------------------------


@router.get("/app/sites/{site_id}")
def site_detail(site_id: str, request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")

    scan = site.latest_scan()
    pending = any(s.status in ("queued", "running") for s in site.scans)

    findings = list(scan.findings) if scan else []
    grouped = {k: [f for f in findings if f.layer == k] for k, _l, _s in LAYER_META}
    for group in grouped.values():
        group.sort(key=lambda f: (-f.weight, f.check))

    scores = {}
    pages = []
    page_flow = None
    if scan:
        scores = {"craft": scan.score_craft, "structure": scan.score_structure,
                  "search": scan.score_search, "answers": scan.score_answers}
        pages = session.scalars(
            select(Page).where(Page.scan_id == scan.id).order_by(Page.path)
        ).all()
        home = next((p for p in pages if p.path in ("/", "")), pages[0] if pages else None)
        if home and home.section_roles:
            # Mark the first block holding each role a finding named, by index
            # rather than by name -- a page with three "content" blocks should
            # not light all three up.
            named = set()
            for f in findings:
                if f.check == "section_order":
                    for role in set(home.section_roles):
                        if role.replace("_", " ") in f.summary:
                            named.add(role)
            flagged, taken = set(), set()
            for i, role in enumerate(home.section_roles):
                if role in named and role not in taken:
                    flagged.add(i)
                    taken.add(role)
            page_flow = {"path": home.path, "roles": home.section_roles, "flagged": flagged}

    ctx = _ctx(request, session, account, "estate")
    ctx.update(site=site, scan=scan, pending=pending, findings=findings,
               grouped=grouped, scores=scores, pages=pages, page_flow=page_flow,
               layer_meta=LAYER_META,
               verdict=verdict(scan.score) if scan and scan.score is not None else None)
    return templates.TemplateResponse("site.html", ctx)


# --- queue --------------------------------------------------------------


@router.get("/app/queue")
def queue_view(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    site_ids = [s.id for s in account.sites]
    rows = session.scalars(
        select(Scan).where(Scan.site_id.in_(site_ids))
        .order_by(Scan.created_at.desc()).limit(60)
    ).all() if site_ids else []

    by_id = {s.id: s for s in account.sites}
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    scans = [{
        "site_id": s.site_id,
        "hostname": by_id[s.site_id].hostname if s.site_id in by_id else "—",
        "status": s.status, "trigger": s.trigger, "pages_crawled": s.pages_crawled,
        "score": s.score, "verdict": verdict(s.score) if s.score is not None else None,
        "took": s.duration_s(), "created_at": s.created_at, "error": s.error,
    } for s in rows]

    ctx = _ctx(request, session, account, "queue")
    ctx.update(depth=queue_depth(session), scans=scans,
               done_today=sum(1 for s in rows if s.status == "done"
                              and s.created_at and s.created_at >= since),
               failed=sum(1 for s in rows if s.status == "failed"))
    return templates.TemplateResponse("queue.html", ctx)


# --- keys ---------------------------------------------------------------


@router.get("/app/keys")
def keys_view(request: Request, session: Session = Depends(get_session), new: str = ""):
    account = _account(request, session)
    keys = session.scalars(
        select(ApiKey).where(ApiKey.account_id == account.id)
        .order_by(ApiKey.created_at.desc())
    ).all()
    ctx = _ctx(request, session, account, "keys")
    ctx.update(keys=keys, new_key=new or None)
    return templates.TemplateResponse("keys.html", ctx)


@router.post("/app/keys")
def create_key(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    _row, plaintext = mint_key(session, account, label="dashboard")
    session.commit()
    # Shown once, then never again — only the hash is kept.
    return RedirectResponse(f"/app/keys?new={plaintext}", status_code=303)


@router.post("/app/keys/{key_id}/revoke")
def revoke_key(request: Request, key_id: str, session: Session = Depends(get_session)):
    account = _account(request, session)
    key = session.get(ApiKey, key_id)
    if key is None or key.account_id != account.id:
        raise HTTPException(404, "no such key")
    key.revoked = True
    session.commit()
    return RedirectResponse("/app/keys", status_code=303)


# --- billing ------------------------------------------------------------


@router.get("/app/billing")
def billing_view(request: Request, session: Session = Depends(get_session),
                 checkout: str = "", msg: str = ""):
    account = _account(request, session)
    quote = price_quote(max(account.billable_sites(), account.site_floor, 1))
    quote["billable_sites"] = account.billable_sites()
    quote["site_floor"] = account.site_floor
    quote["enabled"] = config.BILLING_ENABLED
    message = msg or {"done": "Checkout completed.",
                      "cancelled": "Checkout cancelled."}.get(checkout, "")
    ctx = _ctx(request, session, account, "billing")
    ctx.update(quote=quote, message=message)
    return templates.TemplateResponse("billing.html", ctx)


@router.post("/app/billing/checkout")
def billing_checkout(request: Request, session: Session = Depends(get_session)):
    from app.billing import checkout as make_checkout
    account = _account(request, session)
    try:
        result = make_checkout(account=account, session=session)
    except HTTPException as exc:
        return RedirectResponse(f"/app/billing?msg={exc.detail}", status_code=303)
    return RedirectResponse(result["url"], status_code=303)


@router.post("/app/billing/sync")
def billing_sync(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    try:
        result = sync_quantity(session, account)
    except HTTPException as exc:
        return RedirectResponse(f"/app/billing?msg={exc.detail}", status_code=303)
    note = f"quantity now {result['quantity']}" if result.get("synced") else result.get("reason", "")
    return RedirectResponse(f"/app/billing?msg={note}", status_code=303)


# --- sign in / out ------------------------------------------------------


@router.get("/login")
def login_page(request: Request, session: Session = Depends(get_session)):
    if current_account(request, session) is not None:
        return RedirectResponse("/app", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "auth_ready": config.AUTH_READY,
        "supabase_url": config.SUPABASE_URL,
        # public by design; the service-role key never reaches a browser
        "supabase_anon_key": config.SUPABASE_ANON_KEY,
    })


@router.post("/auth/session")
async def establish_session(request: Request, payload: dict = Body(...),
                            session: Session = Depends(get_session)):
    """Trade a verified Supabase access token for our own session cookie.

    The token is checked with Supabase, used to find or create the User and
    Account, and then discarded -- we never store it, and it never touches
    JavaScript on any page of ours after this call.
    """
    token = (payload or {}).get("access_token")
    if not token:
        raise HTTPException(400, "access_token is required")
    supabase_user = await verify_access_token(token)
    user = link_user(session, supabase_user)
    start_session(request, user)
    return JSONResponse({"ok": True, "next": "/app", "email": user.email})


@router.get("/logout")
@router.post("/logout")
def logout(request: Request):
    end_session(request)
    return RedirectResponse("/login", status_code=303)
