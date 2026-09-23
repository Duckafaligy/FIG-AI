"""The workspace JSON API — what the Next.js frontend in `frontend/` reads.

Two APIs live in this process and they are deliberately different:

  * `/v1` (`app/api.py`) is the **partner** API. Authenticated with a
    `fig_live_*` key, versioned, stable, meant to be embedded by an agency or
    a platform reselling FIG. Changing it breaks someone else's build.
  * `/api` (here) is the **workspace** API. Authenticated with this app's own
    session cookie, shaped to whatever the frontend needs, and free to change
    alongside it. One endpoint per surface, because that is how the frontend
    renders — a page does one request, not eleven.

Everything here delegates to `app/pages.py` for the queries, so there is one
implementation of "what is on the overview" rather than two that drift.

Auth: `current_account` resolves the session cookie. With `FIG_DEV_NO_AUTH=1`
it resolves to the seeded demo account so the frontend can be developed
without a sign-in flow; that must be 0 before anything is public.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app import account_data, billing, config, content, pages, publishing
from app.auth import current_account, end_session, session_user, start_session
from app.db import get_session
from app.jobs import enqueue_estate, enqueue_scan, queue_depth
from app.models import Account, Site, ContentPost, User
from app.api import public_hostname

router = APIRouter(prefix="/api", tags=["workspace"])


# --- plumbing ------------------------------------------------------------


def _account(request: Request, session: Session) -> Account:
    account = current_account(request, session)
    if account is None:
        raise HTTPException(401, "sign in required")
    return account


def _require_scanning_allowed(account: Account) -> None:
    """Trial enforcement. A scan is the cost-incurring action here -- it
    crawls a real site and calls the LLM -- so it's the one thing gated once
    the trial runs out with nothing subscribed. Everything else (existing
    data, drafts, settings, billing) stays fully visible and editable, so
    someone whose trial lapsed can still see what they had and subscribe.
    The seeded demo account is exempt: FIG_DEV_NO_AUTH and the public
    showcase both resolve to it, and its trial (set once, at seed time) is
    permanently in the past."""
    if account.slug == config.DEMO_ACCOUNT_SLUG:
        return
    if account.trial_expired():
        raise HTTPException(
            402,
            "Your free trial has ended. Subscribe in Settings → Billing "
            "to keep scanning sites.")


def _public(payload: dict) -> dict:
    """Drop the ORM objects `pages.py` keeps for its own use.

    The `_`-prefixed keys exist so the page functions can pass models around
    internally. Anything starting with `_` never leaves this process.
    """
    return {k: v for k, v in payload.items() if not k.startswith("_")}


def _project(session: Session, account: Account, project_id: str) -> Site | None:
    owned = pages.sites_of(session, account)
    if project_id:
        for s in owned:
            if s.id == project_id:
                return s
        raise HTTPException(404, "no such project in this workspace")
    return owned[0] if owned else None


# --- session -------------------------------------------------------------


@router.get("/me")
def me(request: Request, session: Session = Depends(get_session)):
    """Who the caller is. The frontend calls this first to decide whether to
    render the workspace or bounce to /signin."""
    account = current_account(request, session)
    if account is None:
        return {"signed_in": False, "dev_no_auth": config.DEV_NO_AUTH}
    user = session_user(request, session)
    return {
        "signed_in": True,
        "dev_no_auth": config.DEV_NO_AUTH,
        "user": {"id": user.id, "email": user.email} if user else None,
        "account": {
            "id": account.id, "name": account.name, "slug": account.slug,
            "kind": account.kind,
            "on_trial": account.on_trial(),
            "trial_days_left": account.trial_days_left(),
            "projects": len(pages.sites_of(session, account)),
        },
    }


@router.post("/session")
async def establish(request: Request, payload: dict = Body(...),
                    session: Session = Depends(get_session)):
    """Exchange a Supabase access token for this app's session cookie.

    The token is verified against Supabase server-side and then thrown away —
    only our own user id goes in the cookie. The frontend never has to store
    or forward the Supabase token again.
    """
    token = (payload or {}).get("access_token", "")
    if not token:
        raise HTTPException(400, "access_token required")
    from app.auth import link_user, verify_access_token

    claims = await verify_access_token(token)
    if claims is None:
        raise HTTPException(401, "that token did not verify")
    workspace = (payload or {}).get("workspace_name") or ""
    user = link_user(session, claims, account_name=workspace or None)
    start_session(request, user)
    return {"ok": True, "email": user.email}


@router.post("/logout")
def logout(request: Request):
    end_session(request)
    return {"ok": True}


@router.post("/session/revoke")
async def revoke_sessions(request: Request, payload: dict = Body(...),
                          session: Session = Depends(get_session)):
    """End every FIG session for the person this Supabase token belongs to.

    The reset-password page calls this right after a password change, so a
    session someone else already holds (a stolen cookie, a shared computer) does
    not survive the reset. It answers the same way whatever the token, so it
    cannot be used to find out who has an account.
    """
    from app.auth import verify_access_token
    token = (payload or {}).get("access_token", "")
    claims = None
    if token:
        try:
            claims = await verify_access_token(token)
        except HTTPException:
            claims = None      # verify_access_token raises on a bad token; that must look the same as a good one
    if claims:
        user = session.scalars(select(User).where(User.supabase_uid == claims["id"])).first()
        if user is not None:
            user.session_epoch = (user.session_epoch or 0) + 1
            session.commit()
    return {"ok": True}


@router.post("/account/delete")
def delete_account(request: Request, payload: dict = Body(...),
                   session: Session = Depends(get_session)):
    """Delete this workspace and everything in it. Requires the account email
    typed as confirmation. POST rather than DELETE-with-a-body, which proxies
    and CDNs are free to drop."""
    account = _account(request, session)
    user = session_user(request, session)
    if user is None:
        raise HTTPException(401, "sign in required")
    try:
        result = account_data.delete_workspace(
            session, account, user, confirm=(payload or {}).get("confirm", ""))
    except account_data.DeletionRefused as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    end_session(request)
    return result


# --- the surfaces --------------------------------------------------------


@router.get("/projects")
def projects(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.projects(session, account))


@router.get("/overview")
def overview(request: Request, project: str = Query(default=""),
             session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.overview(session, account,
                                  _project(session, account, project)))


@router.get("/seo")
def seo(request: Request, project: str = Query(default=""),
        tab: str = Query(default="queue"),
        session: Session = Depends(get_session)):
    account = _account(request, session)
    if tab not in ("queue", "review", "approved"):
        tab = "queue"
    return _public(pages.seo(session, account,
                             _project(session, account, project), tab))


@router.get("/geo")
def geo(request: Request, project: str = Query(default=""),
        session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.geo(session, account,
                             _project(session, account, project)))


@router.get("/notifications")
def notifications(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.notifications(session, account))


@router.get("/history")
def history(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.history(session, account))


@router.get("/settings")
def settings(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return _public(pages.settings(session, account))


@router.patch("/settings/profile")
def update_profile(request: Request, payload: dict = Body(...),
                   session: Session = Depends(get_session)):
    """Rename the workspace. The name is the only editable profile field.

    The slug and contact email are deliberately not settable here: the slug
    appears in URLs, and the email is what billing and account recovery hang
    off, so changing either belongs to a flow that proves it is the owner.
    """
    account = _account(request, session)
    raw = (payload or {}).get("name")
    if not isinstance(raw, str):
        raise HTTPException(422, "a workspace name is required")
    name = " ".join(raw.split())          # trims and collapses runs of whitespace
    if not 2 <= len(name) <= 80:
        raise HTTPException(422, "a workspace name is 2 to 80 characters")
    if any(not ch.isprintable() for ch in name):
        raise HTTPException(422, "a workspace name cannot contain control characters")
    account.name = name
    session.commit()
    return {"ok": True, "profile": {"name": account.name, "slug": account.slug}}


# --- things the frontend needs to be able to do --------------------------


@router.post("/projects")
def add_project(request: Request, payload: dict = Body(...),
                session: Session = Depends(get_session)):
    """Add a project and immediately queue its first audit."""
    account = _account(request, session)
    _require_scanning_allowed(account)
    raw = (payload or {}).get("hostname", "")
    if not raw:
        raise HTTPException(400, "a hostname is required")
    # Full validation (syntax + DNS resolves to a public address), not just
    # syntax -- this is a real user submitting an arbitrary hostname, same
    # trust level as the free /scan endpoint. The crawler re-checks on every
    # request regardless, but failing here means a clear 422 instead of a
    # Site row that can only ever produce a failed scan.
    host = public_hostname(raw)

    # Checked against every row for this account, active or not: the
    # database's own (account_id, hostname) uniqueness constraint doesn't
    # care whether a prior Site was deactivated by `remove_project`, but
    # `pages.sites_of()` only returns active ones -- comparing against that
    # let a removed-then-re-added hostname reach the insert and hit the
    # constraint as an unhandled IntegrityError (500), found live in
    # production (FIG-AI-BACKEND-4).
    existing = session.scalar(
        select(Site).where(Site.account_id == account.id, Site.hostname == host))
    if existing is not None and existing.is_active:
        raise HTTPException(409, f"{host} is already in this workspace")

    if existing is not None:
        # Re-adding a project you'd previously removed: revive the same
        # row (and so its scan/finding history) rather than fail on the
        # constraint or fork a second row for the same hostname.
        site = existing
        site.is_active = True
        if (payload or {}).get("name"):
            site.client_name = payload["name"]
        if (payload or {}).get("label"):
            site.label = payload["label"]
        session.commit()
    else:
        site = Site(account_id=account.id, hostname=host,
                    client_name=(payload or {}).get("name") or None,
                    label=(payload or {}).get("label") or None)
        session.add(site)
        session.commit()
        session.refresh(site)

    scan = enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    # The subscription is billed per active site: keep its quantity in step.
    billing.try_sync(session, account)
    return {"id": site.id, "hostname": site.hostname, "scan_id": scan.id}


@router.patch("/projects/{project_id}")
def rename_project(project_id: str, request: Request, payload: dict = Body(...),
                   session: Session = Depends(get_session)):
    account = _account(request, session)
    site = _project(session, account, project_id)
    if site is None:
        raise HTTPException(404, "no such project")
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
        raise HTTPException(422, "Project name must contain 1–80 characters")
    site.client_name = name.strip()
    session.commit()
    return {"ok": True, "id": site.id, "name": site.client_name}


@router.delete("/projects/{project_id}")
def remove_project(project_id: str, request: Request,
                   session: Session = Depends(get_session)):
    """Deactivate a project. Not a delete: the audit history stays, and the
    per-site meter stops counting it."""
    account = _account(request, session)
    site = _project(session, account, project_id)
    if site is None:
        raise HTTPException(404, "no such project")
    site.is_active = False
    session.commit()
    billing.try_sync(session, account)
    return {"ok": True, "id": site.id, "billable_sites": account.billable_sites()}


@router.post("/projects/{project_id}/share")
def share_project(project_id: str, request: Request, payload: dict = Body(...),
                  session: Session = Depends(get_session)):
    """Turns the public report link for this site's latest finished scan on
    or off. Off by default (Site.reports_public) -- this is the only way an
    account-owned scan ever becomes reachable at GET /scan/{scan_id}
    (app/public.py), which otherwise 404s it even if someone has the id."""
    account = _account(request, session)
    site = _project(session, account, project_id)
    if site is None:
        raise HTTPException(404, "no such project")
    site.reports_public = bool((payload or {}).get("public"))
    session.commit()
    latest = site.latest_scan()
    report_url = (f"{config.FRONTEND_URL}/report/{latest.id}"
                  if site.reports_public and latest else None)
    return {"ok": True, "public": site.reports_public, "report_url": report_url}


@router.post("/projects/{project_id}/audit")
def audit_project(project_id: str, request: Request,
                  session: Session = Depends(get_session)):
    account = _account(request, session)
    _require_scanning_allowed(account)
    site = _project(session, account, project_id)
    if site is None:
        raise HTTPException(404, "no such project")
    scan = enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return {"ok": True, "scan_id": scan.id, "queue": queue_depth(session)}


@router.get("/project-settings")
def project_settings(request: Request, project: str = Query(default=""),
                     session: Session = Depends(get_session)):
    """/app/settings is per-project (its connectors), the same `?project=`
    scoping as /api/overview, /api/seo and /api/geo -- an explicit,
    non-empty id 404s if it isn't yours; empty defaults to the account's
    first site, same as those three, and a zero-site account gets an empty,
    non-error shape rather than a 404."""
    account = _account(request, session)
    return _public(pages.project_settings(session, account,
                                          _project(session, account, project)))


@router.post("/audit-all")
def audit_all(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    _require_scanning_allowed(account)
    scans = enqueue_estate(session, account.id, trigger="manual")
    session.commit()
    return {"ok": True, "queued": len(scans), "queue": queue_depth(session)}


# --- the content queue ---------------------------------------------------


@router.post("/content/propose")
def content_propose(request: Request, session: Session = Depends(get_session)):
    """Turn the latest findings into briefs across every active project."""
    account = _account(request, session)
    made = 0
    for site in pages.sites_of(session, account):
        made += len(content.propose(session, site))
    return {"ok": True, "briefs": made}


@router.post("/content")
def content_add(request: Request, payload: dict = Body(...),
                session: Session = Depends(get_session)):
    account = _account(request, session)
    try:
        post = content.add(
            session, account,
            site_id=(payload or {}).get("project_id", ""),
            title=(payload or {}).get("title", ""),
            category=(payload or {}).get("category", "blog"),
            priority=(payload or {}).get("priority", "medium"),
            keyword=(payload or {}).get("keyword", ""),
            body=(payload or {}).get("body", ""))
    except content.Refused as exc:
        raise HTTPException(422, str(exc)) from exc
    return _post_json(session, post)


@router.get("/content")
def content_library(request: Request, project: str = Query(default=""),
                    state: str = Query(default=""), q: str = Query(default="", max_length=200),
                    limit: int = Query(default=30, ge=1, le=100),
                    offset: int = Query(default=0, ge=0),
                    session: Session = Depends(get_session)):
    """Account-scoped content, with bounded pagination and real empty results."""
    account = _account(request, session)
    filters = [Site.account_id == account.id]
    if project:
        _project(session, account, project)
        filters.append(ContentPost.site_id == project)
    if state:
        if state not in content.STATES:
            raise HTTPException(422, "Unknown content status")
        filters.append(ContentPost.state == state)
    if q.strip():
        filters.append(ContentPost.title.contains(q.strip(), autoescape=True))
    query = select(ContentPost).join(Site, ContentPost.site_id == Site.id).where(*filters)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    posts = session.scalars(query.order_by(ContentPost.created_at.desc(), ContentPost.id)
                           .offset(offset).limit(limit)).all()
    return {"items": [_post_json(session, post) for post in posts],
            "total": total, "limit": limit, "offset": offset,
            "projects": [{"id": site.id, "name": site.client_name or site.hostname,
                          "hostname": site.hostname}
                         for site in pages.sites_of(session, account)]}


@router.get("/content/{post_id}")
def content_get(post_id: str, request: Request,
                session: Session = Depends(get_session)):
    account = _account(request, session)
    try:
        post = content._owned(session, account, post_id)
    except content.Refused as exc:
        raise HTTPException(404, str(exc)) from exc
    report = content.score_post(post)
    return _post_json(session, post) | {
        "report": report,
        "checks": [{"key": k, "weight": w, "label": label}
                   for k, w, label in content.CHECK_WEIGHTS],
    }


@router.patch("/content/{post_id}")
def content_patch(post_id: str, request: Request, payload: dict = Body(...),
                  session: Session = Depends(get_session)):
    """Save a draft. Re-scored on every save."""
    account = _account(request, session)
    try:
        post = content._owned(session, account, post_id)
    except content.Refused as exc:
        raise HTTPException(404, str(exc)) from exc
    before = (post.title, post.body)
    if "body" in (payload or {}):
        post.body = (payload["body"] or "").strip() or None
    if "title" in (payload or {}) and payload["title"]:
        post.title = payload["title"].strip()
    if "keyword" in (payload or {}):
        post.target_keyword = (payload["keyword"] or "").strip().lower() or None
    if (post.title, post.body) != before:
        content.reopen_if_scheduled(post)
    content.rescore(post)
    session.commit()
    return _post_json(session, post) | {"report": content.score_post(post)}


@router.post("/content/{post_id}/move")
def content_move(post_id: str, request: Request, payload: dict = Body(...),
                 session: Session = Depends(get_session)):
    account = _account(request, session)
    try:
        post = content.move(session, account, post_id,
                            (payload or {}).get("to", ""))
    except content.Refused as exc:
        # 409, not 500: an illegal transition is a valid request the rules
        # refuse, and the frontend should show the reason.
        raise HTTPException(409, str(exc)) from exc
    return _post_json(session, post)


@router.post("/content/{post_id}/draft")
def content_draft(post_id: str, request: Request,
                  session: Session = Depends(get_session)):
    """Not built, and says so. See `content.draft` and CLAUDE.md."""
    account = _account(request, session)
    try:
        content.draft(session, account, post_id)
    except content.Refused as exc:
        raise HTTPException(501, str(exc)) from exc
    return {"ok": True}


def _post_json(session: Session, post) -> dict:
    site = session.get(Site, post.site_id)
    return {
        "id": post.id, "title": post.title, "slug": post.slug,
        "category": post.category, "brief": post.brief, "body": post.body,
        "word_count": post.word_count, "state": post.state,
        "priority": post.priority, "keyword": post.target_keyword,
        "seo_score": post.seo_score,
        "search_volume": post.search_volume,
        "keyword_difficulty": post.keyword_difficulty,
        "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
        "overdue": content.is_overdue(post),
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "project": {"id": site.id, "hostname": site.hostname} if site else None,
        "next_action": content._next_action(post.state),
    }


# --- the change queue ----------------------------------------------------


@router.get("/changes")
def changes(request: Request, layer: str = Query(default=""), project: str = Query(default=""),
            session: Session = Depends(get_session)):
    account = _account(request, session)
    site_id = _project(session, account, project).id if project else None
    result = publishing.queue(session, account, layer=layer or None, site_id=site_id)
    # _public() only strips top-level keys; each row also carries its own
    # internal-only "_change" (the raw ORM object), one level down.
    result["rows"] = [_public(row) for row in result["rows"]]
    return _public(result)


@router.post("/changes/propose")
def changes_propose(request: Request, project: str = Query(default=""),
                    session: Session = Depends(get_session)):
    account = _account(request, session)
    if project:
        site = _project(session, account, project)
        if site is None:
            raise HTTPException(404, "no such project")
        sites = [site]
    else:
        sites = pages.sites_of(session, account)
    made = 0
    for site in sites:
        made += len(publishing.propose(session, site))
    return {"ok": True, "changes": made}


@router.post("/changes/{change_id}/{action}")
def change_action(change_id: str, action: str, request: Request,
                  session: Session = Depends(get_session)):
    account = _account(request, session)
    fn = {"approve": publishing.approve, "reject": publishing.reject,
          "publish": publishing.publish, "revert": publishing.revert}.get(action)
    if fn is None:
        raise HTTPException(404, "no such action")
    result = fn(session, account, change_id)
    if isinstance(result, dict):
        # publish/revert report whether they actually managed it, and why not.
        # 409 with the real reason, not a generic failure: "no CMS is
        # connected" is something the person can act on.
        if not result.get("ok", True):
            raise HTTPException(409, result.get("reason", "that did not work"))
        return result
    return {"ok": True, "id": change_id, "state": result.state}


# --- integrations --------------------------------------------------------


@router.post("/integrations")
def connect(request: Request, payload: dict = Body(...),
            session: Session = Depends(get_session)):
    """Record a CMS connection.

    Only a reference and a last-four hint are stored, never the credential —
    see `publishing.connect`. Always 200: a rejected credential is not an
    HTTP error, it's `connected: false` with `error` saying why (wrong
    password, adapter not built yet, ...), so the frontend can show the
    real reason instead of a generic failure.
    """
    account = _account(request, session)
    p = payload or {}
    integration = publishing.connect(
        session, account, p.get("project_id", ""), p.get("platform", ""),
        p.get("endpoint", ""), p.get("credential", ""))
    return {"id": integration.id, "platform": integration.platform,
            "connected": integration.is_connected(),
            "hint": integration.credential_hint,
            "error": integration.last_error}


@router.post("/integrations/{integration_id}/disconnect")
def disconnect(integration_id: str, request: Request,
               session: Session = Depends(get_session)):
    account = _account(request, session)
    publishing.disconnect(session, account, integration_id)
    return {"ok": True}


# --- billing --------------------------------------------------------------
# Thin wrappers around app/billing.py's plain functions -- the actual Stripe
# calls live there once, shared with the /v1 partner route. This is what
# lets the Settings billing tab's buttons call something real instead of a
# PreviewInfo popup.


@router.post("/billing/checkout")
def billing_checkout(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return billing.start_checkout(session, account)


@router.post("/billing/portal")
def billing_portal(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    return billing.start_portal(session, account)
