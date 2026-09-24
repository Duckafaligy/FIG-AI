"""Creates the three fixed-price Stripe products/prices for the self-serve
catalogue (Standard/Premium/Education, PLAN-DECISIONS.md) -- distinct from
scripts/stripe_setup.py's single volume-tiered per-site price, because these
are flat monthly prices, one per plan, not a tiered schedule.

    python scripts/stripe_plans_setup.py --check    # is the key working, what exists
    python scripts/stripe_plans_setup.py            # create the three (idempotent)

No --write / .env step: each price is given a lookup_key (`fig_plan_{plan}`)
at creation, and app/billing.py resolves the id from the live Stripe account
by that key at checkout time, not from an env var. Once created here, every
deployment that already has STRIPE_SECRET_KEY (Render included) can check
out against these prices with nothing further to configure -- see
app/billing.py:_plan_price_id and app/config.py's comment on why there's no
STRIPE_PRICE_STANDARD/_PREMIUM/_EDUCATION var to set.

Reads Account.PLAN_LIMITS as the one source of truth for price/label, so this
can never create a price that doesn't match what app/models.py enforces.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv                                    # noqa: E402

load_dotenv(ROOT / ".env")

import os                                                         # noqa: E402

from app.models import Account                                    # noqa: E402


def lookup_key(plan: str) -> str:
    return f"fig_plan_{plan}"


def main() -> int:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        print("STRIPE_SECRET_KEY is not set in .env")
        return 1
    try:
        import stripe
    except ImportError:
        print("pip install stripe")
        return 1
    stripe.api_key = key

    mode = "test" if "_test_" in key or key.startswith("sk_test") else "LIVE"
    print(f"Stripe key: {mode} mode")

    if "--check" in sys.argv:
        for plan, limits in Account.PLAN_LIMITS.items():
            existing = stripe.Price.list(lookup_keys=[lookup_key(plan)], limit=1)
            if existing["data"]:
                p = existing["data"][0].to_dict()
                print(f"  {plan}: {p['id']}  ${p['unit_amount'] / 100:.2f}/{p['recurring']['interval']}")
            else:
                print(f"  {plan}: not created yet (${limits['price_cents'] / 100:.0f}/month)")
        return 0

    for plan, limits in Account.PLAN_LIMITS.items():
        existing = stripe.Price.list(lookup_keys=[lookup_key(plan)], limit=1)
        if existing["data"]:
            price = existing["data"][0]
            print(f"{plan}: already exists: {price['id']}")
        else:
            product_name = f"FIG — {limits['label']}"
            products = [p for p in stripe.Product.list(limit=100)["data"]
                        if p["name"] == product_name]
            product = products[0] if products else stripe.Product.create(
                name=product_name,
                description=f"{limits['label']} plan — up to {limits['max_projects']} "
                            f"active project(s), {limits['scans_per_period']} scans/month.",
            )
            price = stripe.Price.create(
                product=product["id"],
                currency="usd",
                recurring={"interval": "month", "usage_type": "licensed"},
                unit_amount=limits["price_cents"],
                lookup_key=lookup_key(plan),
                nickname=limits["label"],
            )
            print(f"{plan}: created product {product['id']}, price {price['id']} "
                  f"(${limits['price_cents'] / 100:.0f}/month)")

    print("\nNothing to add to .env -- app/billing.py resolves each price by "
          "lookup_key at checkout time. Any deployment with STRIPE_SECRET_KEY "
          "set can check out against these prices already.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
