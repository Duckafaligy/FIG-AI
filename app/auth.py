"""API key issue and check.

Keys look like `fig_live_<prefix>_<secret>`. Only a SHA-256 of the whole key
is stored, so a database dump does not hand anyone working credentials; the
plaintext is returned exactly once, at creation.

Supabase Auth for the dashboard is still to come — until it is, DEV_NO_AUTH
resolves every dashboard request to the demo account.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DEMO_ACCOUNT_SLUG, DEV_NO_AUTH
from app.db import get_session
from app.models import Account, ApiKey

KEY_PREFIX = "fig_live"


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
    session: Session = Depends(get_session),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Account:
    """Bearer token or X-API-Key. Partners tend to prefer the header."""
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token:
        if DEV_NO_AUTH:
            account = demo_account(session)
            if account:
                return account
        raise HTTPException(401, "missing API key")

    account = _lookup(session, token)
    if account is None:
        raise HTTPException(401, "invalid API key")
    return account


def demo_account(session: Session) -> Account | None:
    return session.scalars(
        select(Account).where(Account.slug == DEMO_ACCOUNT_SLUG)
    ).first()


def current_account(session: Session) -> Account | None:
    """Whoever the dashboard is looking at. While DEV_NO_AUTH is on that is
    always the demo account — this is the single line that changes when
    Supabase Auth goes in."""
    if DEV_NO_AUTH:
        return demo_account(session) or session.scalars(select(Account)).first()
    return None
