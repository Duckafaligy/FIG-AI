"""Creates the Stripe product and price FIG bills against.

STRIPE_PRICE_ID is not something to look up — nothing has been created in the
Stripe account yet. This makes it, derived from Account.TIERS so the two can
never drift apart.

    python scripts/stripe_setup.py --check    # is the key working, what exists
    python scripts/stripe_setup.py            # create it, print the id
    python scripts/stripe_setup.py --write    # create it and write it to .env

The tiers are *volume* priced, not graduated: at 30 sites every site costs the
30-site rate, which is what app/models.py:Account.monthly_cents already
computes. Stripe's "graduated" mode would charge the first 4 at $20, the next
20 at $15 and so on, and the invoice would stop matching the dashboard.
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

PRODUCT_NAME = "FIG — site monitoring"
LOOKUP_KEY = "fig_per_site_monthly"


def tiers() -> list[dict]:
    """Account.TIERS is (min_sites, cents). Stripe wants upper bounds, so each
    tier runs up to one below the next threshold, and the last is open-ended."""
    rows = list(Account.TIERS)
    out = []
    for i, (_threshold, cents) in enumerate(rows):
        if i + 1 < len(rows):
            out.append({"up_to": rows[i + 1][0] - 1, "unit_amount": cents})
        else:
            out.append({"up_to": "inf", "unit_amount": cents})
    return out


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
        prices = stripe.Price.list(limit=20, active=True, expand=["data.product"])
        if not prices["data"]:
            print("No active prices in this account yet — run without --check to make one.")
        for p in prices["data"]:
            p = p.to_dict()   # Stripe objects are not dicts: .get() raises on them
            name = p["product"]["name"] if isinstance(p["product"], dict) else p["product"]
            rec = p.get("recurring") or {}
            print(f"  {p['id']}  {name}  "
                  f"{p.get('billing_scheme')}  {rec.get('interval') or 'one-off'}")
        return 0

    # Reuse rather than duplicating on a second run.
    existing = stripe.Price.list(lookup_keys=[LOOKUP_KEY], limit=1)
    if existing["data"]:
        price = existing["data"][0]
        print(f"Already exists: {price['id']}")
    else:
        products = [p for p in stripe.Product.list(limit=100)["data"]
                    if p["name"] == PRODUCT_NAME]
        product = products[0] if products else stripe.Product.create(
            name=PRODUCT_NAME,
            description="One website read for craft, structure, search and answers.",
        )
        price = stripe.Price.create(
            product=product["id"],
            currency="usd",
            recurring={"interval": "month", "usage_type": "licensed"},
            billing_scheme="tiered",
            tiers_mode="volume",
            tiers=tiers(),
            lookup_key=LOOKUP_KEY,
            nickname="Per site, volume tiers",
        )
        print(f"Created product {product['id']}")
        print(f"Created price   {price['id']}")

    for t in tiers():
        print(f"  up to {str(t['up_to']):>4} sites  ${t['unit_amount'] / 100:.2f} each")

    line = f"STRIPE_PRICE_ID={price['id']}"
    if "--write" in sys.argv:
        env = ROOT / ".env"
        text = env.read_text(encoding="utf-8")
        if "STRIPE_PRICE_ID=" in text:
            out = []
            for row in text.splitlines():
                stripped = row.lstrip("# ").strip()
                out.append(line if stripped.startswith("STRIPE_PRICE_ID=") else row)
            text = "\n".join(out) + "\n"
        else:
            text = text.rstrip() + f"\n{line}\n"
        env.write_text(text, encoding="utf-8")
        print(f"\nWrote {line} to .env")
    else:
        print(f"\nAdd this to .env:\n{line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
