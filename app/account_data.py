"""Deleting a workspace and everything in it.

The privacy policy promises deletion on request; this is the request. It removes
the sites and their scans, pages, findings, content, change history, connected
services *and their stored credentials*, API keys, and the people (`User` rows)
in the workspace, then the workspace itself, and tries to remove the sign-in
record at Supabase so the address can't sign in to nothing.

What it deliberately does not do:
  * Delete Stripe's customer record. Invoices and tax records have to be kept
    (the policy says so); the subscription is cancelled instead.
  * Touch anyone else's data, or the seeded demo workspace.

Order matters and is chosen so a failure leaves a workspace that is whole rather
than half-gone: refuse first (cheap checks), cancel billing second (so nobody is
charged for a workspace that no longer exists, and if Stripe won't cancel we stop
here), delete data third, sign-in record last (best effort; it's the one step
that can be finished later by hand).
"""
from __future__ import annotations

import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import billing, config
from app.models import (Account, Change, ContentPost, Integration, Job,
                        PublicRead, Scan, Site, User)
from app.secrets_store import delete_secret

log = logging.getLogger("fig.account")


class DeletionRefused(Exception):
    """A deletion that must not go ahead, with a reason worth showing."""

    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def _check_allowed(session: Session, account: Account, user: User, confirm: str) -> list[User]:
    if account.slug == config.DEMO_ACCOUNT_SLUG:
        raise DeletionRefused("The demo workspace can't be deleted.", 403)
    members = list(session.scalars(select(User).where(User.account_id == account.id)))
    if user.account_id != account.id or user.role != "owner":
        raise DeletionRefused("Only the workspace owner can delete it.", 403)
    if len(members) > 1:
        raise DeletionRefused(
            "This workspace has other members. Remove them first, or ask us to help.")
    if (confirm or "").strip().lower() != (user.email or "").strip().lower():
        raise DeletionRefused("Type your account email address to confirm.", 422)
    return members


def delete_auth_user(supabase_uid: str | None) -> bool:
    """Remove the person's sign-in record at Supabase. Best effort: returns
    False (and logs) when it can't, so the caller can say so honestly."""
    if not supabase_uid or not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        return False
    try:
        r = requests.delete(
            f"{config.SUPABASE_URL}/auth/v1/admin/users/{supabase_uid}",
            headers={"apikey": config.SUPABASE_SERVICE_ROLE_KEY,
                     "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}"},
            timeout=15)
        return r.status_code in (200, 204, 404)     # 404: already gone
    except requests.RequestException:
        log.exception("could not delete the Supabase sign-in record %s", supabase_uid)
        return False


def delete_workspace(session: Session, account: Account, user: User, *, confirm: str) -> dict:
    members = _check_allowed(session, account, user, confirm)
    supabase_uid = user.supabase_uid

    # Billing first. If Stripe will not cancel, nothing has been deleted and the
    # error reaches the caller; the alternative is a deleted workspace that keeps
    # being charged.
    cancelled = False
    if account.stripe_subscription_id:
        if not config.BILLING_ENABLED:
            raise DeletionRefused(
                "This workspace has a subscription but billing is not reachable right now, "
                "so it can't be cancelled safely. Try again shortly.", 503)
        try:
            cancelled = billing.cancel_subscription(account)
        except Exception as exc:                   # noqa: BLE001
            log.exception("stripe refused to cancel %s for account %s",
                          account.stripe_subscription_id, account.slug)
            raise DeletionRefused(
                "We couldn't cancel your subscription, so nothing was deleted. "
                "Try again, or email us.", 502) from exc

    sites = list(session.scalars(select(Site).where(Site.account_id == account.id)))
    site_ids = [s.id for s in sites]
    scan_ids = [x for (x,) in session.execute(select(Scan.id).where(Scan.site_id.in_(site_ids)))] if site_ids else []

    if site_ids:
        # Stored credentials first: once the Integration row is gone nothing
        # would ever point at them again.
        for integ in session.scalars(select(Integration).where(Integration.site_id.in_(site_ids))):
            if integ.credential_ref:
                delete_secret(session, integ.credential_ref)
        for model in (ContentPost, Change, Integration):
            session.query(model).filter(model.site_id.in_(site_ids)).delete(synchronize_session=False)
    if scan_ids:
        session.query(PublicRead).filter(PublicRead.scan_id.in_(scan_ids)).delete(synchronize_session=False)
        # Queued or running scans of this workspace would fail on a missing row.
        for job in session.scalars(select(Job).where(Job.created_at >= account.created_at)):
            if any(scan_id in str(job.payload) for scan_id in scan_ids):
                session.delete(job)
    session.flush()

    # People point at the account, so they go before it; sites, scans, pages,
    # findings and API keys go with the account through its cascades.
    for member in members:
        session.delete(member)
    session.flush()
    session.delete(account)
    session.commit()

    auth_deleted = delete_auth_user(supabase_uid)
    log.info("deleted workspace %s (%d sites, subscription cancelled: %s, sign-in record deleted: %s)",
             account.slug, len(sites), cancelled, auth_deleted)
    return {"deleted": True, "sites": len(sites),
            "subscription_cancelled": cancelled, "sign_in_record_deleted": auth_deleted}
