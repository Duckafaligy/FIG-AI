"""Remove leftover test data from the database FIG is pointed at.

    python scripts/cleanup_test_data.py            # dry run: says what it WOULD delete
    python scripts/cleanup_test_data.py --apply    # actually deletes it

Written as a script (not a one-off) so the deletion can be read before it runs,
and so it only ever touches a fixed, named list of leftovers:

  * accounts named in JUNK (created by old test scripts and disposable sign-ups),
    but only if they have no subscription and every user in them is a
    disposable `fig-*@example.com` address;
  * the two `127.0.0.1:8123` free-scan rows (and their site) from before URL
    validation existed, which still sit on the public /library page;
  * the Supabase sign-in records of those disposable users, if they still exist.

It never touches "Northgate Digital" (the seeded demo), real accounts, or anything
not listed here, and it asserts the guards above before each deletion. It uses
the same DATABASE_URL as the backend, so check which database that is first: the
first line it prints says.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv                                    # noqa: E402

load_dotenv(ROOT / ".env")

import requests                                                   # noqa: E402
from sqlalchemy import func, select                               # noqa: E402

from app import config                                            # noqa: E402
from app.db import engine, session_scope                          # noqa: E402
from app.models import (Account, Change, ContentPost, Integration, Job,   # noqa: E402
                        PublicRead, Scan, Site, User)
from app.secrets_store import delete_secret                       # noqa: E402

JUNK = {"My Workspace", "FIG test runs", "Debug Co", "Perf Co", "GSC Co", "Stripe Test Co"}
STALE_HOST = "127.0.0.1:8123"
APPLY = "--apply" in sys.argv


def say(msg: str) -> None:
    print(("DELETE  " if APPLY else "would delete  ") + msg)


def purge_site(db, site: Site) -> int:
    site_ids = [site.id]
    scan_ids = [x for (x,) in db.execute(select(Scan.id).where(Scan.site_id == site.id))]
    for integ in db.scalars(select(Integration).where(Integration.site_id == site.id)):
        if integ.credential_ref:
            delete_secret(db, integ.credential_ref)
    for model in (ContentPost, Change, Integration):
        db.query(model).filter(model.site_id.in_(site_ids)).delete(synchronize_session=False)
    if scan_ids:
        db.query(PublicRead).filter(PublicRead.scan_id.in_(scan_ids)).delete(synchronize_session=False)
        for job in db.scalars(select(Job).where(Job.created_at.is_not(None))):
            if any(i in str(job.payload) for i in scan_ids):
                db.delete(job)
    db.flush()
    db.delete(site)
    return len(scan_ids)


def main() -> int:
    print(f"database: {engine.url.render_as_string(hide_password=True)}")
    from sqlalchemy import inspect
    columns = {c["name"] for c in inspect(engine).get_columns("users")}
    if "session_epoch" not in columns:
        print()
        print("The users table is missing the session_epoch column. The backend adds it itself on "
              "startup, so deploy the latest code first (or start it once), then run this again.")
        return 2
    print("mode:", "APPLY (will delete)" if APPLY else "dry run (nothing is changed)")
    removed_emails: list[str] = []

    with session_scope() as db:
        # 1. the stale localhost library rows and their site
        rows = list(db.scalars(select(PublicRead).where(PublicRead.hostname == STALE_HOST)))
        sites = list(db.scalars(select(Site).where(Site.hostname == STALE_HOST)))
        say(f"{len(rows)} public library row(s) for {STALE_HOST}")
        say(f"{len(sites)} site row(s) for {STALE_HOST}")
        if APPLY:
            for row in rows:
                db.delete(row)
            db.flush()
            for site in sites:
                assert db.get(Account, site.account_id).slug == config.DEMO_ACCOUNT_SLUG
                purge_site(db, site)

        # 2. junk accounts
        for account in list(db.scalars(select(Account).where(Account.name.in_(JUNK)))):
            assert account.slug != config.DEMO_ACCOUNT_SLUG, account.name
            assert not account.stripe_subscription_id, f"{account.name} has a subscription"
            users = list(db.scalars(select(User).where(User.account_id == account.id)))
            assert all(u.email.startswith("fig-") and u.email.endswith("@example.com") for u in users), \
                f"{account.name} has a non-disposable user: {[u.email for u in users]}"
            acct_sites = list(db.scalars(select(Site).where(Site.account_id == account.id)))
            say(f"account {account.name!r}: {len(users)} user(s), {len(acct_sites)} site(s)")
            removed_emails += [u.email for u in users]
            if APPLY:
                for site in acct_sites:
                    purge_site(db, site)
                for user in users:
                    db.delete(user)
                db.flush()
                db.delete(account)

    # 3. their sign-in records at Supabase
    if removed_emails and config.SUPABASE_URL and config.SUPABASE_SERVICE_ROLE_KEY:
        headers = {"apikey": config.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}"}
        listing = requests.get(f"{config.SUPABASE_URL}/auth/v1/admin/users", headers=headers, params={"per_page": 1000}, timeout=30).json()
        for u in listing.get("users", []):
            if u.get("email") in removed_emails:
                say(f"Supabase sign-in record {u['email']}")
                if APPLY:
                    requests.delete(f"{config.SUPABASE_URL}/auth/v1/admin/users/{u['id']}", headers=headers, timeout=30)

    with session_scope() as db:
        left = [a.name for a in db.scalars(select(Account).order_by(Account.created_at))]
    print("accounts", "now" if APPLY else "after", ":", left if APPLY else [n for n in left if n not in JUNK])
    if not APPLY:
        print("\nNothing was changed. Re-run with --apply to delete the above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
