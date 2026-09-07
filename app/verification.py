"""Domain ownership proof for the Verified/Project tier — same pattern as
Google Search Console: a DNS TXT record, or a meta tag on the homepage.
Never required for a one-off Scan, only to attach a Watch (see CLAUDE.md).
"""
from __future__ import annotations

import secrets

import dns.resolver
import requests
from bs4 import BeautifulSoup

VERIFICATION_PREFIX = "ai-tell-verify"
REQUEST_TIMEOUT = 10


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
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "AITellChecker/0.1"})
        response.raise_for_status()
    except requests.RequestException:
        return False

    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.find("meta", attrs={"name": "ai-tell-verification"})
    return bool(tag and tag.get("content", "").strip() == token)
