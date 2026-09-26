import type { MetadataRoute } from "next";
import { LAST_UPDATED, SITE_URL } from "@/lib/legal";

// Only pages meant to be found. /library, /signup, /signin, /report/* and the
// app send X-Robots-Tag: noindex (next.config.mjs), so listing them here would
// contradict that; robots.txt deliberately doesn't block them either, or
// crawlers could never read the noindex.
export default function sitemap(): MetadataRoute.Sitemap {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "1") return [];
  const legalUpdated = new Date(LAST_UPDATED);
  return [
    { url: `${SITE_URL}/` },
    { url: `${SITE_URL}/pricing` },
    ...["/privacy", "/terms", "/refunds", "/bot"].map(path => ({ url: `${SITE_URL}${path}`, lastModified: legalUpdated })),
  ];
}
