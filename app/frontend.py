"""Every page route. Thin on purpose: resolve the workspace, call `pages`,
render the template.

This router replaces the page half of `dashboard.py` and `public.py`, whose
templates were archived when the frontend was rebuilt. The `/v1` API and the
billing router are untouched and still mounted.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import config, pages
from app.db import get_session
from app.models import Site

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(config.ROOT / "templates"))


def _site(session: Session, account, site_id: str | None) -> Site | None:
    """The project the page is about: the one asked for, else the first."""
    owned = pages.sites_of(session, account)
    if site_id:
        for s in owned:
            if s.id == site_id:
                return s
    return owned[0] if owned else None


def _render(request: Request, name: str, ctx: dict):
    ctx["request"] = request
    return templates.TemplateResponse(name, ctx)


# --- marketing -----------------------------------------------------------


@router.get("/")
def home(request: Request):
    return _render(request, "site/home.html", {"nav": "home"})


@router.get("/pricing")
def pricing(request: Request):
    return _render(request, "site/pricing.html", {"nav": "pricing"})


@router.get("/signin")
def signin(request: Request):
    return _render(request, "site/signin.html", {"nav": "signin"})


@router.get("/signup")
def signup(request: Request):
    return _render(request, "site/signup.html", {"nav": "signup"})


@router.get("/demo")
def demo():
    return RedirectResponse("/app", status_code=303)


# --- the app -------------------------------------------------------------


@router.get("/app")
def app_projects(request: Request, session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    return _render(request, "app/projects.html", pages.projects(session, account))


@router.get("/app/overview")
def app_overview(request: Request, site: str = "",
                 session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    ctx = pages.overview(session, account, _site(session, account, site))
    return _render(request, "app/overview.html", ctx)


@router.get("/app/seo")
def app_seo(request: Request, site: str = "", tab: str = "queue",
            session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    if tab not in ("queue", "review", "approved"):
        tab = "queue"
    ctx = pages.seo(session, account, _site(session, account, site), tab)
    return _render(request, "app/seo.html", ctx)


@router.get("/app/geo")
def app_geo(request: Request, site: str = "",
            session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    ctx = pages.geo(session, account, _site(session, account, site))
    return _render(request, "app/geo.html", ctx)


@router.get("/app/notifications")
def app_notifications(request: Request, session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    return _render(request, "app/notifications.html",
                   pages.notifications(session, account))


@router.get("/app/history")
def app_history(request: Request, session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    return _render(request, "app/history.html", pages.history(session, account))


@router.get("/app/settings")
def app_settings(request: Request, session: Session = Depends(get_session)):
    account = pages.resolve_account(session)
    return _render(request, "app/settings.html", pages.settings(session, account))
