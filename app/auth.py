"""Who is asking.

Two independent paths, deliberately:

- **API keys** (`fig_live_…`) authenticate machines on `/v1`. A partner's
  server holds one. Only a SHA-256 is stored, so a database dump does not
  hand anyone working credentials; the plaintext is shown once at creation.

- **Supabase Auth** authenticates people on the dashboard. The browser signs
  in with the Supabase JS client and hands us the access token exactly once;
  we verify it against Supabase, then keep our own signed, HttpOnly session
  cookie. The access token itself is never stored and never goes near
  JavaScript on our pages.

`FIG_DEV_NO_AUTH=1` short-circuits the person half and resolves every request
to the demo account. It is the local convenience and the production footgun.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.db import get_session
from app.models import Account, ApiKey, User

log = logging.getLogger("fig.auth")

KEY_PREFIX = "fig_live"
SESSION_KEY = "uid"


# --- API keys -----------------------------------------------------------


def mint_key(session: Session, account: Account, label: str = "default") -> tuple[ApiKey, str]:
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(32)
    plaintext = f"{KEY_PREFIX}_{prefix}_{secret}"
    row = ApiKey(
        account_id=account.id,
        label=label,
        prefix=prefix,
        key_hash=hashlib.sha256(plaintext.encode()).hexdigest(),
    )
    session.add(row)
    session.flush()
    return row, plaintext


def _lookup(session: Session, plaintext: str) -> Account | None:
    parts = plaintext.split("_")
    if len(parts) < 4 or f"{parts[0]}_{parts[1]}" != KEY_PREFIX:
        return None
    digest = hashlib.sha256(plaintext.encode()).hexdigest()
    row = session.scalars(
        select(ApiKey).where(ApiKey.prefix == parts[2], ApiKey.revoked.is_(False))
    ).first()
    if row is None or not secrets.compare_digest(row.key_hash, digest):
        return None
    row.last_used_at = datetime.now(timezone.utc)
    session.commit()
    return session.get(Account, row.account_id)


def require_account(
    request: Request,
    session: Session = Depends(get_session),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Account:
    """API key first, then a dashboard session, then the dev bypass."""
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if token:
        account = _lookup(session, token)
        if account is None:
            raise HTTPException(401, "invalid API key")
        return account

    account = session_account(request, session)
    if account is not None:
        return account

    raise HTTPException(401, "missing API key")


# --- Supabase Auth ------------------------------------------------------


async def verify_access_token(access_token: str) -> dict:
    """Ask Supabase who this token belongs to.

    Checking with Supabase rather than verifying the JWT locally means there
    is no third copy of the signing secret to look after, and a token revoked
    upstream stops working here immediately. It costs one call, at sign-in
    only -- after that our own cookie carries the session.
    """
    if not config.AUTH_READY:
        raise HTTPException(503, "Supabase Auth is not configured")
    url = f"{config.SUPABASE_URL}/auth/v1/user"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={
            "Authorization": f"Bearer {access_token}",
            "apikey": config.SUPABASE_ANON_KEY,
        })
    if r.status_code != 200:
        raise HTTPException(401, "that sign-in could not be verified")
    user = r.json()
    if not user.get("id"):
        raise HTTPException(401, "that sign-in could not be verified")
    return user


def _slug_for(email: str, session: Session) -> str:
    base = "".join(c if c.isalnum() else "-" for c in email.split("@")[0].lower())
    base = base.strip("-") or "account"
    slug, n = base, 1
    while session.scalars(select(Account).where(Account.slug == slug)).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


def link_user(session: Session, supabase_user: dict,
               account_name: str | None = None) -> User:
    """Find or create our User row, and decide which Account it belongs to.

    A new person gets their own empty workspace, named by them at sign-up.
    Nobody lands inside somebody else's client list -- the only exception is
    FIG_OWNER_EMAIL, which adopts the seeded demo estate so it has an owner
    rather than floating unattached.
    """
    uid = supabase_user["id"]
    email = (supabase_user.get("email") or "").strip().lower()

    user = session.scalars(select(User).where(User.supabase_uid == uid)).first()
    if user is None and email:
        # Same person, previously seen by email (e.g. seeded before auth).
        user = session.scalars(select(User).where(User.email == email)).first()
        if user is not None:
            user.supabase_uid = uid

    if user is None:
        user = User(supabase_uid=uid, email=email or f"{uid}@unknown.local")
        session.add(user)
        session.flush()

    if user.account_id is None:
        account = None
        if config.OWNER_EMAIL and email == config.OWNER_EMAIL:
            account = session.scalars(
                select(Account).where(Account.slug == config.DEMO_ACCOUNT_SLUG)).first()
        if account is None:
            account = Account(
                name=(account_name or "").strip()[:80]
                     or (email.split("@")[0].title() if email else "New workspace"),
                slug=_slug_for(email or uid, session),
                kind="direct",
                contact_email=email or None,
                # The free week starts here, not at checkout: no card is
                # taken, so nothing can start billing without a decision.
                trial_ends_at=datetime.now(timezone.utc) + timedelta(
                    days=Account.TRIAL_DAYS),
            )
            session.add(account)
            session.flush()
            log.info("created account %s for %s", account.slug, email or uid)
        user.account_id = account.id

    session.commit()
    return user


EPOCH_KEY = "ep"


def start_session(request: Request, user: User) -> None:
    request.session[SESSION_KEY] = user.id
    request.session[EPOCH_KEY] = user.session_epoch or 0


def end_session(request: Request) -> None:
    request.session.pop(SESSION_KEY, None)


def session_user(request: Request, session: Session) -> User | None:
    """The signed-in person, or None. A session issued before their epoch was
    last bumped is dead: that is how a password reset ends every other device.
    Sessions from before epochs existed carry none and count as epoch 0, so
    deploying this signed nobody out."""
    uid = request.session.get(SESSION_KEY) if hasattr(request, "session") else None
    if not uid:
        return None
    user = session.get(User, uid)
    if user is None:
        return None
    if request.session.get(EPOCH_KEY, 0) != (user.session_epoch or 0):
        return None
    return user


def session_account(request: Request, session: Session) -> Account | None:
    user = session_user(request, session)
    if user is None or user.account_id is None:
        return None
    return session.get(Account, user.account_id)


# --- what the dashboard asks -------------------------------------------


def demo_account(session: Session) -> Account | None:
    return session.scalars(
        select(Account).where(Account.slug == config.DEMO_ACCOUNT_SLUG)).first()


def current_account(request: Request, session: Session) -> Account | None:
    """Whoever the dashboard is looking at, or None to send them to /login."""
    account = session_account(request, session)
    if account is not None:
        return account
    if config.DEV_NO_AUTH:
        return demo_account(session) or session.scalars(select(Account)).first()
    return None
