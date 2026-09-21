"use client";

import { useState } from "react";
import { TIERS, dollars, monthlyCents, rateFor } from "@/lib/pricing";

/**
 * "What would N sites cost?" using exactly the rule billing uses: the rate for
 * your total applies to every site (volume pricing, not graduated).
 */
export function PriceCalculator() {
  const [text, setText] = useState("12");
  const parsed = Number.parseInt(text, 10);
  const sites = Number.isFinite(parsed) ? Math.min(Math.max(parsed, 1), 100000) : 1;
  const rate = rateFor(sites);
  const next = TIERS.find(([threshold]) => threshold > sites);

  return (
    <div className="price-calc">
      <label htmlFor="calc-sites">How many sites?</label>
      <input id="calc-sites" inputMode="numeric" value={text} onChange={(event) => setText(event.target.value.replace(/[^0-9]/g, "").slice(0, 6))} aria-describedby="calc-result" />
      <p id="calc-result" role="status">
        <strong>{dollars(monthlyCents(sites))}</strong> per month
        <span>{sites.toLocaleString("en-US")} {sites === 1 ? "site" : "sites"} × {dollars(rate)}</span>
      </p>
      {next && <small>From {next[0].toLocaleString("en-US")} sites every site drops to {dollars(next[1])}.</small>}
    </div>
  );
}
