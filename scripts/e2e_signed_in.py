"""Signed-in end-to-end test against a DEPLOYED FIG.

    python scripts/e2e_signed_in.py                      # the live Vercel proxy
    python scripts/e2e_signed_in.py https://other.host   # any deployment

It exists because "the health endpoint is green" and "the tests pass" have both
been true while something a signed-in person actually does was broken. This
walks the real path through the real proxy, exactly as a browser does:

  * everything is 401 while signed out, and a forged token or cookie gets nowhere
  * sign in -> create a project -> create, edit, review and schedule a post
  * publishing and AI drafting refuse cleanly (they are deliberately not built)
  * a SECOND user cannot read, edit, move, share, audit or delete the first
    user's project or posts
  * logout really ends the session

It makes two disposable Supabase users and one project (example.com, or
neverssl.com where that does not resolve; one tiny real scan). Everything it made is deleted afterwards, scoped by
the accounts it created, and never anything else. A real account is never used.

It does not exercise billing: a checkout here would be real money in live mode.
Session expiry is also not covered (14 days; needs a clock, not a request).
"""
from __future__ import annotations

import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv                                    # noqa: E402

load_dotenv(ROOT / ".env")

import os                                                         # noqa: E402

import requests                                                   # noqa: E402

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://fig-ai-seven.vercel.app").rstrip("/")
SUPA = os.environ["SUPABASE_URL"].rstrip("/")
ANON = os.environ["SUPABASE_ANON_KEY"]
SERVICE = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TAG = secrets.token_hex(4)
TIMEOUT = 90          # Render's free tier may need to wake


def _pick_host() -> str:
    """A tiny public site to add as a project. example.com is the first choice;
    some resolvers refuse it, so fall back rather than fail on the network."""
    import socket
    for host in ("example.com", "neverssl.com"):
        try:
            socket.getaddrinfo(host, 443)
            return host
        except OSError:
            continue
    return "neverssl.com"


HOST = _pick_host()

results: list[tuple[str, bool, str]] = []
notes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not ok else ""))
    return bool(ok)


def note(text: str) -> None:
    notes.append(text)
    print(f"  [NOTE] {text}")


class Client:
    """A browser: one cookie jar, talking to the deployed site."""

    def __init__(self) -> None:
        self.s = requests.Session()

    def call(self, method: str, path: str, **kw) -> requests.Response:
        return self.s.request(method, BASE + path, timeout=TIMEOUT, **kw)


def supa_headers(key: str) -> dict:
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def make_user(label: str) -> dict:
    email = f"fig-e2e-{TAG}-{label}@example.com"
    password = secrets.token_urlsafe(18)
    r = requests.post(f"{SUPA}/auth/v1/admin/users", headers=supa_headers(SERVICE),
                      json={"email": email, "password": password, "email_confirm": True},
                      timeout=30)
    r.raise_for_status()
    uid = r.json()["id"]
    t = requests.post(f"{SUPA}/auth/v1/token?grant_type=password", headers={"apikey": ANON},
                      json={"email": email, "password": password}, timeout=30)
    t.raise_for_status()
    return {"email": email, "uid": uid, "password": password, "token": t.json()["access_token"], "client": Client()}


def cleanup(users: list[dict]) -> None:
    """Delete what this run made. Scoped by the e2e accounts, nothing wider."""
    print("\ncleanup")
    from sqlalchemy import select

    from app.db import session_scope
    from app.models import (Account, Change, ContentPost, Integration, Job,
                            PublicRead, Scan, Site, User)

    emails = [u["email"] for u in users if u]
    assert all(e.startswith("fig-e2e-") and e.endswith("@example.com") for e in emails)
    try:
        with session_scope() as db:
            accounts = list(db.scalars(select(Account).where(Account.contact_email.in_(emails))))
            acc_ids = [a.id for a in accounts]
            sites = list(db.scalars(select(Site).where(Site.account_id.in_(acc_ids)))) if acc_ids else []
            site_ids = [s.id for s in sites]
            scan_ids = [x.id for x in db.scalars(select(Scan).where(Scan.site_id.in_(site_ids)))] if site_ids else []
            if site_ids:
                for model in (ContentPost, Change, Integration):
                    for row in db.scalars(select(model).where(model.site_id.in_(site_ids))):
                        db.delete(row)
            if scan_ids:
                for row in db.scalars(select(PublicRead).where(PublicRead.scan_id.in_(scan_ids))):
                    db.delete(row)
            recent = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
            for job in db.scalars(select(Job).where(Job.created_at >= recent)):
                blob = str(job.payload)
                if any(i in blob for i in site_ids + scan_ids):
                    db.delete(job)
            db.flush()
            # Users point at accounts, so they go first.
            for row in db.scalars(select(User).where(User.email.in_(emails))):
                db.delete(row)
            db.flush()
            for a in accounts:
                db.delete(a)          # cascades to sites, scans, pages, findings, keys
        print(f"  database: removed {len(accounts)} accounts, {len(site_ids)} sites")
    except Exception as exc:                                       # noqa: BLE001
        print(f"  database cleanup FAILED, leftovers named fig-e2e-{TAG}-*: {exc}")
    for u in users:
        if not u or not u.get("uid"):
            continue
        r = requests.delete(f"{SUPA}/auth/v1/admin/users/{u['uid']}",
                            headers=supa_headers(SERVICE), timeout=30)
        print(f"  supabase user {u['email']}: {r.status_code}")


