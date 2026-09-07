"""SQLAlchemy models.

The shape follows the way this is actually sold: an Account holds many Sites,
and a Scan is a crawl of one Site producing Findings across four layers. An
Account may be a direct customer, an agency reselling to its own clients, or
a platform embedding FIG under its own brand — which is why the site count,
not the seat count, is the meter.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- who is paying ------------------------------------------------------

ACCOUNT_KINDS = ("direct", "agency", "platform")


class Account(Base):
    """A billing entity. An agency's own clients are Sites, never Accounts —
    the client stays inside the agency's product and never signs up here."""

    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    kind = Column(String, nullable=False, default="direct")
    contact_email = Column(String, nullable=True)

    # Resale: when set, nothing FIG-branded is rendered in this account's
    # reports. The end client sees only the partner.
    white_label = Column(Boolean, nullable=False, default=False)
    brand_name = Column(String, nullable=True)
    brand_color = Column(String, nullable=True)

    # Commercials. site_floor is the annual commitment; anything above it is
    # overage at the tier rate, which is what lets a partner grow without
    # having to re-sign.
    site_floor = Column(Integer, nullable=False, default=0)
    rate_override_cents = Column(Integer, nullable=True)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=_now)

    api_keys = relationship("ApiKey", back_populates="account", cascade="all, delete-orphan")
    sites = relationship("Site", back_populates="account", cascade="all, delete-orphan")

    # Graduated per-site rate, in cents/month. Cheaper as the estate grows,
    # but not so cheap so early that there is nothing left to offer at real
    # volume.
    TIERS = ((1, 2000), (5, 1500), (25, 1200), (100, 900), (300, 700), (1000, 500))

    @classmethod
    def rate_for(cls, site_count: int) -> int:
        rate = cls.TIERS[0][1]
        for threshold, cents in cls.TIERS:
            if site_count >= threshold:
                rate = cents
        return rate

    def billable_sites(self) -> int:
        return sum(1 for s in self.sites if s.is_active)

    def monthly_cents(self) -> int:
        n = max(self.billable_sites(), self.site_floor)
        rate = self.rate_override_cents or self.rate_for(n)
        return n * rate


class ApiKey(Base):
    """Only the hash is stored. The full key is shown once, at creation."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=_uuid)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False, index=True)
    label = Column(String, nullable=False, default="default")
    prefix = Column(String, nullable=False, index=True)
    key_hash = Column(String, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_now)

    account = relationship("Account", back_populates="api_keys")


# --- what is being scanned ---------------------------------------------


class Site(Base):
    """One website under an account. `client_name` is who a partner is
    delivering it for — it goes on their report, not ours."""

    __tablename__ = "sites"
    __table_args__ = (
        UniqueConstraint("account_id", "hostname", name="uq_site_account_hostname"),
        Index("ix_sites_hostname", "hostname"),
    )

    id = Column(String, primary_key=True, default=_uuid)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False, index=True)

    hostname = Column(String, nullable=False)
    label = Column(String, nullable=True)
    client_name = Column(String, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    monitor = Column(Boolean, nullable=False, default=False)
    monitor_days = Column(Integer, nullable=False, default=30)

    # Ownership proof is only needed to schedule monitoring, never for a
    # one-off read (CLAUDE.md, two-tier model).
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_token = Column(String, nullable=True)
    verification_method = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    account = relationship("Account", back_populates="sites")
    scans = relationship(
        "Scan", back_populates="site", cascade="all, delete-orphan",
        order_by="Scan.created_at.desc()",
    )

    def latest_scan(self):
        for s in self.scans:
            if s.status == "done":
                return s
        return None


SCAN_STATUSES = ("queued", "running", "done", "failed")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="queued")
    trigger = Column(String, nullable=False, default="manual")
    error = Column(Text, nullable=True)

    pages_crawled = Column(Integer, nullable=False, default=0)
    pages_requested = Column(Integer, nullable=False, default=0)

    # Four layer scores, 0-100, plus the headline. Named to match what the
    # dashboard shows: Craft, Structure, Search, Answers.
    score = Column(Integer, nullable=True)
    score_craft = Column(Integer, nullable=True)
    score_structure = Column(Integer, nullable=True)
    score_search = Column(Integer, nullable=True)
    score_answers = Column(Integer, nullable=True)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    site = relationship("Site", back_populates="scans")
    pages = relationship("Page", back_populates="scan", cascade="all, delete-orphan")
    findings = relationship(
        "Finding", back_populates="scan", cascade="all, delete-orphan",
        order_by="Finding.weight.desc()",
    )

    def duration_s(self) -> float | None:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class Page(Base):
    __tablename__ = "pages"

    id = Column(String, primary_key=True, default=_uuid)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, index=True)

    url = Column(String, nullable=False)
    path = Column(String, nullable=False, default="/")
    title = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=False, default=0)
    section_roles = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=_now)

    scan = relationship("Scan", back_populates="pages")


LAYERS = ("craft", "structure", "search", "answers")
SEVERITIES = ("info", "low", "medium", "high")


class Finding(Base):
    """One flagged pattern. `why` and `fix` come from the rule itself;
    ai_explain may rewrite them for this specific page, but a finding is
    complete and useful with no LLM call at all."""

    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=_uuid)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, index=True)
    page_url = Column(String, nullable=True)

    check = Column(String, nullable=False, index=True)
    layer = Column(String, nullable=False, default="craft")
    severity = Column(String, nullable=False, default="medium")
    weight = Column(Float, nullable=False, default=1.0)

    summary = Column(Text, nullable=False)
    why = Column(Text, nullable=True)
    fix = Column(Text, nullable=True)
    evidence = Column(JSON, nullable=True)
    count = Column(Integer, nullable=False, default=0)
    ai_written = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=_now)

    scan = relationship("Scan", back_populates="findings")


# --- the queue ----------------------------------------------------------

JOB_STATUSES = ("queued", "running", "done", "failed")


class Job(Base):
    """DB-backed queue. Deliberately boring: a worker claims the oldest
    runnable row. Swapping this for Celery later means replacing this table's
    consumer, not the pipeline."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=_uuid)
    kind = Column(String, nullable=False, default="scan")
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="queued", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error = Column(Text, nullable=True)
    run_after = Column(DateTime, default=_now, index=True)
    claimed_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)


class User(Base):
    """Kept for the Supabase Auth wiring: a user belongs to an account, and
    the account is what holds sites and billing."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True, index=True)
    email = Column(String, unique=True, nullable=False)
    supabase_uid = Column(String, unique=True, nullable=True)
    role = Column(String, nullable=False, default="owner")
    created_at = Column(DateTime, default=_now)


class PublicRead(Base):
    """One free read from the marketing site, and its row in the public feed.

    Anonymous unless `show_hostname` is set by the person who ran it. The
    project rule is explicit that there is no public leaderboard naming real
    sites, so a domain someone else pointed this at never appears here.

    device_hash and ip_hash are one-way and exist only to cap the free read.
    Neither the raw cookie nor the IP is stored.
    """

    __tablename__ = "public_reads"

    id = Column(String, primary_key=True, default=_uuid)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, index=True)

    hostname = Column(String, nullable=False)
    show_hostname = Column(Boolean, nullable=False, default=False)

    score = Column(Integer, nullable=True)
    pages = Column(Integer, nullable=True)
    top_check = Column(String, nullable=True)
    top_layer = Column(String, nullable=True)

    device_hash = Column(String, nullable=False, index=True)
    ip_hash = Column(String, nullable=False, index=True)

    created_at = Column(DateTime, default=_now, index=True)
