"""Stripe.

The meter is sites, not seats — a partner with three logins and four hundred
client sites pays for four hundred. That means the subscription carries a
quantity that has to be kept in step with the estate, which is what
`sync_quantity` is for: adding a site through the API changes the invoice
without anyone re-signing anything.

Everything here degrades quietly. With no STRIPE_SECRET_KEY the routes report
that billing is off and the rest of the product is unaffected.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import config
from app.auth import require_account
from app.db import get_session
from app.models import Account

log = logging.getLogger("fig.billing")
router = APIRouter(prefix="/v1/billing", tags=["billing"])


def _stripe():
    if not config.STRIPE_SECRET_KEY:
        raise HTTPException(503, "billing is not configured (set STRIPE_SECRET_KEY)")
    try:
        import stripe
    except ImportError as exc:                     # pragma: no cover
        raise HTTPException(503, "the stripe package is not installed") from exc
    stripe.api_key = config.STRIPE_SECRET_KEY
    return stripe


def price_quote(site_count: int) -> dict:
    """What an estate of this size costs, and what the next tier would save.
    Used by the dashboard and worth exposing — partners ask before they grow."""
    rate = Account.rate_for(site_count)
    tiers = []
    for threshold, cents in Account.TIERS:
        tiers.append({"from_sites": threshold, "cents_per_site": cents,
                      "current": cents == rate})
    return {
        "sites": site_count,
        "cents_per_site": rate,
        "monthly_cents": site_count * rate,
        "tiers": tiers,
    }


@router.get("/quote")
def quote(account: Account = Depends(require_account)):
    n = max(account.billable_sites(), account.site_floor)
    q = price_quote(n)
    q["billable_sites"] = account.billable_sites()
    q["site_floor"] = account.site_floor
    q["enabled"] = config.BILLING_ENABLED
    q["trial_days_left"] = account.trial_days_left()
    q["on_trial"] = account.on_trial()
    return q


def ensure_customer(session: Session, account: Account) -> str:
    stripe = _stripe()
    if account.stripe_customer_id:
        return account.stripe_customer_id
    customer = stripe.Customer.create(
        name=account.name,
        email=account.contact_email or None,
        metadata={"fig_account_id": account.id, "fig_slug": account.slug},
    )
    account.stripe_customer_id = customer["id"]
    session.commit()
    return customer["id"]


def start_checkout(session: Session, account: Account) -> dict:
    """A subscription whose quantity is the number of active sites. Plain
    function so both /v1 (partner, API-key auth) and /api (our own
    frontend, session-cookie auth) can call the same implementation rather
    than drifting into two."""
    stripe = _stripe()
    if not config.STRIPE_PRICE_ID:
        raise HTTPException(503, "set STRIPE_PRICE_ID to the per-site recurring price")
    # The Settings button already switches to the portal once subscribed, but
    # this is the function that takes the money, so it refuses on its own: a
    # second tab, a double click or a direct API call must not open a second
    # subscription and charge twice.
    if account.stripe_subscription_id:
        raise HTTPException(409, "This workspace already has a subscription. "
                                 "Change or cancel it from the billing portal.")
    customer_id = ensure_customer(session, account)
    qty = max(account.billable_sites(), account.site_floor, 1)
    # Carry over whatever is left of the free week rather than restarting it
    # — somebody who subscribes on day 3 should not get 7 more days, and
    # should not lose the 4 they had either.
    trial_left = account.trial_days_left()
    sub_data = {"trial_period_days": trial_left} if trial_left else {}

    # FRONTEND_URL, not PUBLIC_URL: Settings lives on the Next.js app, not
    # this JSON-only backend. Sending Stripe's redirect at the backend's own
    # URL would land the browser on a 404 (or the frontend's, if they ever
    # share a domain, dev.by-default assumption) instead of the actual
    # billing tab -- found while wiring these buttons up, never exercised
    # before since nothing called checkout() until now.
    s = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": config.STRIPE_PRICE_ID, "quantity": qty}],
        subscription_data=sub_data or None,
        success_url=f"{config.FRONTEND_URL}/app/settings?tab=billing&checkout=done",
        cancel_url=f"{config.FRONTEND_URL}/app/settings?tab=billing&checkout=cancelled",
        metadata={"fig_account_id": account.id},
    )
    return {"url": s["url"], "quantity": qty, "trial_days": trial_left}


def start_portal(session: Session, account: Account) -> dict:
    stripe = _stripe()
    customer_id = ensure_customer(session, account)
    s = stripe.billing_portal.Session.create(
        customer=customer_id, return_url=f"{config.FRONTEND_URL}/app/settings?tab=billing")
    return {"url": s["url"]}


@router.post("/checkout")
def checkout(account: Account = Depends(require_account),
             session: Session = Depends(get_session)):
    return start_checkout(session, account)


@router.post("/portal")
def portal(account: Account = Depends(require_account),
           session: Session = Depends(get_session)):
    return start_portal(session, account)


def sync_quantity(session: Session, account: Account) -> dict:
    """Push the current site count onto the live subscription. Called after a
    partner provisions or deactivates a site."""
    if not config.BILLING_ENABLED or not account.stripe_subscription_id:
        return {"synced": False, "reason": "no active subscription"}
    stripe = _stripe()
    qty = max(account.billable_sites(), account.site_floor, 1)
    sub = stripe.Subscription.retrieve(account.stripe_subscription_id)
    item = sub["items"]["data"][0]
    if item["quantity"] == qty:
        return {"synced": False, "reason": "already in step", "quantity": qty}
    stripe.Subscription.modify(
        account.stripe_subscription_id,
        items=[{"id": item["id"], "quantity": qty}],
        proration_behavior="create_prorations",
    )
    return {"synced": True, "quantity": qty}


@router.post("/sync")
def sync(account: Account = Depends(require_account),
         session: Session = Depends(get_session)):
    return sync_quantity(session, account)


@router.post("/webhook")
async def webhook(request: Request, session: Session = Depends(get_session)):
    """Signature is verified when STRIPE_WEBHOOK_SECRET is set. Without it the
    endpoint refuses rather than trusting an unsigned body."""
    stripe = _stripe()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not config.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "set STRIPE_WEBHOOK_SECRET before pointing Stripe here")
    try:
        event = stripe.Webhook.construct_event(payload, sig, config.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:                       # noqa: BLE001
        raise HTTPException(400, f"bad signature: {exc}") from exc

    # construct_event() deserializes event.data.object into a typed Stripe
    # object (a Subscription, a checkout Session, ...), not a plain dict --
    # newer stripe-python raises on .get() against those ("a Subscription is
    # not a dict"). This crashed on every single real event type below until
    # caught by testing against a real signed event, since nothing in this
    # file had run against a live key before. .to_dict() makes every .get()
    # call below safe again.
    obj = event["data"]["object"].to_dict()
    kind = event["type"]
    apply_event(session, kind, obj)
    return {"received": True, "type": kind}


# A subscription in one of these states is one FIG should treat as paid for.
# past_due stays subscribed on purpose: Stripe is still retrying the card, and
# cutting someone off on the first failed attempt is a decision for the dunning
# settings, not for this file. Anything else (incomplete, paused, ...) links
# nothing.
SUBSCRIBED_STATUSES = frozenset({"active", "trialing", "past_due"})
ENDED_STATUSES = frozenset({"canceled", "incomplete_expired", "unpaid"})


def _account_for_event(session: Session, obj: dict) -> Account | None:
    account_id = (obj.get("metadata") or {}).get("fig_account_id")
    account = session.get(Account, account_id) if account_id else None
    if account is None and obj.get("customer"):
        account = session.query(Account).filter(
            Account.stripe_customer_id == obj["customer"]).first()
    return account


def apply_event(session: Session, kind: str, obj: dict) -> str | None:
    """Change an account's subscription link for one Stripe event.

    Returns "linked", "cleared", or None when the event changes nothing. Kept
    apart from the HTTP handler so it can be tested without Stripe.

    Stripe does not promise events arrive in order, so this never treats an
    event as "the latest word" on its own: it looks at the subscription's own
    status. That closes two holes the first version had. A late
    `customer.subscription.updated` for an already-cancelled subscription used
    to re-link the account and show a cancelled customer as subscribed. And a
    `customer.subscription.created` for a subscription whose first payment had
    not cleared (status `incomplete`) used to grant access before any money
    moved.
    """
    if kind == "checkout.session.completed":
        if obj.get("mode") != "subscription":
            return None
        # "no_payment_required" is a checkout that starts with a free trial.
        if obj.get("payment_status") not in ("paid", "no_payment_required"):
            return None
        sub_id = obj.get("subscription")
        account = _account_for_event(session, obj)
        if account is None or not sub_id:
            return None
        account.stripe_subscription_id = sub_id
        session.commit()
        log.info("billing: linked account %s to %s", account.slug, sub_id)
        return "linked"

    if kind in ("customer.subscription.created", "customer.subscription.updated"):
        sub_id, status = obj.get("id"), obj.get("status")
        if status in ENDED_STATUSES:
            return _clear(session, sub_id)
        if status not in SUBSCRIBED_STATUSES or not sub_id:
            return None
        account = _account_for_event(session, obj)
        if account is None:
            return None
        account.stripe_subscription_id = sub_id
        session.commit()
        log.info("billing: linked account %s to %s", account.slug, sub_id)
        return "linked"

    if kind == "customer.subscription.deleted":
        return _clear(session, obj.get("id"))
    return None


def _clear(session: Session, sub_id: str | None) -> str | None:
    """Unlink whichever account holds this subscription. Matching on the
    subscription id means ending an old subscription can never unlink a newer
    one the account has since taken out."""
    if not sub_id:
        return None
    account = session.query(Account).filter(
        Account.stripe_subscription_id == sub_id).first()
    if account is None:
        return None
    account.stripe_subscription_id = None
    session.commit()
    log.info("billing: cleared %s from account %s", sub_id, account.slug)
    return "cleared"
