/**
 * What FIG costs, in one place.
 *
 * FIG is billed per active site per month, on *volume* tiers: the rate for
 * your total number of sites applies to every one of them (30 sites cost 30
 * times the 25-99 rate, not a blend). This mirrors `Account.TIERS` in
 * app/models.py, which is what the Stripe price is built from
 * (scripts/stripe_setup.py), so the page, the dashboard and the invoice agree.
 * `test_pricing_sync.py` fails if this list and the backend's ever differ.
 *
 * Each row is [minimum sites, cents per site per month].
 */
export const TIERS: ReadonlyArray<readonly [number, number]> = [
  [1, 2000],
  [5, 1500],
  [25, 1200],
  [100, 900],
  [300, 700],
  [1000, 500],
];

export function rateFor(sites: number): number {
  let rate = TIERS[0][1];
  for (const [threshold, cents] of TIERS) if (sites >= threshold) rate = cents;
  return rate;
}

export function monthlyCents(sites: number): number {
  return Math.max(0, Math.floor(sites)) * rateFor(sites);
}

export function dollars(cents: number): string {
  return `$${(cents / 100).toLocaleString("en-US", { minimumFractionDigits: cents % 100 ? 2 : 0, maximumFractionDigits: 2 })}`;
}

/** "1–4 sites", "5–24 sites", ... "1,000+ sites" */
export function tierRange(index: number): string {
  const from = TIERS[index][0];
  const next = TIERS[index + 1]?.[0];
  if (next === undefined) return `${from.toLocaleString("en-US")}+ sites`;
  return from === next - 1 ? `${from} site` : `${from}–${next - 1} sites`;
}
