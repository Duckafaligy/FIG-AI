"""Domain ownership proof for the Verified/Project tier — same pattern as
Google Search Console: a DNS TXT record, or a meta tag on the homepage.
Never required for a one-off Scan, only to attach a Watch (see CLAUDE.md).
"""
from __future__ import annotations

import secrets
from urllib.parse import urljoin

import dns.resolver
import requests
from bs4 import BeautifulSoup

from app.validation import ValidationError, check_url, pinned

VERIFICATION_PREFIX = "ai-tell-verify"
REQUEST_TIMEOUT = 10
MAX_REDIRECTS = 5
REDIRECT_CODES = (301, 302, 303, 307, 308)


def generate_verification_token() -> str:
    return f"{VERIFICATION_PREFIX}={secrets.token_hex(16)}"


def verify_via_dns_txt(hostname: str, token: str) -> bool:
    try:
        answers = dns.resolver.resolve(hostname, "TXT")
    except Exception:
        return False

    for rdata in answers:
        for txt_string in rdata.strings:
            value = txt_string.decode("utf-8", errors="ignore") if isinstance(txt_string, bytes) else txt_string
            if value.strip() == token:
                return True
    return False


def verify_via_meta_tag(url: str, token: str) -> bool:
    """Fetches `url` (built from a Site's own `hostname`, checked when the
    site was created -- not raw user input at call time). Re-checked here
    anyway, in real time, on every hop: the hostname could have been
    repointed at a private address any time between site creation and this
    call, with nothing as exotic as DNS rebinding required, and a plain
    `requests.get` follows redirects by default with no re-check at all --
    either gap would turn "verify my own site" into fetching whatever an
    attacker's redirect or DNS change points at. `check_url` + `pinned`
    (app/validation.py) close both the same way app/scraper.py does."""
    current = url
    response: requests.Response | None = None
    for _ in range(MAX_REDIRECTS + 1):
        try:
            resolution = check_url(current)
        except ValidationError:
            return False
        try:
            with pinned(resolution.hostname, resolution.addresses[0]):
                response = requests.get(current, timeout=REQUEST_TIMEOUT,
                                         headers={"User-Agent": "AITellChecker/0.1"},
                                         allow_redirects=False)
        except requests.RequestException:
            return False
        if response.status_code not in REDIRECT_CODES:
            break
        location = response.headers.get("location", "").strip()
        if not location:
            return False
        current = urljoin(current, location)
    else:
        return False

    if response is None or not response.ok:
        return False
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.find("meta", attrs={"name": "ai-tell-verification"})
    return bool(tag and tag.get("content", "").strip() == token)
