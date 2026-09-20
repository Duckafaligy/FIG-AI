"""The validation system: what FIG is allowed to point a crawler at.

Every scan starts with a hostname somebody typed, and the crawler then makes
server-side HTTP requests on their behalf. That is a server-side request
forgery surface by construction: without a gate, `127.0.0.1`,
`169.254.169.254` (the cloud metadata endpoint) or a name that resolves to
10.0.0.5 would all be fetched from inside our own network, and the response
fed straight into a report.

Three checks, in order, each raising a `ValidationError` with a stable code
the API returns alongside a human message:

  1. `normalise_target` -- syntax, no network. Reduce a URL to a hostname and
     refuse schemes other than http(s), non-standard ports, IP literals,
     malformed labels, and names that are never a public site
     (`localhost`, `*.internal`, `*.local`, ...).
  2. `assert_public_host` -- network. Resolve the name and refuse it if ANY
     address is not globally routable. Any, not all: a name answering with
     one public and one private address is exactly the shape of a rebinding
     attempt.
  3. `check_url` -- both checks again on every individual request the crawler
     makes, including each redirect hop and each sitemap URL, so a public
     page cannot redirect the crawler somewhere private.

Step 1 touches no network and step 2 takes an injectable resolver, so the
whole module is testable offline (see test_backend.py).

DNS rebinding is closed too, not just documented: `check_url` returns the
exact addresses it just validated, and `pinned()` (below) forces the
connection `requests` is about to make to use one of them, instead of
letting `requests` resolve the hostname again at connect time. Without this,
an answer that changes between our check and that connection (DNS rebinding
with a near-zero TTL) would bypass every check above -- the check would pass
against a public address while the actual connection went wherever the
second, attacker-controlled answer pointed.
"""
from __future__ import annotations

import contextlib
import ipaddress
import re
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterator
from urllib.parse import urlsplit


