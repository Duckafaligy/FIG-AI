"""Test runs: drive the real backend end to end and write down what happened.

    python scripts/test_run.py launchvault.ca
    python scripts/test_run.py launchvault.ca --max-pages 10

In order:

  1. Preflight  -- the database is the real one (FIG_DB_STRICT=1, so a dead
                   connection fails the run instead of silently falling back
                   to SQLite), the Claude key is present, schema is current.
  2. Server     -- starts `uvicorn app.main:app` as its own process on a free
                   port with FIG_WORKSPACE_API=0: the backend exactly as it
                   runs disconnected from the frontend.
  3. Routes     -- health, auth (no key, wrong key, real key), the frontend
                   API and browser CORS really being gone, and the validation
                   system refusing unsafe targets through /v1 and /scan.
  4. The scan   -- provisions the target through /v1, checks its ownership
                   status, queues a scan, polls it to completion, then pulls
                   the findings, pages, stage-by-stage trace and estate report,
                   and cross-checks all of it against the database.
  5. The log    -- appends "## Test #N" to `Test Runs.md` at the repo root.

The run uses its own account (slug `test-runs`) and mints an API key for
itself, which it revokes when it finishes. Secrets are redacted from the log.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# Fail loudly rather than quietly testing against a local SQLite file.
os.environ["FIG_DB_STRICT"] = "1"

LOG_FILE = ROOT / "Test Runs.md"
TEST_ACCOUNT_SLUG = "test-runs"
POLL_SECONDS = 1.5
SCAN_TIMEOUT_S = 900
STARTUP_TIMEOUT_S = 90

try:
    import httpx
    from sqlalchemy import func, inspect, select

    from app import config
    from app.auth import mint_key
    from app.db import IS_SQLITE, engine, init_db, session_scope
    from app.models import Account, ApiKey, Finding, Job, Page, Scan
    from app.validation import ValidationError, normalise_target
except Exception as _exc:                          # noqa: BLE001
    BOOT_ERROR: Exception | None = _exc
else:
    BOOT_ERROR = None


# (input, what it is, the code the validation system should answer with)
UNSAFE_TARGETS = [
    ("127.0.0.1", "loopback address", "ip_literal"),
    ("169.254.169.254", "cloud metadata endpoint", "ip_literal"),
    ("http://10.0.0.1:8080/admin", "private address on a non-standard port", "has_port"),
    ("2130706433", "127.0.0.1 written as a number", "bad_hostname"),
    ("localhost", "reserved name", "reserved_name"),
    ("printer.internal", "internal-only suffix", "reserved_name"),
    ("127.0.0.1.nip.io", "real public DNS name that resolves to 127.0.0.1", "non_public_address"),
    (f"fig-nx-{secrets.token_hex(5)}.com", "domain that does not exist", "dns_failed"),
    ("ftp://launchvault.ca", "non-web scheme", "bad_scheme"),
    ("not a hostname", "not a hostname at all", "bad_hostname"),
    ("", "empty input", "empty"),
]

STAGE_ORDER = ["validate", "resolve_base", "robots", "discover", "fetch", "rules",
               "explain", "score", "persist"]


# --- small helpers ---------------------------------------------------------


def _ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


def fmt_ms(ms: int | float | None) -> str:
    if ms is None:
        return "—"
    return f"{ms:,.0f} ms" if ms < 1000 else f"{ms / 1000:,.1f} s"


def fmt_bytes(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n:,} B" if n < 1024 else f"{n / 1024:,.1f} KB"


def cell(value) -> str:
    """Safe inside a Markdown table cell."""
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip() or "—"


def path_of(url: str) -> str:
    parsed = urlparse(url or "")
    return (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def next_test_number() -> int:
    if not LOG_FILE.exists():
        return 1
    found = [int(n) for n in re.findall(r"^## Test #(\d+)", LOG_FILE.read_text(encoding="utf-8"),
                                         flags=re.M)]
    return max(found, default=0) + 1


def _oracle_allowed(robots_text: str, path: str) -> bool:
    """A deliberately small, separate reading of robots.txt to check the
    backend against: the `*` group(s), blank lines ignored, plain prefix rules,
    longest match wins and Allow wins a tie. Enough to catch the crawler reading
    a path the site disallows, which Test #1 did."""
    rules: list[tuple[bool, str]] = []
    in_star, last_was_agent = False, False
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not last_was_agent:
                in_star = False
            in_star = in_star or value == "*"
            last_was_agent = True
        elif key in ("allow", "disallow"):
            last_was_agent = False
            if in_star and value:
                rules.append((key == "allow", value))
    best: tuple[bool, str] | None = None
    for allow, prefix in rules:
        if path.startswith(prefix) and (best is None or len(prefix) > len(best[1])
                                        or (len(prefix) == len(best[1]) and allow)):
            best = (allow, prefix)
    return True if best is None else best[0]


