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

    # A week, free, from the moment the account is created. No card, so it is
    # a trial in the honest sense rather than a subscription that starts
    # quietly.
    trial_ends_at = Column(DateTime, nullable=True)

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

    TRIAL_DAYS = 7

    def trial_days_left(self) -> int:
        """Whole days remaining, 0 once it has run out."""
        if not self.trial_ends_at:
            return 0
        end = self.trial_ends_at
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        left = (end - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(left // 86400) + (1 if left % 86400 else 0))

    def on_trial(self) -> bool:
        return self.trial_days_left() > 0 and not self.stripe_subscription_id


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


# --- publishing to the site itself --------------------------------------

PLATFORMS = ("wordpress", "shopify", "webflow", "ghost", "custom")


class Integration(Base):
    """A CMS FIG is allowed to write back to.

    The whole point of the product is that a finding comes with a fix; an
    integration is what turns the fix into a change on the actual site instead
    of a task in somebody's backlog.

    Credentials are stored per site, never per account: an agency holds keys
    for forty different clients and one leaking must not expose the rest.
    """

    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("site_id", "platform", name="uq_integration_site_platform"),
    )

    id = Column(String, primary_key=True, default=_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)

    endpoint = Column(String, nullable=True)          # admin/API base URL
    # Only ever a reference to the secret, never the secret. Nothing in this
    # table is enough on its own to write to somebody's site.
    credential_ref = Column(String, nullable=True)
    credential_hint = Column(String, nullable=True)   # e.g. "wp_...4f2a"

    # Nothing is written without a person pressing publish unless this is on.
    auto_publish = Column(Boolean, nullable=False, default=False)
    # Categories the integration is allowed to touch, e.g. ["meta", "schema"].
    scopes = Column(JSON, nullable=True)

    connected_at = Column(DateTime, nullable=True)
    last_publish_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)

    site = relationship("Site")

    def is_connected(self) -> bool:
        return bool(self.credential_ref and self.connected_at)


CHANGE_STATES = ("proposed", "approved", "published", "rejected", "failed", "reverted")


class Change(Base):
    """One proposed edit to a live page, and its history.

    A change starts as `proposed` -- derived from a finding -- and only moves
    on when somebody approves it. `before` is kept so a publish can be undone:
    an automated tool that writes to a client site without a way back is not
    something an agency will ever switch on.
    """

    __tablename__ = "changes"

    id = Column(String, primary_key=True, default=_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False, index=True)
    finding_id = Column(String, ForeignKey("findings.id"), nullable=True)

    page_url = Column(String, nullable=True)
    kind = Column(String, nullable=False)             # meta | schema | heading | alt | copy | order
    layer = Column(String, nullable=False, default="search")
    title = Column(String, nullable=False)
    detail = Column(Text, nullable=True)

    before = Column(Text, nullable=True)
    after = Column(Text, nullable=True)

    state = Column(String, nullable=False, default="proposed", index=True)
    error = Column(Text, nullable=True)

    proposed_at = Column(DateTime, default=_now)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    reverted_at = Column(DateTime, nullable=True)

    site = relationship("Site")


# --- the content queue --------------------------------------------------

POST_STATES = ("queued", "in_progress", "review", "scheduled", "published")
PRIORITIES = ("high", "medium", "low")


class ContentPost(Base):
    """A blog post or glossary entry moving through the pipeline.

    This is the other half of publishing: the audit says a page is thin or has
    nothing a model can quote, and the answer is often a page that does not
    exist yet. A post is drafted, reviewed, scheduled, and pushed to the CMS
    through the same Integration as any other change.

    `review` is a state on purpose. Generated copy going straight to a live
    client site with nobody reading it first is exactly the failure this whole
    product is a reaction to.
    """

    __tablename__ = "content_posts"

    id = Column(String, primary_key=True, default=_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    category = Column(String, nullable=False, default="blog")   # blog | glossary | guide
    # Why this piece exists: the finding, in words, carried from the audit.
    brief = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=False, default=0)

    state = Column(String, nullable=False, default="queued", index=True)
    priority = Column(String, nullable=False, default="medium")

    # What the piece is aimed at, and how hard that is.
    target_keyword = Column(String, nullable=True)
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Integer, nullable=True)

    seo_score = Column(Integer, nullable=True)
    # Traffic once it is live. Needs Search Console; null until then.
    clicks = Column(Integer, nullable=True)

    scheduled_for = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    site = relationship("Site")
