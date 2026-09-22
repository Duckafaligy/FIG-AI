import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/legal";
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", ...(process.env.NEXT_PUBLIC_DEMO_MODE === "1" ? { disallow: "/" } : { allow: "/", disallow: ["/api/", "/oauth/", "/scan"] }) }, sitemap: `${SITE_URL}/sitemap.xml` };
}
