"""Minimal encrypted-at-rest storage for OAuth tokens and CMS credentials —
the piece CLAUDE.md's roadmap calls out as the real blocker on any
write-capable integration (#4b). `Integration.credential_ref` holds a
`Secret` row's id; the Integration row itself never carries anything usable
on its own.

Not a KMS or vault: one symmetric key (`FIG_SECRET_KEY`, Fernet) encrypts
every value. That stops a database dump from handing over live tokens, which
is the immediate risk; swap this for an actual secret manager before this is
fronting real customer CMS credentials at any scale.
"""
from __future__ import annotations

import json

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app import config
from app.models import Secret


class SecretsNotConfigured(Exception):
    """FIG_SECRET_KEY is unset, or a stored secret can't be read with the
    key currently configured (it was encrypted under a different one)."""


def _fernet() -> Fernet:
    if not config.SECRET_ENCRYPTION_KEY:
        raise SecretsNotConfigured(
            "FIG_SECRET_KEY is not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\" and put it in .env — "
            "never commit it.")
    return Fernet(config.SECRET_ENCRYPTION_KEY.encode())


def store_secret(session: Session, value: dict) -> str:
    """Encrypts `value` and inserts a new Secret row. Returns its id for
    `Integration.credential_ref`. Caller commits — this only flushes, so it
    can be part of the same transaction that writes the Integration row."""
    token = _fernet().encrypt(json.dumps(value).encode())
    row = Secret(ciphertext=token.decode())
    session.add(row)
    session.flush()
    return row.id


def read_secret(session: Session, ref: str) -> dict:
    row = session.get(Secret, ref)
    if row is None:
        raise KeyError(f"no secret {ref}")
    try:
        return json.loads(_fernet().decrypt(row.ciphertext.encode()))
    except InvalidToken as exc:
        raise SecretsNotConfigured(
            f"secret {ref} can't be decrypted with the current FIG_SECRET_KEY "
            "(wrong key, or it rotated)") from exc


def update_secret(session: Session, ref: str, value: dict) -> None:
    row = session.get(Secret, ref)
    if row is None:
        raise KeyError(f"no secret {ref}")
    row.ciphertext = _fernet().encrypt(json.dumps(value).encode()).decode()


def delete_secret(session: Session, ref: str) -> None:
    row = session.get(Secret, ref)
    if row is not None:
        session.delete(row)