def main() -> int:
    print(f"E2E against {BASE}   run {TAG}\n")
    a = b = None
    try:
        a = make_user("a")
        b = make_user("b")
        A, B = a["client"], b["client"]

        print("1. signed out")
        for path in ("/api/projects", "/api/overview", "/api/seo", "/api/geo",
                     "/api/notifications", "/api/history", "/api/settings",
                     "/api/content", "/api/changes"):
            r = Client().call("GET", path)
            check(f"GET {path} is 401", r.status_code == 401, str(r.status_code))
        for path, body in (("/api/content", {"title": "x", "project_id": "x"}),
                           ("/api/projects", {"hostname": HOST}),
                           ("/api/billing/checkout", {}),
                           ("/api/audit-all", {})):
            r = Client().call("POST", path, json=body)
            check(f"POST {path} is 401", r.status_code == 401, str(r.status_code))
        r = Client().call("GET", "/api/me")
        check("/api/me says signed_in false", r.status_code == 200 and r.json().get("signed_in") is False)
        r = Client().call("POST", "/api/session", json={"access_token": "not-a-real-token"})
        check("a forged token does not create a session", r.status_code in (401, 422), str(r.status_code))
        forged = Client()
        forged.s.cookies.set("fig_session", "forged.value.here")
        check("a forged session cookie gets nowhere",
              forged.call("GET", "/api/me").json().get("signed_in") is False)

        print("\n2. sign in as A")
        r = A.call("POST", "/api/session", json={"access_token": a["token"], "workspace_name": "E2E A"})
        check("POST /api/session accepts a real token", r.status_code == 200, r.text[:120])
        me = A.call("GET", "/api/me").json()
        check("session survives the next request", me.get("signed_in") is True, str(me)[:120])
        check("A got their own empty workspace", me.get("account", {}).get("projects") == 0, str(me.get("account")))
        check("workspace name came from sign-up", me.get("account", {}).get("name") == "E2E A")

        print("\n3. projects")
        r = A.call("POST", "/api/projects", json={"hostname": HOST, "name": "E2E project"})
        ok = check("A can add a project", r.status_code == 200 and "id" in r.json(), r.text[:160])
        project = r.json() if ok else {}
        pid = project.get("id", "")
        check("same hostname again is 409", A.call("POST", "/api/projects", json={"hostname": HOST}).status_code == 409)
        for bad in ("localhost", "10.0.0.1", "http://169.254.169.254"):
            r = A.call("POST", "/api/projects", json={"hostname": bad})
            check(f"unsafe hostname {bad!r} is refused", r.status_code in (400, 422), str(r.status_code))
        r = A.call("GET", "/api/projects")
        check("project shows up in A's list", r.status_code == 200 and HOST in r.text)

        print("\n4. content: create, edit, review, schedule, refuse to publish")
        r = A.call("POST", "/api/content", json={"project_id": pid, "title": "E2E draft post",
                                                 "keyword": "e2e keyword"})
        ok = check("A can create a post", r.status_code == 200 and r.json().get("state") == "queued", r.text[:160])
        post = r.json() if ok else {}
        post_id = post.get("id", "")
        r = A.call("POST", "/api/content", json={"project_id": pid, "title": "   "})
        check("a blank title is refused", r.status_code == 422, str(r.status_code))
        body = ("Choosing an e2e keyword is easier when the page answers the question "
                "first. " * 12)
        r = A.call("PATCH", f"/api/content/{post_id}", json={"body": body})
        check("saving a draft scores it", r.status_code == 200 and r.json().get("word_count", 0) > 50
              and r.json().get("seo_score") is not None, r.text[:160])
        check("draft persists across requests",
              A.call("GET", f"/api/content/{post_id}").json().get("body", "").startswith("Choosing"))
        r = A.call("POST", f"/api/content/{post_id}/move", json={"to": "in_progress"})
        check("queued -> in_progress", r.status_code == 200 and r.json()["state"] == "in_progress", r.text[:120])
        r = A.call("POST", f"/api/content/{post_id}/move", json={"to": "review"})
        check("in_progress -> review", r.status_code == 200 and r.json()["state"] == "review", r.text[:120])
        r = A.call("POST", f"/api/content/{post_id}/move", json={"to": "scheduled"})
        check("review -> scheduled sets a date", r.status_code == 200 and r.json().get("scheduled_for"), r.text[:120])
        r = A.call("POST", f"/api/content/{post_id}/move", json={"to": "published"})
        check("scheduled -> published refuses (no CMS push exists)", r.status_code == 409, str(r.status_code))
        check("...and the post is still scheduled",
              A.call("GET", f"/api/content/{post_id}").json().get("state") == "scheduled")
        r = A.call("POST", f"/api/content/{post_id}/draft")
        check("AI drafting refuses out loud", r.status_code == 501, str(r.status_code))
        r = A.call("POST", "/api/content", json={"project_id": pid, "title": "E2E empty brief"})
        empty = r.json().get("id", "")
        A.call("POST", f"/api/content/{empty}/move", json={"to": "in_progress"})
        r = A.call("POST", f"/api/content/{empty}/move", json={"to": "review"})
        check("a post with no draft cannot go to review", r.status_code == 409, str(r.status_code))
        r = A.call("POST", f"/api/content/{empty}/move", json={"to": "scheduled"})
        check("review cannot be skipped (in_progress -> scheduled)", r.status_code == 409, str(r.status_code))
        r = A.call("GET", "/api/content?state=scheduled")
        check("library filters by status", r.status_code == 200 and r.json()["total"] == 1, r.text[:120])
        check("bad status filter is 422", A.call("GET", "/api/content?state=bogus").status_code == 422)
        check("limit is bounded", A.call("GET", "/api/content?limit=1000").status_code == 422)
        r = A.call("GET", "/api/content?q=" + "x" * 300)
        check("oversized search is bounded", r.status_code == 422, str(r.status_code))
        r = A.call("PATCH", f"/api/content/{post_id}", json={"body": body + " Edited after scheduling."})
        check("editing approved text sends it back to review",
              r.status_code == 200 and r.json().get("state") == "review" and not r.json().get("scheduled_for"),
              r.text[:160])

        print("\n5. B cannot touch A's work")
        r = B.call("POST", "/api/session", json={"access_token": b["token"], "workspace_name": "E2E B"})
        check("B signs in", r.status_code == 200)
        check("B sees no posts", B.call("GET", "/api/content").json().get("total") == 0)
        check("B's project list does not include A's", HOST not in B.call("GET", "/api/projects").text)
        r = B.call("GET", f"/api/content/{post_id}")
        check("B cannot read A's post", r.status_code == 404 and "E2E draft" not in r.text, str(r.status_code))
        other = r.text
        r = B.call("GET", "/api/content/00000000-0000-0000-0000-000000000000")
        check("someone else's post looks the same as a missing one", other == r.text,
              f"{other[:80]!r} vs {r.text[:80]!r}")
        r = B.call("PATCH", f"/api/content/{post_id}", json={"body": "hijacked"})
        check("B cannot edit A's post", r.status_code == 404, str(r.status_code))
        r = B.call("POST", f"/api/content/{post_id}/move", json={"to": "review"})
        check("B cannot move A's post", r.status_code == 409, str(r.status_code))
        r = B.call("POST", "/api/content", json={"project_id": pid, "title": "planted"})
        check("B cannot create posts on A's project", r.status_code == 422, str(r.status_code))
        check("B cannot filter the library to A's project", B.call("GET", f"/api/content?project={pid}").status_code == 404)
        check("B cannot delete A's project", B.call("DELETE", f"/api/projects/{pid}").status_code == 404)
        check("B cannot audit A's project", B.call("POST", f"/api/projects/{pid}/audit").status_code == 404)
        check("B cannot publish A's report", B.call("POST", f"/api/projects/{pid}/share", json={"public": True}).status_code == 404)
        check("A's post is untouched", A.call("GET", f"/api/content/{post_id}").json().get("body", "").find("hijacked") == -1)
        check("A's report was not made public by B's attempt", "\"public\": true" not in A.call("GET", "/api/settings").text.lower())

        print("\n6. logout")
        check("logout returns ok", A.call("POST", "/api/logout").status_code == 200)
        check("session is gone after logout", A.call("GET", "/api/me").json().get("signed_in") is False)
        check("protected route is 401 again", A.call("GET", "/api/content").status_code == 401)
        check("B is still signed in (sessions are separate)", B.call("GET", "/api/me").json().get("signed_in") is True)

        print("\n7. rename, ending sessions after a reset, deleting an account")
        A.call("POST", "/api/session", json={"access_token": a["token"]})            # A signs back in after section 6
        r = A.call("PATCH", "/api/settings/profile", json={"name": "E2E A renamed"})
        check("A can rename the workspace", r.status_code == 200 and r.json().get("profile", {}).get("name") == "E2E A renamed", r.text[:120])
        check("a blank name is refused", A.call("PATCH", "/api/settings/profile", json={"name": "  "}).status_code == 422)
        check("...and B's name is untouched", B.call("GET", "/api/me").json().get("account", {}).get("name") == "E2E B")

        A2 = Client()                                                                # a second device for A
        A2.call("POST", "/api/session", json={"access_token": a["token"]})
        check("A is signed in on two devices", A.call("GET", "/api/me").json().get("signed_in") is True
              and A2.call("GET", "/api/me").json().get("signed_in") is True)
        forged = Client().call("POST", "/api/session/revoke", json={"access_token": "forged"})
        check("a forged token revokes nothing", forged.status_code == 200 and A.call("GET", "/api/me").json().get("signed_in") is True)
        rv = Client().call("POST", "/api/session/revoke", json={"access_token": a["token"]})   # what the reset page does
        check("revoke answers ok", rv.status_code == 200, rv.text[:80])
        check("...and signs out every device", A.call("GET", "/api/me").json().get("signed_in") is False
              and A2.call("GET", "/api/me").json().get("signed_in") is False)
        check("...but the person can sign in again", A.call("POST", "/api/session", json={"access_token": a["token"]}).status_code == 200
              and A.call("GET", "/api/me").json().get("signed_in") is True)
        check("...and B was not signed out by A's revoke", B.call("GET", "/api/me").json().get("signed_in") is True)

        wrong = B.call("POST", "/api/account/delete", json={"confirm": "someone-else@example.com"})
        check("deleting needs the right email", wrong.status_code == 422, str(wrong.status_code))
        check("...and nothing was deleted", B.call("GET", "/api/me").json().get("signed_in") is True)
        gone = B.call("POST", "/api/account/delete", json={"confirm": b["email"]})
        check("B can delete their own workspace", gone.status_code == 200 and gone.json().get("deleted") is True, gone.text[:160])
        check("...their session ends", B.call("GET", "/api/me").json().get("signed_in") is False)
        check("...their sign-in record is removed at Supabase", gone.json().get("sign_in_record_deleted") is True,
              "the backend may lack SUPABASE_SERVICE_ROLE_KEY")
        login = requests.post(f"{SUPA}/auth/v1/token?grant_type=password", headers={"apikey": ANON},
                              json={"email": b["email"], "password": b["password"]}, timeout=30)
        check("...so they cannot sign in again", login.status_code == 400, str(login.status_code))
        check("A's data survived B's deletion", A.call("GET", "/api/content").json().get("total") == 2)
        check("...and so did A's project", HOST in A.call("GET", "/api/projects").text)

        print("\nwaiting for the one queued scan to finish before cleanup")
        deadline = time.time() + 120
        from sqlalchemy import select

        from app.db import session_scope
        from app.models import Scan
        while time.time() < deadline:
            with session_scope() as db:
                status = db.scalars(select(Scan.status).where(Scan.id == project.get("scan_id"))).first()
            if status not in ("queued", "running", "pending", None):
                break
            time.sleep(4)
        print(f"  scan status: {status}")
    except Exception as exc:                                       # noqa: BLE001
        check("the run completed without an exception", False, repr(exc))
    finally:
        cleanup([u for u in (a, b) if u])

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed, {len(failed)} failed, {len(notes)} notes")
    for name, _ok, detail in failed:
        print(f"  FAIL {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--cleanup":
        # Remove the database rows a crashed run left behind (its Supabase
        # users are deleted separately). Pass the run tag it printed.
        TAG = sys.argv[2]
        cleanup([{"email": f"fig-e2e-{TAG}-{x}@example.com", "uid": None} for x in "ab"])
        raise SystemExit(0)
    raise SystemExit(main())
