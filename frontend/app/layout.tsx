import type { Metadata } from "next";
import { Bricolage_Grotesque } from "next/font/google";
import { JsonLd } from "@/components/json-ld";
import { PageMotion } from "@/components/page-motion";
import { SITE_URL } from "@/lib/legal";
import "./globals.css";
import "./redesign.css";
import "./dashboard-redesign.css";
import "./dashboard-details.css";
import "./laptop-polish.css";
import "./visual-polish.css";
import "./interaction-polish.css";
import "./navigation-polish.css";
import "./library-workspace.css";
import "./launch-polish.css";
import "./publish-queue.css";
import "./draft-two.css";
import "./theme-dark-pages.css";
import "./home-neon.css";
import "./pricing-auth-neon.css";
import { ThemeProvider } from "@/components/theme-provider";

const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-bricolage", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "FIG — see what makes your site read as generic",
  description: "Paste a URL and FIG checks 21 patterns across design, structure, search and answers, then shows where each is and how to fix it. Free, no account.",
};

const siteData = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": `${SITE_URL}/#org`, name: "FIG", url: SITE_URL },
    { "@type": "WebSite", "@id": `${SITE_URL}/#site`, name: "FIG", url: SITE_URL, publisher: { "@id": `${SITE_URL}/#org` } },
    {
      "@type": "SoftwareApplication", name: "FIG", applicationCategory: "DeveloperApplication", operatingSystem: "Web",
      url: SITE_URL, description: "A self-check tool that scans a website's public pages for patterns commonly associated with generic design, and explains each with a fix.",
    },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={bricolage.variable} suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
          <JsonLd data={siteData} />
          <PageMotion />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
