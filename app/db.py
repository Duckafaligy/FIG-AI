"""Database session handling.

SQLAlchemy against DATABASE_URL. Point it at the Supabase Postgres string and
this runs there; with nothing configured it is a local SQLite file, which is
what lets the dashboard be opened with no setup.

If a Postgres URL is set but unreachable — no network, laptop offline, wrong
password — the engine falls back to SQLite and says so loudly rather than
refusing to start. Set FIG_DB_STRICT=1 to make that an error instead.

The Supabase client is kept separately for Auth, which is not wired up yet.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL, SQLITE_URL
from app.models import Base

log = logging.getLogger("fig.db")

_STRICT = os.environ.get("FIG_DB_STRICT", "0") == "1"


def _build(url: str):
    sqlite = url.startswith("sqlite")
    eng = create_engine(
        url,
        future=True,
        pool_pre_ping=not sqlite,
        # Worker threads and request handlers share one SQLite file.
        connect_args={"check_same_thread": False, "timeout": 30} if sqlite else {},
    )
    if sqlite:
        @event.listens_for(eng, "connect")
        def _pragmas(dbapi_conn, _record):
            # WAL lets a worker write while a request reads, which is what
            # allows a scan to run while the dashboard is being refreshed.
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
    return eng


def _reachable(eng) -> bool:
    try:
        with eng.connect() as c:
            c.execute(text("select 1"))
        return True
    except Exception as exc:                        # noqa: BLE001
        log.warning("database %s unreachable: %s",
                    eng.url.render_as_string(hide_password=True), exc)
        return False


engine = _build(DATABASE_URL)

if not DATABASE_URL.startswith("sqlite") and not _reachable(engine):
    if _STRICT:
        # render_as_string hides the password; the raw URL must never
        # reach a log line or a traceback.
        raise RuntimeError(
            f"cannot reach {engine.url.render_as_string(hide_password=True)}"
            " and FIG_DB_STRICT=1")
    log.warning("falling back to %s (set FIG_DATABASE_URL to override)", SQLITE_URL)
    engine = _build(SQLITE_URL)

IS_SQLITE = engine.url.get_backend_name() == "sqlite"

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False,
                            future=True, class_=Session)


# Columns added to a table that already exists in a deployed database.
# create_all only ever creates missing tables -- it never alters one -- so an
# additive, nullable column has to be added here. Idempotent.
_ADDED_COLUMNS = (
    ("sites", "ga_property", "VARCHAR"),
    ("scans", "trace", "JSON"),
    ("sites", "reports_public", "BOOLEAN DEFAULT FALSE"),
    ("users", "session_epoch", "INTEGER NOT NULL DEFAULT 0"),
    ("pages", "js_dependent", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("pages", "js_dependent_reason", "VARCHAR"),
    ("integrations", "account_id", "VARCHAR"),
)

# Column-nullability changes, run after _add_missing_columns() so the column
# exists first. SQLite has no ALTER COLUMN at all (no-op, harmless -- a
# database created from today's model already has the right nullability,
# and every test starts from a fresh create_all()); Postgres runs this for
# real, idempotently, against the one already-deployed database that
# predates account_id-scoped integrations (2026-09-23: Google Analytics/
# Search Console moved from site_id-scoped to account_id-scoped, so
# integrations.site_id can no longer be NOT NULL).
_RELAXED_NOT_NULL = (
    ("integrations", "site_id"),
)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _add_missing_columns()
    _relax_not_null_columns()


def _add_missing_columns() -> None:
    inspector = inspect(engine)
    for table, column, sql_type in _ADDED_COLUMNS:
        if not inspector.has_table(table):
            continue
        if column in {c["name"] for c in inspector.get_columns(table)}:
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
        log.info("added column %s.%s", table, column)


def _relax_not_null_columns() -> None:
    if engine.dialect.name != "postgresql":
        return
    inspector = inspect(engine)
    for table, column in _RELAXED_NOT_NULL:
        if not inspector.has_table(table):
            continue
        columns = {c["name"]: c for c in inspector.get_columns(table)}
        if column not in columns or columns[column]["nullable"]:
            continue
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"))
        log.info("relaxed NOT NULL on %s.%s", table, column)


@contextmanager
def session_scope():
    """Commit on success, roll back on error, always close."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_session():
    """FastAPI dependency."""
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


# --- Supabase (Auth only, not yet wired up) ----------------------------

_sb = None


def get_supabase():
    global _sb
    if _sb is None:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _sb = create_client(url, key)
    return _sb
