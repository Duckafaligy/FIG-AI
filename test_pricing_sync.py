"""The prices the website shows are the prices Stripe charges.

`frontend/lib/pricing.ts` mirrors `Account.TIERS`, which `scripts/stripe_setup.py`
builds the Stripe price from. Two copies of a price are how a customer ends up
reading one number and paying another, so this fails if they ever differ.
Also checks `legal.ts` against the backend's trial length. No network.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"

import re
import unittest
from pathlib import Path

from app.models import Account

FRONTEND = Path(__file__).parent / "frontend" / "lib"


def frontend_tiers() -> list[tuple[int, int]]:
    text = (FRONTEND / "pricing.ts").read_text(encoding="utf-8")
    block = text[text.index("export const TIERS"):text.index("];", text.index("export const TIERS"))]
    return [(int(a), int(b)) for a, b in re.findall(r"\[\s*(\d+)\s*,\s*(\d+)\s*\]", block)]


class PricingSyncTests(unittest.TestCase):
    def test_website_tiers_match_the_backend_and_stripe(self):
        self.assertEqual(frontend_tiers(), [tuple(t) for t in Account.TIERS])

    def test_the_trial_length_shown_matches_the_backend(self):
        text = (FRONTEND / "legal.ts").read_text(encoding="utf-8")
        shown = int(re.search(r"export const TRIAL_DAYS\s*=\s*(\d+)", text).group(1))
        self.assertEqual(shown, Account.TRIAL_DAYS)

    def test_the_frontend_rate_function_agrees_with_the_backend_for_every_size(self):
        tiers = frontend_tiers()

        def rate(n):
            r = tiers[0][1]
            for threshold, cents in tiers:
                if n >= threshold:
                    r = cents
            return r
        for n in (1, 2, 4, 5, 24, 25, 99, 100, 299, 300, 999, 1000, 5000):
            self.assertEqual(rate(n), Account.rate_for(n), f"at {n} sites")


if __name__ == "__main__":
    unittest.main()
