"""Keeping personal identifiers only as long as they are used.

A free scan stores two scrambled values next to its record: a hash of the IP
address and a hash of the IP plus a random device ID. They exist for the
per-hour and per-day scan limits (app/public.py), which only ever look back a
day. After that they identify nobody usefully and serve no purpose, so they are
blanked. The scan, its score and its library entry are untouched: those are the
public result, not the visitor.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.db import session_scope
from app.models import PublicRead

log = logging.getLogger("fig.retention")

IDENTIFIER_DAYS = 30
BLANK = ""          # the columns are NOT NULL, and "" can never match a real hash


def purge_identifiers(now: datetime | None = None, days: int = IDENTIFIER_DAYS) -> int:
    """Blank the hashed IP/device identifiers on reads older than `days`.
    Returns how many rows were changed; safe to run any number of times."""
    cutoff = (now or datetime.now(timezone.utc)).replace(tzinfo=None) - timedelta(days=days)
    with session_scope() as s:
        rows = s.query(PublicRead).filter(
            PublicRead.created_at < cutoff,
            (PublicRead.device_hash != BLANK) | (PublicRead.ip_hash != BLANK),
        )
        changed = rows.update({PublicRead.device_hash: BLANK, PublicRead.ip_hash: BLANK},
                              synchronize_session=False)
    if changed:
        log.info("blanked hashed identifiers on %d free reads older than %d days", changed, days)
    return changed
