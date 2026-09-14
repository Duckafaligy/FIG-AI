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
# Off by default. Turning it on pins every request to the seeded demo account
# with no sign-in -- useful for looking at the UI with data in it, and an open
# admin panel if it ever reaches a public URL.
DEV_NO_AUTH = os.environ.get("FIG_DEV_NO_AUTH", "0") == "1"
DEMO_ACCOUNT_SLUG = "northgate"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
# Safe to send to the browser: it is the key the Supabase JS client uses, and
# it carries no privileges of its own. The service-role key never leaves here.
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
AUTH_READY = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# The email that inherits the seeded account on first sign-in. Anyone else
# signing in gets an account of their own.
OWNER_EMAIL = os.environ.get("FIG_OWNER_EMAIL", "").strip().lower()

# Signs the session cookie. Generated per-process if unset, which means every
# restart signs everyone out -- fine locally, not fine in production.
SESSION_SECRET = os.environ.get("FIG_SESSION_SECRET", "")
SESSION_EPHEMERAL = not SESSION_SECRET
if not SESSION_SECRET:
    import secrets as _secrets
    SESSION_SECRET = _secrets.token_urlsafe(48)
SESSION_MAX_AGE = int(os.environ.get("FIG_SESSION_MAX_AGE", str(14 * 24 * 3600)))

# Where the marketing site is served from. The demo runs on that origin and
# calls this API cross-origin, so it has to be allowed explicitly.
SITE_ORIGINS = [o.strip() for o in os.environ.get(
    "FIG_SITE_ORIGINS",
    "http://127.0.0.1:8123,http://localhost:8123,https://fig-ai.vercel.app",
).split(",") if o.strip()]

# --- limits -----------------------------------------------------------
# The public read crawls real sites and calls Claude. Both cost something and
# neither should be freely loopable.
PUBLIC_SCANS_PER_DAY = int(os.environ.get("FIG_PUBLIC_SCANS_PER_DAY", "3"))
PUBLIC_SCANS_PER_HOUR_IP = int(os.environ.get("FIG_PUBLIC_SCANS_PER_HOUR_IP", "10"))
PUBLIC_SCAN_MAX_PAGES = int(os.environ.get("FIG_PUBLIC_SCAN_MAX_PAGES", "6"))

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
# Where the marketing site lives. The auth pages link back to it, and its
# origin is the one allowed to call this API from a browser.
MARKETING_URL = os.environ.get("FIG_MARKETING_URL", "http://127.0.0.1:8123")


# --- the frontend ---------------------------------------------------------
# The Next.js app in `frontend/` runs separately and calls this API across an
# origin, so its origin has to be allowed explicitly. Comma-separated for the
# cases where preview deploys need adding.
FRONTEND_URL = os.environ.get("FIG_FRONTEND_URL", "http://localhost:3001")
CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "FIG_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001",
    ).split(",") if o.strip()
]
