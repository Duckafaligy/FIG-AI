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


@router.post("/checkout")
def checkout(account: Account = Depends(require_account),
             session: Session = Depends(get_session)):
    """A subscription whose quantity is the number of active sites."""
    stripe = _stripe()
    if not config.STRIPE_PRICE_ID:
        raise HTTPException(503, "set STRIPE_PRICE_ID to the per-site recurring price")
    customer_id = ensure_customer(session, account)
    qty = max(account.billable_sites(), account.site_floor, 1)
    # Carry over whatever is left of the free week rather than restarting it
    # — somebody who subscribes on day 3 should not get 7 more days, and
    # should not lose the 4 they had either.
    trial_left = account.trial_days_left()
    sub_data = {"trial_period_days": trial_left} if trial_left else {}

    s = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": config.STRIPE_PRICE_ID, "quantity": qty}],
        subscription_data=sub_data or None,
        success_url=f"{config.PUBLIC_URL}/app/billing?checkout=done",
        cancel_url=f"{config.PUBLIC_URL}/app/billing?checkout=cancelled",
        metadata={"fig_account_id": account.id},
    )
    return {"url": s["url"], "quantity": qty, "trial_days": trial_left}


@router.post("/portal")
def portal(account: Account = Depends(require_account),
           session: Session = Depends(get_session)):
    stripe = _stripe()
    customer_id = ensure_customer(session, account)
    s = stripe.billing_portal.Session.create(
        customer=customer_id, return_url=f"{config.PUBLIC_URL}/app/billing")
    return {"url": s["url"]}


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

    obj = event["data"]["object"]
    kind = event["type"]

    if kind in ("checkout.session.completed", "customer.subscription.created",
                "customer.subscription.updated"):
        account_id = (obj.get("metadata") or {}).get("fig_account_id")
        account = session.get(Account, account_id) if account_id else None
        if account is None and obj.get("customer"):
            account = session.query(Account).filter(
                Account.stripe_customer_id == obj["customer"]).first()
        if account is not None:
            sub_id = obj.get("subscription") or (obj.get("id") if "sub_" in str(obj.get("id")) else None)
            if sub_id:
                account.stripe_subscription_id = sub_id
            session.commit()
            log.info("billing: linked account %s to %s", account.slug, sub_id)

    elif kind == "customer.subscription.deleted":
        account = session.query(Account).filter(
            Account.stripe_subscription_id == obj.get("id")).first()
        if account is not None:
            account.stripe_subscription_id = None
            session.commit()

    return {"received": True, "type": kind}
