"""Turning findings into changes, and changes into edits on the live site.

This is the half of the product that makes an audit worth running: a finding
arrives with a fix, and the fix can be applied to the actual page rather than
copied into somebody's backlog.

Three rules shape it, and they are not negotiable:

1. **Nothing is written without approval** unless the integration explicitly
   has `auto_publish` on, per site, per scope.
2. **Every change keeps its `before`.** A tool that edits a client's site with
   no way back is not something an agency will ever switch on.
3. **Credentials live per site, never per account.** An agency holds keys for
   forty clients; one leaking must not expose the other thirty-nine.

The CMS adapters are not written yet. `publish()` records the attempt and
returns a clear "not connected" rather than pretending, so the queue and the
approval flow can be used and reviewed before any write path exists.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Change, Finding, Integration, Site

log = logging.getLogger("fig.publishing")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Which findings have a fix that can be applied mechanically, and what kind of
# edit that is. Anything not in here needs a person to write something -- FIG
# will not invent your copy and publish it.
MECHANICAL = {
    "missing_meta_description": ("meta", "Add a meta description"),
    "meta_description_length": ("meta", "Rewrite the meta description to length"),
    "missing_title": ("meta", "Add a page title"),
    "title_length": ("meta", "Shorten the page title"),
    "missing_canonical": ("meta", "Add a canonical link"),
    "missing_lang": ("meta", "Declare the page language"),
    "no_structured_data": ("schema", "Add an Organization block"),
    "thin_structured_data": ("schema", "Extend the structured data"),
    "missing_alt": ("alt", "Describe images that carry meaning"),
    "missing_h1": ("heading", "Promote the headline to an h1"),
    "multiple_h1": ("heading", "Demote the extra h1s"),
    "heading_skips": ("heading", "Step heading levels down one at a time"),
}

# Findings whose fix is a judgement call. They are surfaced as advice, not as
# a publishable change.
ADVISORY = {
    "section_order", "generic_copy", "low_specificity", "no_answerable_questions",
    "component_uniformity", "default_color_palette", "flat_typography",
    "overused_icons", "numbered_eyebrows", "thin_page", "few_internal_links",
}


def propose(session: Session, site: Site) -> list[Change]:
    """Derive changes from the site's latest audit.

    Idempotent: a proposal already on file for the same finding is left alone,
    so re-running this after an audit does not duplicate the queue.
    """
    scan = site.latest_scan()
    if scan is None:
        return []

    existing = {
        c.finding_id for c in session.scalars(
            select(Change).where(Change.site_id == site.id)).all()
        if c.finding_id
    }

    made = []
    for f in scan.findings:
        if f.id in existing or f.check not in MECHANICAL:
            continue
        kind, title = MECHANICAL[f.check]
        change = Change(
            site_id=site.id, finding_id=f.id, page_url=f.page_url,
            kind=kind, layer=f.layer, title=title,
            detail=f.fix or f.why,
            before=(f.evidence or [None])[0] if f.evidence else None,
            after=None,                      # filled in when it is drafted
            state="proposed",
        )
        session.add(change)
        made.append(change)

    if made:
        session.commit()
        log.info("proposed %s change(s) for %s", len(made), site.hostname)
    return made


def queue(session: Session, account: Account, layer: str | None = None) -> dict:
    """The publish console: what is waiting, per site, with its integration."""
    sites = {s.id: s for s in account.sites if s.is_active}
    if not sites:
        return {"rows": [], "counts": {}, "integrations": [], "connected": 0}

    q = select(Change).where(Change.site_id.in_(list(sites)))
    if layer:
        q = q.where(Change.layer == layer)
    changes = session.scalars(q.order_by(Change.proposed_at.desc())).all()

    integrations = session.scalars(
        select(Integration).where(Integration.site_id.in_(list(sites)))).all()
    by_site = {i.site_id: i for i in integrations}

    rows = []
    for c in changes:
        site = sites.get(c.site_id)
        integ = by_site.get(c.site_id)
        rows.append({
            "change": c, "id": c.id, "site_id": c.site_id,
            "hostname": site.hostname if site else "—",
            "client": site.client_name if site else None,
            "page": c.page_url, "kind": c.kind, "title": c.title,
            "detail": c.detail, "state": c.state, "error": c.error,
            "platform": integ.platform if integ else None,
            "can_publish": bool(integ and integ.is_connected()),
            "at": c.proposed_at,
        })

    counts = {}
    for state in ("proposed", "approved", "published", "failed", "rejected", "reverted"):
        counts[state] = sum(1 for r in rows if r["state"] == state)

    return {
        "rows": rows,
        "counts": counts,
        "integrations": integrations,
        "connected": sum(1 for i in integrations if i.is_connected()),
        "sites": len(sites),
    }


def approve(session: Session, account: Account, change_id: str) -> Change:
    change = _owned(session, account, change_id)
    change.state = "approved"
    change.approved_at = _now()
    session.commit()
    return change


def reject(session: Session, account: Account, change_id: str) -> Change:
    change = _owned(session, account, change_id)
    change.state = "rejected"
    session.commit()
    return change


def publish(session: Session, account: Account, change_id: str) -> dict:
    """Write one approved change to the live site.

    The CMS adapters are not built. Rather than silently succeeding, this
    records the attempt against the change and says exactly what is missing,
    so the console is honest about what it can and cannot do today.
    """
    change = _owned(session, account, change_id)
    if change.state != "approved":
        return {"ok": False, "reason": "A change has to be approved before it is published."}

    integ = session.scalars(
        select(Integration).where(Integration.site_id == change.site_id)).first()
    if integ is None or not integ.is_connected():
        change.state = "failed"
        change.error = ("No CMS is connected for this site. Connect one under "
                        "Settings -> Integrations.")
        session.commit()
        return {"ok": False, "reason": change.error}

    change.state = "failed"
    change.error = (f"The {integ.platform} adapter is not implemented yet. The change, "
                    "its approval and its before-state are all recorded, so it will "
                    "publish as soon as the adapter lands.")
    session.commit()
    return {"ok": False, "reason": change.error}


def revert(session: Session, account: Account, change_id: str) -> dict:
    change = _owned(session, account, change_id)
    if change.state != "published":
        return {"ok": False, "reason": "Only a published change can be reverted."}
    if change.before is None:
        return {"ok": False, "reason": "No before-state was recorded, so this cannot be undone."}
    change.state = "reverted"
    change.reverted_at = _now()
    session.commit()
    return {"ok": True}


def _owned(session: Session, account: Account, change_id: str) -> Change:
    from fastapi import HTTPException
    change = session.get(Change, change_id)
    if change is None:
        raise HTTPException(404, "no such change")
    site = session.get(Site, change.site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such change")
    return change


def connect(session: Session, account: Account, site_id: str, platform: str,
            endpoint: str, credential: str) -> Integration:
    """Record a CMS connection.

    The credential itself is not stored: only a reference for the secret store
    and a hint so a person can tell which key is which. Until a secret store
    is wired up the reference is a placeholder, which is why `is_connected`
    also requires `connected_at`.
    """
    from fastapi import HTTPException
    site = session.get(Site, site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such site")

    integ = session.scalars(
        select(Integration).where(Integration.site_id == site_id,
                                  Integration.platform == platform)).first()
    if integ is None:
        integ = Integration(site_id=site_id, platform=platform)
        session.add(integ)

    integ.endpoint = endpoint.strip() or None
    if credential:
        tail = credential.strip()[-4:]
        integ.credential_ref = f"pending:{site_id}:{platform}"
        integ.credential_hint = f"{platform[:2]}_...{tail}"
        # Deliberately not set: a connection is not live until the secret is
        # actually held somewhere and a test call has succeeded.
        integ.connected_at = None
        integ.last_error = ("Stored as pending. A secret store and a test call are "
                            "needed before FIG will write to this site.")
    session.commit()
    return integ


def disconnect(session: Session, account: Account, integration_id: str) -> None:
    from fastapi import HTTPException
    integ = session.get(Integration, integration_id)
    if integ is None:
        raise HTTPException(404, "no such integration")
    site = session.get(Site, integ.site_id)
    if site is None or site.account_id != account.id:
        raise HTTPException(404, "no such integration")
    session.delete(integ)
    session.commit()
