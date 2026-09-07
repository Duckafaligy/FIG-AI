"""Runtime settings.

Everything has a working default so the app boots and the dashboard is
visitable with nothing configured -- SQLite on disk, no auth, no Stripe.
Point DATABASE_URL at Supabase Postgres and the same code runs there.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

# --- database ---------------------------------------------------------
# Supabase gives a postgresql:// URL; psycopg2 is only needed when one is set.
# FIG_DATABASE_URL wins over DATABASE_URL so a local run can point somewhere
# else without touching the deployment value.
SQLITE_URL = f"sqlite:///{ROOT / 'fig.db'}"
DATABASE_URL = (os.environ.get("FIG_DATABASE_URL")
                or os.environ.get("DATABASE_URL")
                or SQLITE_URL)

# --- auth -------------------------------------------------------------
# While this is on, the dashboard opens straight onto the demo account with
# no sign-in. It is what makes the thing visitable today. Turn it off before
# anything is public.
DEV_NO_AUTH = os.environ.get("FIG_DEV_NO_AUTH", "1") == "1"
DEMO_ACCOUNT_SLUG = "northgate"

# --- crawling ---------------------------------------------------------
USER_AGENT = os.environ.get(
    "FIG_USER_AGENT",
    "FIGBot/0.2 (+https://fig.tools/bot; site self-check and structure scanner)",
)
REQUEST_TIMEOUT = int(os.environ.get("FIG_REQUEST_TIMEOUT", "12"))
# Politeness: one request per host at a time, spaced by this many seconds.
CRAWL_DELAY = float(os.environ.get("FIG_CRAWL_DELAY", "0.8"))
MAX_PAGES_PER_SCAN = int(os.environ.get("FIG_MAX_PAGES", "40"))
WORKER_COUNT = int(os.environ.get("FIG_WORKERS", "2"))

# A domain is only re-crawled this often on the free path (CLAUDE.md: the
# per-domain weekly cache). Paid re-scans bypass it.
DOMAIN_CACHE_HOURS = int(os.environ.get("FIG_DOMAIN_CACHE_HOURS", "168"))

# --- ai ---------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# ai_explain is the only LLM call in the pipeline. Without a key the whole
# scan still works; findings just carry their built-in explanation.
AI_EXPLAIN_ENABLED = bool(ANTHROPIC_API_KEY) and os.environ.get("FIG_AI_EXPLAIN", "1") == "1"

# --- billing ----------------------------------------------------------
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")   # per-site graduated price
BILLING_ENABLED = bool(STRIPE_SECRET_KEY)
PUBLIC_URL = os.environ.get("FIG_PUBLIC_URL", "http://127.0.0.1:8000")