class Api:
    """A thin HTTP client that records every call it makes."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.client = httpx.Client(base_url=base, timeout=60.0)
        self.calls: list[dict] = []

    def call(self, step: str, method: str, path: str, *, expect, key: str | None = None,
             json_body=None, params: dict | None = None, headers: dict | None = None,
             note: str = ""):
        sent = dict(headers or {})
        if key:
            sent["X-API-Key"] = key
        expected = tuple(expect) if isinstance(expect, (tuple, list)) else (expect,)
        started = time.monotonic()
        status, body, got_headers = None, None, {}
        try:
            resp = self.client.request(method, path, params=params, json=json_body, headers=sent)
            status, got_headers = resp.status_code, {k.lower(): v for k, v in resp.headers.items()}
            try:
                body = resp.json()
            except ValueError:
                body = resp.text[:500]
        except httpx.HTTPError as exc:
            body = f"{type(exc).__name__}: {exc}"
        shown = path + (f"?{urlencode(params)}" if params else "")
        ok = status in expected
        self.calls.append({"step": step, "method": method, "path": shown, "status": status,
                           "expect": "/".join(str(e) for e in expected), "ok": ok,
                           "ms": _ms(started), "note": note})
        print(f"  [{'ok ' if ok else 'BAD'}] {method:<7} {shown[:60]:<60} -> {status}")
        return status, body, got_headers


# --- the run ----------------------------------------------------------------


class TestRun:
    def __init__(self, target: str, max_pages: int | None, argv: list[str]) -> None:
        self.target = target
        self.max_pages = max_pages
        self.argv = argv
        self.number = next_test_number()
        self.started_at = datetime.now().astimezone()
        self.wall_started = time.monotonic()

        self.checks: list[dict] = []
        self.errors: list[str] = []
        self.secrets: list[str] = []
        self.env: dict = {}
        self.api: Api | None = None
        self.proc: subprocess.Popen | None = None
        self.server: dict = {}
        self.server_log_text = ""

        self.expected_host = ""
        self.key = ""
        self.key_id = ""
        self.account_id = ""
        self.site: dict = {}
        self.site_id = ""
        self.rejections: list[dict] = []
        self.ownership: dict = {}
        self.scan_id = ""
        self.scan_status = ""
        self.scan_transitions: list[tuple[float, str]] = []
        self.scan_wall_ms = 0
        self.scan_full: dict = {}
        self.pages: list = []
        self.trace: dict = {}
        self.report: dict = {}
        self.db: dict = {}
        self.robots_oracle: dict = {}

    # -- bookkeeping --

    def check(self, section: str, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append({"section": section, "name": name, "ok": bool(ok), "detail": detail})
        print(f"  [{'ok ' if ok else 'BAD'}] {name}" + (f" -- {detail}" if detail and not ok else ""))
        return bool(ok)

    def phase(self, name: str, fn) -> bool:
        print(f"\n== {name}")
        try:
            fn()
            return True
        except Exception as exc:                   # noqa: BLE001
            self.errors.append(f"{name}: {type(exc).__name__}: {exc}")
            print(f"  !! {name} failed: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            return False

    def _collect_secrets(self) -> None:
        for key, value in os.environ.items():
            if value and len(value) >= 8 and re.search(r"KEY|SECRET|PASSWORD|TOKEN|DATABASE_URL",
                                                        key, re.I):
                self.secrets.append(value)
        if engine.url.password:
            self.secrets.append(str(engine.url.password))

    def redact(self, text: str) -> str:
        for value in sorted(set(self.secrets), key=len, reverse=True):
            if value:
                text = text.replace(value, "[redacted]")
        text = re.sub(r"sk-ant-[A-Za-z0-9_\-]{8,}", "[redacted]", text)
        text = re.sub(r"fig_live_[A-Za-z0-9]+_[A-Za-z0-9_\-]+", "fig_live_[redacted]", text)
        text = re.sub(r"postgres(?:ql)?://\S+", "postgresql://[redacted]", text)
        return text

    # -- phases --

    def execute(self) -> None:
        if not self.phase("preflight", self.preflight):
            return
        if not self.phase("API key for this run", self.provision_key):
            return
        try:
            if not self.phase("start the backend", self.start_server):
                return
            self.phase("routes", self.route_checks)
            self.phase("validation system", self.validation_checks)
            if self.phase("provision the site", self.provision_site):
                self.phase("ownership", self.ownership_checks)
                if self.phase("scan", self.run_scan):
                    self.phase("results", self.fetch_results)
                    self.phase("database cross-check", self.db_cross_check)
        finally:
            self.phase("stop the backend", self.stop_server)
            self.phase("revoke the API key", self.revoke_key)

    def preflight(self) -> None:
        self._collect_secrets()
        self.expected_host = normalise_target(self.target).hostname
        started = time.monotonic()
        init_db()
        init_ms = _ms(started)
        columns = {c["name"] for c in inspect(engine).get_columns("scans")}
        self.env = {
            "python": sys.version.split()[0],
            "database": "SQLite" if IS_SQLITE else f"Postgres ({engine.url.host})",
            "init_db_ms": init_ms,
            "anthropic_key": bool(config.ANTHROPIC_API_KEY),
            "ai_explain": config.AI_EXPLAIN_ENABLED,
            "ai_model": config.AI_MODEL,
            "ai_prices": f"${config.AI_PRICE_INPUT_PER_MTOK:.2f} in / "
                         f"${config.AI_PRICE_OUTPUT_PER_MTOK:.2f} out per million tokens",
            "user_agent": config.USER_AGENT,
            "crawl_delay_s": config.CRAWL_DELAY,
            "max_pages": self.max_pages or config.MAX_PAGES_PER_SCAN,
            "max_response_bytes": config.MAX_RESPONSE_BYTES,
            "max_redirects": config.MAX_REDIRECTS,
        }
        self.check("preflight", "database is Postgres, not a SQLite fallback", not IS_SQLITE,
                   self.env["database"])
        self.check("preflight", "Anthropic API key is set", bool(config.ANTHROPIC_API_KEY))
        self.check("preflight", "ai_explain is enabled", config.AI_EXPLAIN_ENABLED)
        self.check("preflight", "scans.trace column exists", "trace" in columns)

    def provision_key(self) -> None:
        with session_scope() as s:
            account = s.scalars(select(Account).where(Account.slug == TEST_ACCOUNT_SLUG)).first()
            if account is None:
                account = Account(name="FIG test runs", slug=TEST_ACCOUNT_SLUG, kind="direct")
                s.add(account)
                s.flush()
            row, plaintext = mint_key(s, account, label=f"test-run-{self.number}")
            self.key_id, self.account_id = row.id, account.id
        self.key = plaintext
        self.secrets.append(plaintext)
        self.check("preflight", f"API key minted on account `{TEST_ACCOUNT_SLUG}`", bool(self.key))

    def start_server(self) -> None:
        port = free_port()
        env = os.environ.copy()
        env.update(FIG_WORKSPACE_API="0", FIG_DB_STRICT="1", FIG_DEV_NO_AUTH="0",
                   PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        log_path = Path(tempfile.gettempdir()) / f"fig-test-run-{self.number}-{os.getpid()}.log"
        self._log_handle = open(log_path, "w", encoding="utf-8")
        command = [sys.executable, "-m", "uvicorn", "app.main:app",
                   "--host", "127.0.0.1", "--port", str(port), "--log-level", "info"]
        started = time.monotonic()
        self.proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=self._log_handle,
                                     stderr=subprocess.STDOUT)
        base = f"http://127.0.0.1:{port}"
        self.server = {"command": " ".join(["python", *command[1:]]), "base": base,
                       "log_path": str(log_path)}

        deadline = time.monotonic() + STARTUP_TIMEOUT_S
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"the server exited with code {self.proc.returncode} while starting")
            try:
                if httpx.get(f"{base}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError(f"the server did not answer /health within {STARTUP_TIMEOUT_S}s")
        self.server["startup_ms"] = _ms(started)
        self.api = Api(base)
        self.check("server", "backend answers /health", True, fmt_ms(self.server["startup_ms"]))

    def route_checks(self) -> None:
        api = self.api
        status, body, _ = api.call("service", "GET", "/", expect=200)
        self.check("routes", "root lists the workspace API as not mounted",
                   isinstance(body, dict) and body.get("workspace_api") is None)

        status, body, _ = api.call("service", "GET", "/health", expect=200)
        body = body if isinstance(body, dict) else {}
        self.server["health"] = body
        self.check("routes", "/health reports Postgres, ai_explain on, workspace API off",
                   body.get("db") == "postgres" and body.get("ai_explain") is True
                   and body.get("workspace_api") is False, json.dumps(body))

        api.call("frontend disconnected", "GET", "/api/me", expect=404, note="workspace API not mounted")
        api.call("frontend disconnected", "GET", "/api/projects", expect=404, note="workspace API not mounted")
        _s, _b, headers = api.call(
            "frontend disconnected", "OPTIONS", "/v1/sites", expect=(400, 405),
            headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "POST"},
            note="CORS preflight from the Next.js dev origin")
        self.check("routes", "no browser origin is allowed (no CORS headers returned)",
                   "access-control-allow-origin" not in headers)

        api.call("auth", "GET", "/v1/account", expect=401, note="no key")
        api.call("auth", "GET", "/v1/account", key="fig_live_00000000_not-a-real-key",
                 expect=401, note="wrong key")
        api.call("auth", "GET", "/v1/account", key=self.key, expect=200, note="key minted for this run")

    def validation_checks(self) -> None:
        for value, label, code in UNSAFE_TARGETS:
            status, body, _ = self.api.call("validation", "POST", "/v1/sites", key=self.key,
                                            json_body={"hostname": value}, expect=422, note=label)
            detail = body.get("detail") if isinstance(body, dict) else None
            detail = detail if isinstance(detail, dict) else {"message": detail}
            self.rejections.append({"input": value, "label": label, "status": status,
                                    "expected": code, "code": detail.get("code"),
                                    "message": detail.get("message")})
        matched = sum(1 for r in self.rejections if r["code"] == r["expected"])
        self.check("validation", "every unsafe target answered with the expected reason code",
                   matched == len(self.rejections), f"{matched}/{len(self.rejections)}")

        status, body, _ = self.api.call("validation", "POST", "/scan",
                                        json_body={"url": "169.254.169.254"}, expect=422,
                                        note="the free public read goes through the same gate")

    def provision_site(self) -> None:
        status, body, _ = self.api.call("provision", "POST", "/v1/sites", key=self.key,
                                        json_body={"hostname": self.target,
                                                   "label": f"Test #{self.number}"},
                                        expect=201, note="as typed")
        if not isinstance(body, dict) or "id" not in body:
            raise RuntimeError(f"provisioning failed: {body}")
        self.site, self.site_id = body, body["id"]
        self.check("provision", f"`{self.target}` stored as `{self.expected_host}`",
                   body.get("hostname") == self.expected_host, str(body.get("hostname")))

        as_url = f"https://{self.target}/pricing?utm_source=fig-test"
        status, again, _ = self.api.call("provision", "POST", "/v1/sites", key=self.key,
                                         json_body={"hostname": as_url}, expect=201,
                                         note="same site given as a full URL")
        self.check("provision", "the URL form resolves to the same site (no duplicate)",
                   isinstance(again, dict) and again.get("id") == self.site_id)
        self.api.call("provision", "GET", f"/v1/sites/{self.site_id}", key=self.key, expect=200)

    def ownership_checks(self) -> None:
        sid = self.site_id
        status, body, _ = self.api.call("ownership", "POST", f"/v1/sites/{sid}/verification",
                                        key=self.key, json_body={"method": "dns_txt"},
                                        expect=200, note="issue a DNS TXT token")
        if isinstance(body, dict) and body.get("token"):
            self.secrets.append(body["token"])
        status, body, _ = self.api.call("ownership", "POST",
                                        f"/v1/sites/{sid}/verification/confirm",
                                        key=self.key, expect=200, note="look the record up")
        verified = body.get("verified") if isinstance(body, dict) else None
        self.ownership = {"method": "dns_txt", "verified": verified}
        self.check("ownership", "unverified (no TXT record) -- and a one-off scan is still allowed",
                   verified is False)

    def run_scan(self) -> None:
        params = {"max_pages": self.max_pages} if self.max_pages else None
        status, body, _ = self.api.call("scan", "POST", f"/v1/sites/{self.site_id}/scans",
                                        key=self.key, params=params, expect=202,
                                        note="queued for a worker")
        if not isinstance(body, dict) or "id" not in body:
            raise RuntimeError(f"could not queue the scan: {body}")
        self.scan_id = body["id"]
        started = time.monotonic()
        last = body.get("status", "queued")
        self.scan_transitions = [(0.0, last)]
        polls = 0
        poll_ms: list[int] = []
        headers = {"X-API-Key": self.key}

        while last not in ("done", "failed"):
            if time.monotonic() - started > SCAN_TIMEOUT_S:
                raise TimeoutError(f"scan still {last} after {SCAN_TIMEOUT_S}s")
            if self.proc and self.proc.poll() is not None:
                raise RuntimeError("the server exited while the scan was running")
            time.sleep(POLL_SECONDS)
            t = time.monotonic()
            resp = self.api.client.get(f"/v1/scans/{self.scan_id}", params={"findings": "false"},
                                       headers=headers)
            poll_ms.append(_ms(t))
            polls += 1
            status_now = resp.json().get("status") if resp.status_code == 200 else f"http {resp.status_code}"
            if status_now != last:
                self.scan_transitions.append((round(time.monotonic() - started, 1), status_now))
                print(f"  .. {status_now} at {self.scan_transitions[-1][0]}s")
                last = status_now

        self.scan_status = last
        self.scan_wall_ms = _ms(started)
        self.api.calls.append({
            "step": "scan", "method": "GET", "path": f"/v1/scans/{self.scan_id}?findings=false",
            "status": 200, "expect": "200", "ok": True,
            "ms": round(sum(poll_ms) / len(poll_ms)) if poll_ms else 0,
            "note": f"polled {polls}x every {POLL_SECONDS}s until {last} (ms is the average)"})
        self.check("scan", "scan finished as `done`", last == "done", last)

    def fetch_results(self) -> None:
        sid = self.scan_id
        _s, body, _ = self.api.call("results", "GET", f"/v1/scans/{sid}", key=self.key,
                                    expect=200, note="scores and findings")
        self.scan_full = body if isinstance(body, dict) else {}
        _s, body, _ = self.api.call("results", "GET", f"/v1/scans/{sid}/pages", key=self.key,
                                    expect=200, note="pages read")
        self.pages = body if isinstance(body, list) else []
        _s, body, _ = self.api.call("results", "GET", f"/v1/scans/{sid}/trace", key=self.key,
                                    expect=200, note="stage-by-stage trace")
        self.trace = (body or {}).get("trace") or {} if isinstance(body, dict) else {}
        _s, body, _ = self.api.call("results", "GET", "/v1/report", key=self.key,
                                    expect=200, note="partner estate roll-up")
        self.report = body if isinstance(body, dict) else {}
        self.api.call("results", "GET", "/v1/scans/not-a-real-scan", key=self.key,
                      expect=404, note="unknown scan id")

        stages = [s.get("stage") for s in self.trace.get("stages", [])]
        self.check("results", "trace covers every pipeline stage",
                   all(s in stages for s in STAGE_ORDER), ", ".join(stages))
        self.check("results", "report lists this site",
                   any(r.get("site_id") == self.site_id for r in self.report.get("rows", [])))

        # An independent reading of robots.txt, deliberately not the backend's
        # parser (see _oracle_allowed). Every page the scan read must pass it.
        robots_text = httpx.get(f"https://{self.expected_host}/robots.txt", timeout=15,
                                headers={"User-Agent": config.USER_AGENT}).text
        read_paths = [path_of(p.get("url", "")) for p in (self._stage_detail("fetch").get("pages") or [])
                      if p.get("outcome") == "ok"]
        blocked = [p for p in read_paths if not _oracle_allowed(robots_text, p)]
        self.robots_oracle = {"read": len(read_paths), "blocked_but_read": blocked}
        self.check("results", "no page the scan read is disallowed by robots.txt (independent check)",
                   not blocked, ", ".join(blocked[:10]))

    def _stage_detail(self, name: str) -> dict:
        for stage in self.trace.get("stages", []):
            if stage.get("stage") == name:
                return stage.get("detail") or {}
        return {}

    def db_cross_check(self) -> None:
        with session_scope() as s:
            scan = s.get(Scan, self.scan_id)
            findings = s.scalar(select(func.count()).select_from(Finding)
                                .where(Finding.scan_id == self.scan_id)) or 0
            ai_written = s.scalar(select(func.count()).select_from(Finding)
                                  .where(Finding.scan_id == self.scan_id,
                                         Finding.ai_written.is_(True))) or 0
            pages = s.scalar(select(func.count()).select_from(Page)
                             .where(Page.scan_id == self.scan_id)) or 0
            jobs = s.scalars(select(Job).order_by(Job.run_after.desc()).limit(25)).all()
            job = next((j for j in jobs if (j.payload or {}).get("scan_id") == self.scan_id), None)
            self.db = {
                "scan_status": scan.status if scan else None,
                "findings_rows": findings,
                "ai_written_rows": ai_written,
                "pages_rows": pages,
                "trace_stored": bool(scan and scan.trace),
                "job_status": job.status if job else None,
                "job_attempts": job.attempts if job else None,
                "duration_s": scan.duration_s() if scan else None,
            }
        api_findings = len(self.scan_full.get("findings") or [])
        api_ai = sum(1 for f in self.scan_full.get("findings") or [] if f.get("ai_written"))
        self.check("database", "findings in the database match the API", findings == api_findings,
                   f"db {findings} vs api {api_findings}")
        self.check("database", "AI-written flags match the API", ai_written == api_ai,
                   f"db {ai_written} vs api {api_ai}")
        self.check("database", "pages in the database match the API", pages == len(self.pages),
                   f"db {pages} vs api {len(self.pages)}")
        self.check("database", "trace stored on the scan row", self.db["trace_stored"])
        self.check("database", "queue job finished on its first attempt",
                   self.db["job_status"] == "done" and self.db["job_attempts"] == 1,
                   f"{self.db['job_status']} after {self.db['job_attempts']} attempt(s)")

    def stop_server(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        handle = getattr(self, "_log_handle", None)
        if handle is not None:
            handle.close()
            self.server_log_text = Path(self.server["log_path"]).read_text(encoding="utf-8",
                                                                           errors="replace")
        if self.api is not None:
            self.api.client.close()

    def revoke_key(self) -> None:
        if not self.key_id:
            return
        with session_scope() as s:
            row = s.get(ApiKey, self.key_id)
            if row is not None:
                row.revoked = True
        print("  key revoked")

    # -- the log --

    def all_checks(self) -> list[dict]:
        route_checks = [{"section": "routes", "name": f"{c['method']} {c['path']}", "ok": c["ok"]}
                        for c in (self.api.calls if self.api else [])]
        return self.checks + route_checks

    def write_log(self) -> Path:
        checks = self.all_checks()
        passed = sum(1 for c in checks if c["ok"])
        success = passed == len(checks) and not self.errors and self.scan_status == "done"
        body = self.redact("\n".join(self.render(checks, passed, success)))

        if LOG_FILE.exists():
            existing = LOG_FILE.read_text(encoding="utf-8").rstrip() + "\n\n---\n\n"
        else:
            existing = (
                "# Test Runs\n\n"
                "End-to-end runs of the FIG backend against real sites, newest at the bottom.\n"
                "Each is produced by `python scripts/test_run.py <site>`: it starts the API\n"
                "disconnected from the frontend, drives it over HTTP the way a client would,\n"
                "and records the validation system, every pipeline stage, what the AI step\n"
                "cost, and what was found.\n\n---\n\n")
        LOG_FILE.write_text(existing + body + "\n", encoding="utf-8")
        return LOG_FILE

    def render(self, checks: list[dict], passed: int, success: bool) -> list[str]:
        out: list[str] = []
        add = out.append
        stages = {s.get("stage"): s for s in self.trace.get("stages", [])}
        detail = lambda name: (stages.get(name) or {}).get("detail") or {}   # noqa: E731
        validate, fetch = detail("validate"), detail("fetch")
        explain, score = detail("explain"), detail("score")
        findings = self.scan_full.get("findings") or []
        layers = self.scan_full.get("layers") or {}
        page_rows = fetch.get("pages") or []
        read = sum(1 for p in page_rows if p.get("outcome") == "ok")
        skipped = [p for p in page_rows if p.get("outcome") != "ok"]
        groups = self._group_findings(findings)
        explained_groups = sum(1 for g in groups if g["ai_written"])

        host = self.expected_host or self.target
        add(f"## Test #{self.number} — {host}")
        add("")
        add(f"**{'PASS' if success else 'FAIL'}** · {passed}/{len(checks)} checks passed · "
            f"{self.started_at:%Y-%m-%d %H:%M} (UTC{self.started_at:%z}) · "
            f"{fmt_ms(_ms(self.wall_started))} total · "
            f"`python scripts/test_run.py {' '.join(self.argv)}`")
        add("")

        add("| | |")
        add("|---|---|")
        addresses = ", ".join(validate.get("addresses") or []) or "—"
        add(f"| Target | `{cell(self.target)}` → `{cell(host)}` ({cell(addresses)}) |")
        if self.scan_id:
            add(f"| Scan | `{self.scan_status or 'not finished'}` · {read} pages read, "
                f"{len(skipped)} skipped · {fmt_ms(self.scan_wall_ms)} from queue to done |")
        if self.scan_full.get("score") is not None:
            add(f"| Score | **{self.scan_full['score']} / 100 — {self.scan_full.get('verdict')}** · "
                f"Craft {layers.get('craft')} · Structure {layers.get('structure')} · "
                f"Search {layers.get('search')} · Answers {layers.get('answers')} |")
            add(f"| Findings | {len(findings)} findings across {len(groups)} distinct problems · "
                f"{explained_groups} of {len(groups)} explained by Claude |")
        if explain:
            add(f"| AI step | `{cell(explain.get('model'))}` (served as "
                f"`{cell(explain.get('resolved_model'))}`) · {explain.get('calls', 0)} calls · "
                f"{explain.get('input_tokens', 0):,} in / {explain.get('output_tokens', 0):,} out "
                f"tokens · **${explain.get('cost_usd', 0):.4f}** |")
        if self.server:
            add(f"| Backend | `{cell(self.server.get('base'))}` · {cell(self.env.get('database'))} · "
                f"workspace API off · up in {fmt_ms(self.server.get('startup_ms'))} |")
        add("")

        # 1. environment
        add("### 1. Environment")
        add("")
        env = self.env
        add(f"- **Database:** {env.get('database', '—')} — `FIG_DB_STRICT=1`, so an unreachable "
            f"database fails the run instead of falling back to SQLite. Schema check "
            f"(`init_db`) took {fmt_ms(env.get('init_db_ms'))}.")
        add(f"- **AI:** key {'present' if env.get('anthropic_key') else 'MISSING'}, model "
            f"`{env.get('ai_model')}`, priced at {env.get('ai_prices')}.")
        add(f"- **Crawler:** user agent `{env.get('user_agent')}`, {env.get('crawl_delay_s')} s "
            f"between requests to a host, up to {env.get('max_pages')} pages, "
            f"{fmt_bytes(env.get('max_response_bytes'))} per response, "
            f"{env.get('max_redirects')} redirects.")
        add(f"- **Server:** `{self.server.get('command', '—')}` with `FIG_WORKSPACE_API=0`, "
            f"Python {env.get('python', '—')}.")
        add("")

        # 2. routes
        add("### 2. Routes")
        add("")
        add("| # | Step | Request | Expected | Got | Time | | Note |")
        add("|---|---|---|---|---|---|---|---|")
        for i, c in enumerate(self.api.calls if self.api else [], 1):
            add(f"| {i} | {cell(c['step'])} | `{cell(c['method'])} {cell(c['path'])}` | "
                f"{cell(c['expect'])} | {cell(c['status'])} | {fmt_ms(c['ms'])} | "
                f"{'✅' if c['ok'] else '❌'} | {cell(c['note'])} |")
        add("")

        # 3. validation
        add("### 3. Validation system")
        add("")
        if validate:
            notes = "; ".join(validate.get("notes") or []) or "nothing to change"
            add(f"**Accepted:** `{cell(self.target)}` → `{cell(validate.get('hostname'))}` "
                f"({notes}). Resolved to {addresses} — every address public, so the crawl was "
                f"allowed. The same site given as `https://{self.target}/pricing?utm_source=fig-test` "
                f"normalised to the same hostname and returned the existing site.")
            add("")
        add(f"**Ownership:** DNS TXT verification was issued and checked — verified: "
            f"`{self.ownership.get('verified')}`. Ownership is only required to schedule "
            f"monitoring; a one-off scan of any public site is allowed without it.")
        add("")
        add("**Rejected** (each is a `POST /v1/sites`, answered before anything is fetched):")
        add("")
        add("| Input | What it is | HTTP | Code | Expected | | Message |")
        add("|---|---|---|---|---|---|---|")
        for r in self.rejections:
            add(f"| `{cell(r['input']) if r['input'] else '(empty)'}` | {cell(r['label'])} | "
                f"{cell(r['status'])} | `{cell(r['code'])}` | `{cell(r['expected'])}` | "
                f"{'✅' if r['code'] == r['expected'] else '❌'} | {cell(r['message'])} |")
        add("")

        # 4. pipeline
        add("### 4. Pipeline")
        add("")
        if not stages:
            add("No trace was recorded.")
            add("")
        else:
            add(f"Trace total: {fmt_ms(self.trace.get('total_ms'))} inside the worker.")
            add("")
            add("| Stage | Status | Time | What happened |")
            add("|---|---|---|---|")
            for stage in self.trace.get("stages", []):
                add(f"| `{cell(stage.get('stage'))}` | {cell(stage.get('status'))} | "
                    f"{fmt_ms(stage.get('ms'))} | {cell(self._summarise_stage(stage))} |")
            add("")
            self._render_robots(add, detail("robots"))
            if self.robots_oracle:
                blocked = self.robots_oracle.get("blocked_but_read") or []
                add(f"**Independent robots check:** of {self.robots_oracle.get('read')} pages read, "
                    f"{len(blocked)} are disallowed by robots.txt"
                    + (f" -- {', '.join(blocked)}" if blocked else "") + ".")
                add("")
            self._render_discovery(add, detail("discover"))
            self._render_pages(add, page_rows, fetch)
            self._render_rules(add, detail("rules"), groups)
            self._render_explain(add, explain)
            if score:
                add("#### Scores")
                add("")
                add("| Layer | Score |")
                add("|---|---|")
                for name in ("craft", "structure", "search", "answers"):
                    add(f"| {name.title()} | {(score.get('layers') or {}).get(name)} |")
                add(f"| **Overall** | **{score.get('overall')} — {score.get('verdict')}** |")
                add("")

        # 5. findings
        add("### 5. Findings")
        add("")
        if not groups:
            add("None recorded.")
            add("")
        for layer in ("craft", "structure", "search", "answers"):
            in_layer = [g for g in groups if g["layer"] == layer]
            if not in_layer:
                continue
            add(f"#### {layer.title()} ({layers.get(layer)}/100)")
            add("")
            for g in in_layer:
                badge = "Claude-written" if g["ai_written"] else "rule text"
                add(f"- **`{g['check']}`** · {g['severity']} · {g['count']}× on "
                    f"{len(g['pages'])} page{'s' if len(g['pages']) != 1 else ''} "
                    f"({', '.join(g['pages'][:4])}{'…' if len(g['pages']) > 4 else ''}) · _{badge}_")
                add(f"  - **Found (one example):** {g['summary']}")
                if g["why"]:
                    add(f"  - **Why:** {g['why']}")
                if g["fix"]:
                    add(f"  - **Fix:** {g['fix']}")
            add("")

        # 6. database
        add("### 6. Database cross-check")
        add("")
        if self.db:
            add("| | Database | API |")
            add("|---|---|---|")
            add(f"| Scan status | {self.db['scan_status']} | {self.scan_status} |")
            add(f"| Findings | {self.db['findings_rows']} | {len(findings)} |")
            add(f"| AI-written findings | {self.db['ai_written_rows']} | "
                f"{sum(1 for f in findings if f.get('ai_written'))} |")
            add(f"| Pages | {self.db['pages_rows']} | {len(self.pages)} |")
            add(f"| Trace stored | {self.db['trace_stored']} | {bool(self.trace)} |")
            add(f"| Queue job | {self.db['job_status']}, attempt {self.db['job_attempts']} | — |")
            add("")
        else:
            add("Not reached.")
            add("")

        # 7. all checks
        add("### 7. Checks")
        add("")
        for c in self.checks:
            add(f"- {'✅' if c['ok'] else '❌'} **{cell(c['section'])}** — {c['name']}"
                + (f" _({c['detail']})_" if c["detail"] and not c["ok"] else ""))
        add(f"- Plus {len(checks) - len(self.checks)} route calls in section 2, "
            f"{sum(1 for c in checks[len(self.checks):] if c['ok'])} as expected.")
        add("")

        # 8. issues
        add("### 8. Issues observed")
        add("")
        issues = self._issues(checks, stages, skipped, explain)
        for issue in issues or ["None."]:
            add(f"- {issue}")
        add("")

        # 9. server log
        add("### 9. Server log (application lines, redacted)")
        add("")
        add("```text")
        lines = [ln for ln in self.server_log_text.splitlines()
                 if " fig" in ln or "WARNING" in ln or "ERROR" in ln or "Traceback" in ln]
        for ln in lines[-60:] or ["(nothing captured)"]:
            add(ln[:300])
        add("```")
        return out

    # -- log pieces --

    def _group_findings(self, findings: list[dict]) -> list[dict]:
        order = {"high": 3, "medium": 2, "low": 1, "info": 0}
        grouped: dict[tuple, dict] = {}
        for f in findings:
            key = (f.get("layer"), f.get("check"))
            g = grouped.setdefault(key, {"layer": f.get("layer"), "check": f.get("check"),
                                         "severity": f.get("severity"), "summary": f.get("summary"),
                                         "why": f.get("why"), "fix": f.get("fix"), "count": 0,
                                         "pages": [], "ai_written": False})
            g["count"] += 1
            p = path_of(f.get("page_url") or "")
            if p not in g["pages"]:
                g["pages"].append(p)
            g["ai_written"] = g["ai_written"] or bool(f.get("ai_written"))
            if order.get(f.get("severity"), 0) > order.get(g["severity"], 0):
                g["severity"] = f.get("severity")
        return sorted(grouped.values(),
                      key=lambda g: (-order.get(g["severity"], 0), -g["count"], g["check"]))

    def _summarise_stage(self, stage: dict) -> str:
        d = stage.get("detail") or {}
        name = stage.get("stage")
        if name == "validate":
            if stage.get("status") != "ok":
                return f"refused: {d.get('code')} — {d.get('error')}"
            return f"{d.get('input')} → {d.get('hostname')} → {', '.join(d.get('addresses') or [])} (all public)"
        if name == "resolve_base":
            attempts = "; ".join(f"{a.get('url')} {a.get('outcome')}"
                                 + (f" {a.get('status')}" if a.get("status") else "")
                                 for a in d.get("attempts") or [])
            return f"{d.get('base_url') or d.get('error')} — tried: {attempts}"
        if name == "robots":
            return (f"{d.get('outcome')} (HTTP {d.get('status')}) · {len(d.get('rules') or [])} rules "
                    f"apply to FIGBot · {len(d.get('sitemaps') or [])} sitemap(s) declared")
        if name == "discover":
            return (f"{len(d.get('sitemaps') or [])} sitemap file(s) read · {d.get('sitemap_urls')} URLs "
                    f"listed · {d.get('same_site_urls')} on this site")
        if name == "fetch":
            skipped = ", ".join(f"{k} {v}" for k, v in (d.get("skipped") or {}).items()) or "none"
            return f"{d.get('read')} read · skipped: {skipped} · {d.get('stopped')}"
        if name == "rules":
            layers = ", ".join(f"{k} {v}" for k, v in (d.get("by_layer") or {}).items())
            return f"{d.get('flags')} flags from {d.get('distinct_checks')} distinct checks ({layers})"
        if name == "explain":
            if stage.get("status") == "skipped":
                return d.get("reason") or "skipped"
            return (f"{d.get('explained')}/{d.get('distinct_findings')} distinct findings explained in "
                    f"{d.get('calls')} calls · {d.get('input_tokens', 0):,} in / "
                    f"{d.get('output_tokens', 0):,} out tokens · ${d.get('cost_usd', 0):.4f}")
        if name == "score":
            return f"overall {d.get('overall')} ({d.get('verdict')}) · {d.get('layers')}"
        if name == "persist":
            return (f"{d.get('pages')} pages and {d.get('findings')} findings saved, "
                    f"{d.get('ai_written')} with Claude-written text")
        return json.dumps(d)[:200]

    def _render_robots(self, add, robots: dict) -> None:
        if not robots:
            return
        add("#### robots.txt")
        add("")
        add(f"`{robots.get('url')}` → HTTP {robots.get('status')}, outcome **{robots.get('outcome')}**, "
            f"read in {fmt_ms(robots.get('ms'))}."
            + (f" Error: {robots.get('error')}" if robots.get("error") else ""))
        add("")
        if robots.get("rules"):
            add("Rules that apply to FIGBot (enforced before every request, including redirect hops):")
            add("")
            add("```text")
            for rule in robots["rules"]:
                add(rule)
            add("```")
            add("")
        for sm in robots.get("sitemaps") or []:
            add(f"- Declared sitemap: `{sm}`")
        if robots.get("sitemaps"):
            add("")

    def _render_discovery(self, add, discover: dict) -> None:
        maps = discover.get("sitemaps") or []
        if not maps:
            return
        add("#### Discovery")
        add("")
        add("| Sitemap | Outcome | HTTP | URLs | Child sitemaps | Time |")
        add("|---|---|---|---|---|---|")
        for m in maps:
            add(f"| `{cell(m.get('url'))}` | {cell(m.get('outcome'))} | {cell(m.get('status'))} | "
                f"{cell(m.get('urls'))} | {cell(m.get('child_sitemaps'))} | {fmt_ms(m.get('ms'))} |")
        add("")

    def _render_pages(self, add, pages: list[dict], fetch: dict) -> None:
        if not pages:
            return
        add("#### Pages")
        add("")
        add(f"{fetch.get('read')} read, {len(pages) - (fetch.get('read') or 0)} skipped; "
            f"stopped because: {fetch.get('stopped')}.")
        add("")
        add("| # | Path | Outcome | HTTP | Size | Time | Note |")
        add("|---|---|---|---|---|---|---|")
        titles = {p.get("url"): p for p in self.pages}
        for i, p in enumerate(pages, 1):
            url = p.get("url", "")
            note = p.get("error") or ""
            if p.get("final_url"):
                note = f"→ {path_of(p['final_url'])} {note}".strip()
            info = titles.get(p.get("final_url") or url)
            if not note and info:
                note = f"“{info.get('title') or ''}” · {info.get('words')} words · sections: " \
                       f"{', '.join(info.get('sections') or []) or '—'}"
            add(f"| {i} | `{cell(path_of(url))}` | {'✅ read' if p.get('outcome') == 'ok' else '⏭ ' + cell(p.get('outcome'))} | "
                f"{cell(p.get('status'))} | {fmt_bytes(p.get('bytes'))} | {fmt_ms(p.get('ms'))} | "
                f"{cell(note)} |")
        add("")

    def _render_rules(self, add, rules: dict, groups: list[dict]) -> None:
        by_check = rules.get("by_check") or {}
        if not by_check:
            return
        layer_of = {g["check"]: g["layer"] for g in groups}
        add("#### Rules")
        add("")
        add(f"{rules.get('flags')} flags over {rules.get('pages')} pages. Deterministic — no model involved.")
        add("")
        add("| Check | Layer | Times flagged |")
        add("|---|---|---|")
        for check, count in by_check.items():
            add(f"| `{cell(check)}` | {cell(layer_of.get(check))} | {count} |")
        add("")

    def _render_explain(self, add, explain: dict) -> None:
        if not explain:
            return
        add("#### AI step (the only model call in the pipeline)")
        add("")
        if not explain.get("enabled"):
            add(f"Skipped: {explain.get('reason')}")
            add("")
            return
        add(f"- Sent **{explain.get('distinct_findings')} items** (one per distinct finding) instead "
            f"of {explain.get('occurrences')} — a check that fires on many pages is explained once.")
        add(f"- Model `{explain.get('model')}`, served as `{explain.get('resolved_model')}`: "
            f"{explain.get('calls')} calls, {explain.get('failed_batches')} failed batches.")
        add(f"- Tokens: {explain.get('input_tokens', 0):,} input, {explain.get('output_tokens', 0):,} output "
            f"→ **${explain.get('cost_usd', 0):.4f}**.")
        add(f"- Explained {explain.get('explained')}, kept the rule's own text for "
            f"{explain.get('kept_rule_text')}.")
        if explain.get("request_ids"):
            add(f"- Request ids: {', '.join('`' + r + '`' for r in explain['request_ids'])}")
        for err in explain.get("errors") or []:
            add(f"- ⚠️ {err}")
        if explain.get("error"):
            add(f"- ⚠️ {explain['error']}")
        add("")

    def _issues(self, checks: list[dict], stages: dict, skipped: list[dict], explain: dict) -> list[str]:
        issues: list[str] = []
        for c in checks:
            if not c["ok"]:
                issues.append(f"❌ Check failed — {c['section']}: {c['name']}"
                              + (f" ({c.get('detail')})" if c.get("detail") else ""))
        issues.extend(f"❌ Harness error — {e}" for e in self.errors)
        if self.scan_full.get("error"):
            issues.append(f"❌ Scan error — {self.scan_full['error']}")
        for name, stage in stages.items():
            if stage.get("status") not in ("ok",):
                issues.append(f"⚠️ Stage `{name}` finished as `{stage.get('status')}`")
        reasons = Counter(p.get("outcome") for p in skipped)
        if reasons.get("robots"):
            paths = ", ".join(path_of(p["url"]) for p in skipped if p.get("outcome") == "robots")
            issues.append(f"ℹ️ {reasons['robots']} page(s) skipped because the site's robots.txt "
                          f"disallows them — expected, and correct: {paths}")
        for reason, count in reasons.items():
            if reason in ("robots", "duplicate"):
                continue
            examples = "; ".join(f"{path_of(p['url'])}: {p.get('error')}" for p in skipped
                                 if p.get("outcome") == reason)[:400]
            issues.append(f"⚠️ {count} page(s) skipped as `{reason}` — {examples}")
        if explain and explain.get("failed_batches"):
            issues.append(f"⚠️ {explain['failed_batches']} AI batch(es) failed; those findings kept rule text")
        warn_lines = [ln for ln in self.server_log_text.splitlines() if " WARNING " in ln or " ERROR " in ln]
        if warn_lines:
            issues.append(f"⚠️ {len(warn_lines)} WARNING/ERROR line(s) in the server log — see section 9")
        return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", help="hostname or URL to scan, e.g. launchvault.ca")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="page limit for the scan (default: the API default)")
    args = parser.parse_args()

    run = TestRun(args.target, args.max_pages, sys.argv[1:])
    print(f"FIG test run #{run.number}: {args.target}")
    if BOOT_ERROR is not None:
        run.errors.append(f"boot: {type(BOOT_ERROR).__name__}: {BOOT_ERROR}")
        print(f"could not import the app: {BOOT_ERROR}")
    else:
        try:
            run.execute()
        except KeyboardInterrupt:
            run.errors.append("interrupted")
            run.phase("stop the backend", run.stop_server)
            run.phase("revoke the API key", run.revoke_key)

    path = run.write_log()
    checks = run.all_checks()
    passed = sum(1 for c in checks if c["ok"])
    print(f"\n{passed}/{len(checks)} checks passed; scan {run.scan_status or 'not run'}; "
          f"log written to {path}")
    return 0 if passed == len(checks) and not run.errors and run.scan_status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
