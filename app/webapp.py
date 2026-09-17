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

from app import config, content, pages, publishing
from app.auth import current_account, end_session, session_user, start_session
from app.db import get_session
from app.jobs import enqueue_estate, enqueue_scan, queue_depth
from app.models import Account, Site
from app.api import public_hostname

router = APIRouter(prefix="/api", tags=["workspace"])


# --- plumbing ------------------------------------------------------------


def _account(request: Request, session: Session) -> Account:
    account = current_account(request, session)
    if account is None:
        raise HTTPException(401, "sign in required")
    return account


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


# --- things the frontend needs to be able to do --------------------------


@router.post("/projects")
def add_project(request: Request, payload: dict = Body(...),
                session: Session = Depends(get_session)):
    """Add a project and immediately queue its first audit."""
    account = _account(request, session)
    raw = (payload or {}).get("hostname", "")
    if not raw:
        raise HTTPException(400, "a hostname is required")
    # Full validation (syntax + DNS resolves to a public address), not just
    # syntax -- this is a real user submitting an arbitrary hostname, same
    # trust level as the free /scan endpoint. The crawler re-checks on every
    # request regardless, but failing here means a clear 422 instead of a
    # Site row that can only ever produce a failed scan.
    host = public_hostname(raw)

    existing = next((s for s in pages.sites_of(session, account)
                     if s.hostname == host), None)
    if existing is not None:
        raise HTTPException(409, f"{host} is already in this workspace")

    site = Site(account_id=account.id, hostname=host,
                client_name=(payload or {}).get("name") or None,
                label=(payload or {}).get("label") or None)
    session.add(site)
    session.commit()
    session.refresh(site)

    scan = enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return {"id": site.id, "hostname": site.hostname, "scan_id": scan.id}


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
    return {"ok": True, "id": site.id, "billable_sites": account.billable_sites()}


@router.post("/projects/{project_id}/audit")
def audit_project(project_id: str, request: Request,
                  session: Session = Depends(get_session)):
    account = _account(request, session)
    site = _project(session, account, project_id)
    if site is None:
        raise HTTPException(404, "no such project")
    scan = enqueue_scan(session, site.id, trigger="manual")
    session.commit()
    return {"ok": True, "scan_id": scan.id, "queue": queue_depth(session)}


@router.post("/audit-all")
def audit_all(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
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
    if "body" in (payload or {}):
        post.body = (payload["body"] or "").strip() or None
    if "title" in (payload or {}) and payload["title"]:
        post.title = payload["title"].strip()
    if "keyword" in (payload or {}):
        post.target_keyword = (payload["keyword"] or "").strip().lower() or None
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
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "project": {"id": site.id, "hostname": site.hostname} if site else None,
        "next_action": content._next_action(post.state),
    }


# --- the change queue ----------------------------------------------------


@router.get("/changes")
def changes(request: Request, layer: str = Query(default=""),
            session: Session = Depends(get_session)):
    account = _account(request, session)
    return publishing.queue(session, account, layer=layer or None)


@router.post("/changes/propose")
def changes_propose(request: Request, session: Session = Depends(get_session)):
    account = _account(request, session)
    made = 0
    for site in pages.sites_of(session, account):
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
    see `publishing.connect`. Until a real secret store is wired up the
    integration stays unconnected and publishing refuses.
    """
    account = _account(request, session)
    p = payload or {}
    integration = publishing.connect(
        session, account, p.get("project_id", ""), p.get("platform", ""),
        p.get("endpoint", ""), p.get("credential", ""))
    return {"id": integration.id, "platform": integration.platform,
            "connected": integration.is_connected(),
            "hint": integration.credential_hint}


@router.post("/integrations/{integration_id}/disconnect")
def disconnect(integration_id: str, request: Request,
               session: Session = Depends(get_session)):
    account = _account(request, session)
    publishing.disconnect(session, account, integration_id)
    return {"ok": True}
