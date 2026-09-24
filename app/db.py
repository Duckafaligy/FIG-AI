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

from sqlalchemy import create_engine, event, inspect, select, text
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

# Constraints declared on the ORM model (app/models.py's __table_args__) but
# never applied to the one already-deployed database, for the same reason as
# the two migrations above -- create_all() never alters an existing table.
# Without this, nothing at the database level stops two concurrent/retried
# /oauth/google/callback requests from creating two account_id-scoped rows
# for the same (account, platform); a plain UNIQUE constraint is correct
# here even though account_id is nullable -- Postgres treats each NULL as
# distinct, so the many legitimate site_id-scoped rows (account_id NULL)
# never collide with each other under it.
_ADDED_UNIQUE_CONSTRAINTS = (
    ("integrations", "uq_integration_account_platform", ("account_id", "platform")),
)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _add_missing_columns()
    _relax_not_null_columns()
    _add_missing_unique_constraints()
    _migrate_site_scoped_google_integrations()


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


def _add_missing_unique_constraints() -> None:
    if engine.dialect.name != "postgresql":
        return          # SQLite: every test/local db is created fresh from the current model
    inspector = inspect(engine)
    for table, name, columns in _ADDED_UNIQUE_CONSTRAINTS:
        if not inspector.has_table(table):
            continue
        existing = {c["name"] for c in inspector.get_unique_constraints(table)}
        if name in existing:
            continue
        col_list = ", ".join(columns)
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD CONSTRAINT {name} UNIQUE ({col_list})"))
        log.info("added unique constraint %s on %s(%s)", name, table, col_list)


def _migrate_site_scoped_google_integrations() -> None:
    """Data migration, not schema (2026-09-23): Google Analytics/Search
    Console moved from site_id-scoped to account_id-scoped Integration rows
    (see Integration's docstring in app/models.py). Without this, an account
    that connected Google before this deploy keeps a live refresh token in a
    row the new account_id-scoped lookup in app/ga.py and
    app/search_console.py can never find again -- silently orphaned, not
    merely stale. Idempotent: once no site-scoped Google row remains, every
    later boot's query returns nothing and this is a no-op.

    An account can have several such rows (the old model let every project
    connect Google separately) -- the most recently connected one is
    promoted in place to the account-scoped row; the rest, and their stored
    secrets, are removed the same way disconnect() removes any other
    integration. If an account-scoped row already exists (a real reconnect
    already happened since deploy), the old rows are superseded, not merged
    -- all of them are removed rather than guessing which is authoritative.
    """
    from datetime import datetime

    from app.models import Integration, Site
    from app.secrets_store import SecretsNotConfigured, delete_secret

    with session_scope() as session:
        rows = list(session.scalars(
            select(Integration).where(
                Integration.site_id.isnot(None),
                Integration.platform.in_(("google_analytics", "google_search_console")),
            )
        ).all())
        if not rows:
            return

        site_ids = {r.site_id for r in rows}
        sites = {s.id: s for s in session.scalars(
            select(Site).where(Site.id.in_(site_ids))).all()}

        groups: dict[tuple[str, str], list[Integration]] = {}
        for row in rows:
            site = sites.get(row.site_id)
            if site is None:
                # The site itself is gone; nothing left to scope this to.
                session.delete(row)
                continue
            groups.setdefault((site.account_id, row.platform), []).append(row)

        def _drop(integ: Integration, account_id: str, why: str) -> None:
            if integ.credential_ref:
                try:
                    delete_secret(session, integ.credential_ref)
                except SecretsNotConfigured:
                    pass
            session.delete(integ)
            log.info("google integration migration: removed %s integration %s for account %s (%s)",
                     integ.platform, integ.id, account_id, why)

        for (account_id, platform), group in groups.items():
            already = session.scalars(select(Integration).where(
                Integration.account_id == account_id, Integration.platform == platform)).first()
            if already is not None:
                for row in group:
                    _drop(row, account_id, "account-scoped row already exists")
                continue
            group.sort(key=lambda r: r.connected_at or datetime.min, reverse=True)
            winner, *losers = group
            winner.site_id = None
            winner.account_id = account_id
            log.info("google integration migration: promoted %s integration %s to account-scoped for account %s",
                     platform, winner.id, account_id)
            for row in losers:
                _drop(row, account_id, "superseded by a more recently connected row")


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
