import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/legal";
export default function sitemap(): MetadataRoute.Sitemap {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "1") return [];
  return ["/", "/pricing", "/privacy", "/terms", "/refunds", "/bot"].map(path => ({ url: `${SITE_URL}${path}` }));
}
