"""The prices the website shows are the prices Stripe charges.

`frontend/lib/pricing.ts` mirrors `Account.TIERS`, which `scripts/stripe_setup.py`
builds the Stripe price from. Two copies of a price are how a customer ends up
reading one number and paying another, so this fails if they ever differ.
Also checks `legal.ts` against the backend's trial length. No network.
"""
import os
os.environ["FIG_DATABASE_URL"] = "sqlite://"

import inspect
import re
import unittest
from pathlib import Path

from app.models import Account
from app.rules import checks

FRONTEND = Path(__file__).parent / "frontend" / "lib"
FRONTEND_APP = Path(__file__).parent / "frontend" / "app"


def frontend_tiers() -> list[tuple[int, int]]:
    text = (FRONTEND / "pricing.ts").read_text(encoding="utf-8")
    block = text[text.index("export const TIERS"):text.index("];", text.index("export const TIERS"))]
    return [(int(a), int(b)) for a, b in re.findall(r"\[\s*(\d+)\s*,\s*(\d+)\s*\]", block)]


class PricingSyncTests(unittest.TestCase):
    def test_website_tiers_match_the_backend_and_stripe(self):
        self.assertEqual(frontend_tiers(), [tuple(t) for t in Account.TIERS])

    def test_plan_prices_and_limits_shown_match_what_the_backend_enforces(self):
        text = (FRONTEND / "plans.ts").read_text(encoding="utf-8")
        shown = {m[0].lower(): (int(m[1]) * 100, int(m[2]), int(m[3])) for m in re.findall(
            r'name: "(\w+)", audience: "\w+", price: (\d+), projects: (\d+), scans: (\d+)', text)}
        real = {k: (v["price_cents"], v["max_projects"], v["scans_per_period"]) for k, v in Account.PLAN_LIMITS.items()}
        self.assertEqual(shown, real)

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

    def test_the_check_count_shown_publicly_matches_the_real_number_of_checks(self):
        """The TOTAL check count ("21 checks across/in four layers") is
        hardcoded as marketing copy in four places (signin, signup, two
        spots on the homepage) with no shared constant -- checked against
        real introspection rather than a second hand-maintained number, so
        this can't itself drift the way the copy it's checking already did
        once (this test's own addition bumped 19 -> 21 to catch it).

        The regex requires "four layers" adjacent to the number on purpose:
        the homepage also shows a genuinely different, smaller count for
        just the answers layer ("5 checks - what a model can quote and
        reach") -- a blanket "<N> checks" match would wrongly compare that
        against the site-wide total instead of its own real answers-layer
        count, which this test intentionally leaves unchecked rather than
        getting that comparison wrong."""
        # obj.__module__ check excludes check_section_order, imported here
        # from app.rules.sections as a helper -- the real per-page check is
        # check_section_order_flags, defined in this module, which calls it.
        real_count = sum(1 for name, obj in vars(checks).items()
                         if name.startswith("check_") and inspect.isfunction(obj)
                         and obj.__module__ == checks.__name__)
        # Only pages that still state the total; the simplified auth pages
        # (2026-09-26) deliberately dropped it.
        for path in ("page.tsx",):
            text = (FRONTEND_APP / path).read_text(encoding="utf-8")
            stripped = re.sub(r"<[^>]+>", " ", text)   # JSX tags can split "checks" from "across ..."
            found = re.findall(
                r"(\d+) checks?\s+(?:across|in)\s+(?:four layers|(?:design|craft), structure, search and answers)",
                stripped)
            self.assertTrue(found, f"no total-check-count copy found in {path}")
            for n in found:
                self.assertEqual(int(n), real_count,
                                 f"{path} says {n} checks, but app/rules/checks.py has {real_count}")


if __name__ == "__main__":
    unittest.main()