class ValidationError(ValueError):
    """A target FIG will not read. `code` is stable and machine-readable;
    `message` is written for a person."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


# Names that are never a public website, however they happen to resolve.
RESERVED_SUFFIXES = (
    "localhost", "localdomain", "local", "internal", "intranet", "lan",
    "home", "corp", "private", "arpa", "test", "example", "invalid", "onion",
)

_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
# An alphabetic TLD (or a punycode one). This alone rejects the numeric
# spellings of IP addresses -- "2130706433", "0x7f.0.0.1" -- that
# getaddrinfo would otherwise happily turn into 127.0.0.1.
_TLD = re.compile(r"^(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$")
_DEFAULT_PORTS = (None, 80, 443)


@dataclass
class Target:
    """A hostname FIG will read, and what normalisation changed to get there."""

    raw: str
    hostname: str
    notes: list[str] = field(default_factory=list)


@dataclass
class Resolution:
    hostname: str
    addresses: list[str]


Resolver = Callable[[str], list[str]]


# --- 1. syntax -----------------------------------------------------------


def normalise_target(value: object) -> Target:
    """Reduce whatever was typed to a bare public-looking hostname."""
    raw = value if isinstance(value, str) else ""
    text = raw.strip()
    if not text:
        raise ValidationError("empty", "No hostname or URL was given.")
    if any(ch.isspace() for ch in text):
        raise ValidationError(
            "bad_hostname", f"{text!r} contains spaces, so it is not a hostname or URL.")

    notes: list[str] = []
    if "://" in text:
        scheme = text.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            raise ValidationError(
                "bad_scheme", f"Only http and https sites can be read, not {scheme}://.")
        parts = urlsplit(text)
        notes.append(f"dropped the scheme {scheme}://")
    else:
        parts = urlsplit(f"//{text}")

    try:
        port = parts.port
    except ValueError:
        raise ValidationError("bad_hostname", f"{text!r} has an invalid port.") from None
    if port not in _DEFAULT_PORTS:
        raise ValidationError(
            "has_port",
            f"Port {port} is not supported. Give the site's hostname; "
            "sites are read over the standard ports.")
    if port is not None:
        notes.append(f"dropped the default port :{port}")
    if parts.username or parts.password:
        notes.append("dropped the credentials embedded in the URL")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        notes.append("dropped the path -- a scan reads the whole site from its homepage")

    host = (parts.hostname or "").strip()
    if not host:
        raise ValidationError("bad_hostname", f"{text!r} does not contain a hostname.")
    if host.endswith("."):
        host = host.rstrip(".")
        notes.append("dropped the trailing dot")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValidationError(
            "ip_literal",
            f"{host} is an IP address. FIG reads sites by domain name; "
            "give the site's hostname instead.")

    if not host.isascii():
        try:
            encoded = host.encode("idna").decode("ascii")
        except UnicodeError:
            raise ValidationError(
                "bad_hostname", f"{host!r} is not a valid internationalised domain name.") from None
        notes.append(f"encoded the internationalised name as {encoded}")
        host = encoded
    host = host.lower()

    for suffix in RESERVED_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            raise ValidationError(
                "reserved_name",
                f"{host} is under the reserved name '{suffix}', which never "
                "points at a public website.")

    labels = host.split(".")
    if (len(host) > 253 or len(labels) < 2
            or not all(_LABEL.match(label) for label in labels)
            or not _TLD.match(labels[-1])):
        raise ValidationError("bad_hostname", f"{host!r} does not look like a public domain name.")

    return Target(raw=raw, hostname=host, notes=notes)


# --- 2. network ----------------------------------------------------------


def is_public_address(address: str) -> bool:
    """True only for globally routable unicast addresses. Loopback, private,
    link-local (which includes 169.254.169.254), carrier-grade NAT, reserved
    and multicast ranges are all refused; IPv4-mapped IPv6 is unwrapped first
    so ::ffff:127.0.0.1 cannot slip through."""
    try:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def system_resolver(hostname: str) -> list[str]:
    infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


def assert_public_host(hostname: str, resolver: Resolver | None = None) -> Resolution:
    resolve = resolver or system_resolver
    try:
        addresses = [a for a in resolve(hostname) if a]
    except (OSError, UnicodeError) as exc:          # socket.gaierror is an OSError
        raise ValidationError("dns_failed", f"{hostname} does not resolve ({exc}).") from None
    if not addresses:
        raise ValidationError("dns_failed", f"{hostname} does not resolve to any address.")

    private = [a for a in addresses if not is_public_address(a)]
    if private:
        raise ValidationError(
            "non_public_address",
            f"{hostname} resolves to {', '.join(private)}, which is not on the "
            "public internet. FIG only reads public sites.")
    return Resolution(hostname=hostname, addresses=addresses)


# A crawl makes dozens of requests to one host; resolving it for every one of
# them would be wasted round trips. Only successes are cached, briefly.
_CACHE_TTL = 120.0
_cache: dict[str, tuple[float, Resolution]] = {}
_cache_lock = threading.Lock()


def _checked(hostname: str, resolver: Resolver | None) -> Resolution:
    if resolver is not None:                        # an injected answer is never cached
        return assert_public_host(hostname, resolver)
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(hostname)
        if hit and now - hit[0] < _CACHE_TTL:
            return hit[1]
    result = assert_public_host(hostname)
    with _cache_lock:
        _cache[hostname] = (now, result)
    return result


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


# --- the two entry points -----------------------------------------------


def validate_target(value: object, resolver: Resolver | None = None) -> tuple[Target, Resolution]:
    """Steps 1 and 2 for a scan target. Raises ValidationError."""
    target = normalise_target(value)
    return target, _checked(target.hostname, resolver)


def check_url(url: str, resolver: Resolver | None = None) -> Resolution:
    """Step 3: the gate in front of every single HTTP request the crawler
    makes. Returns the hostname and addresses it just validated, so the
    caller can pin the actual connection to one of them with `pinned()`
    below -- returning just the hostname (as this used to) would let the
    caller re-resolve at connect time, reopening the rebinding gap this
    whole module exists to close."""
    parts = urlsplit(url)
    if (parts.scheme or "").lower() not in ("http", "https"):
        raise ValidationError("bad_scheme", f"Refusing to fetch {url}: only http and https are allowed.")
    try:
        port = parts.port
    except ValueError:
        raise ValidationError("bad_hostname", f"Refusing to fetch {url}: invalid port.") from None
    if port not in _DEFAULT_PORTS:
        raise ValidationError("has_port", f"Refusing to fetch {url}: non-standard port {port}.")
    target = normalise_target(parts.hostname or "")
    return _checked(target.hostname, resolver)


# --- pinning: make the connection use the address we just checked --------
#
# socket.getaddrinfo is what `requests` (via urllib3) calls to resolve a
# hostname right before connecting. Patched once, process-wide, but scoped
# per call via a thread-local map so concurrent scans of different hosts (see
# app/jobs.py's worker threads) never see each other's pin -- a lookup for
# any hostname not currently pinned on this thread falls straight through to
# the real resolver, unchanged.

_real_getaddrinfo = socket.getaddrinfo
_pin_local = threading.local()


def _pinned_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):  # noqa: A002
    pins = getattr(_pin_local, "map", None)
    address = pins.get(host) if pins else None
    if address is None:
        return _real_getaddrinfo(host, port, family, type, proto, flags)
    is_v6 = ":" in address
    sockaddr = (address, port, 0, 0) if is_v6 else (address, port)
    fam = socket.AF_INET6 if is_v6 else socket.AF_INET
    return [(fam, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]


socket.getaddrinfo = _pinned_getaddrinfo


@contextlib.contextmanager
def pinned(hostname: str, address: str) -> Iterator[None]:
    """Force any connection to `hostname` made on this thread, for the
    duration of this block, to use `address` instead of resolving again."""
    pins = getattr(_pin_local, "map", None)
    if pins is None:
        pins = {}
        _pin_local.map = pins
    previous = pins.get(hostname)
    pins[hostname] = address
    try:
        yield
    finally:
        if previous is None:
            pins.pop(hostname, None)
        else:
            pins[hostname] = previous
