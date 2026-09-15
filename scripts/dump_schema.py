"""Prints the Postgres DDL for the current models.

    python scripts/dump_schema.py > supabase_schema.sql

Nothing needs this to run -- app.db.init_db() creates tables on boot. It
exists so the checked-in schema file can be regenerated instead of drifting.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects import postgresql          # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

from app.models import Base                          # noqa: E402

d = postgresql.dialect()
print(
    "-- FIG schema. Generated from app/models.py -- regenerate rather than\n"
    "-- hand-editing, or the two drift apart.\n"
    "--\n"
    "-- You do not need to run this: app.db.init_db() calls create_all() on boot,\n"
    "-- against whatever DATABASE_URL points at, then adds any column listed in\n"
    "-- app/db.py:_ADDED_COLUMNS to tables that already existed. This file is\n"
    "-- here for review, and for running by hand in the Supabase SQL editor.\n"
    "--\n"
    "--   python scripts/dump_schema.py > supabase_schema.sql\n"
)
for t in Base.metadata.sorted_tables:
    print(str(CreateTable(t).compile(dialect=d)).strip()
          .replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1) + ";\n")
    for ix in t.indexes:
        s = str(CreateIndex(ix).compile(dialect=d)).strip()
        print(s.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS", 1)
               .replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS", 1) + ";\n")
