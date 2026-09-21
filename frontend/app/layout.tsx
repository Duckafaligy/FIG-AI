import type { Metadata } from "next";
import { JsonLd } from "@/components/json-ld";
import { PageMotion } from "@/components/page-motion";
import { SITE_URL } from "@/lib/legal";
import { TIERS } from "@/lib/pricing";
import "./globals.css";
import "./redesign.css";
import "./dashboard-redesign.css";
import "./dashboard-details.css";
import "./laptop-polish.css";
import "./visual-polish.css";
import "./interaction-polish.css";
import "./navigation-polish.css";
import "./library-workspace.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "FIG — see what makes your site read as generic",
  description: "Paste a URL and FIG checks 19 patterns across design, structure, search and answers, then shows where each is and how to fix it. Free, no account.",
};

const siteData = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": `${SITE_URL}/#org`, name: "FIG", url: SITE_URL },
    { "@type": "WebSite", "@id": `${SITE_URL}/#site`, name: "FIG", url: SITE_URL, publisher: { "@id": `${SITE_URL}/#org` } },
    {
      "@type": "SoftwareApplication", name: "FIG", applicationCategory: "DeveloperApplication", operatingSystem: "Web",
      url: SITE_URL, description: "A self-check tool that scans a website's public pages for patterns commonly associated with generic design, and explains each with a fix.",
      offers: { "@type": "AggregateOffer", priceCurrency: "USD", lowPrice: String(Math.min(...TIERS.map((t) => t[1])) / 100), highPrice: String(Math.max(...TIERS.map((t) => t[1])) / 100), offerCount: TIERS.length },
    },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><JsonLd data={siteData} /><PageMotion />{children}</body>
    </html>
  );
}
