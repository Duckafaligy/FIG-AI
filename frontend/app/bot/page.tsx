import type { Metadata } from "next";
import Link from "next/link";
import { Callout, LegalPage, LegalTable, type LegalSection } from "@/components/legal-page";
import { OPERATOR } from "@/lib/legal";

export const metadata: Metadata = {
  title: "About FIGBot — FIG",
  description: "What FIGBot is, what it reads, how politely it behaves, and how to block it or ask us to remove your site.",
  alternates: { canonical: "/bot" },
};

/**
 * This is where a crawler's user agent points, so it is written for a site
 * owner who found "FIGBot" in their logs and wants to know who it is. Every
 * number is the real default in app/config.py (CRAWL_DELAY, MAX_PAGES_PER_SCAN,
 * PUBLIC_SCAN_MAX_PAGES, REQUEST_TIMEOUT, MAX_REDIRECTS) and app/scraper.py;
 * update this page if those change.
 */
const sections: LegalSection[] = [
  {
    id: "what",
    title: "What FIGBot is",
    body: (
      <>
        <p>FIGBot is the reader behind <Link href="/">FIG</Link>, a self-check tool that helps people see which design and copy patterns on their <em>own</em> website are commonly associated with generic, templated output. It appears in your server logs with this user agent:</p>
        <p><code>FIGBot/0.2 (+https://&hellip;/bot; site self-check and structure scanner)</code></p>
        <Callout>
          <p><strong>FIGBot never browses the web on its own.</strong> It fetches a site only when a person asks FIG to scan it, or when a site&rsquo;s verified owner has switched on recurring checks. It does not follow links across the internet and it is not building a search index or a dataset.</p>
        </Callout>
      </>
    ),
  },
  {
    id: "behaviour",
    title: "How it behaves",
    body: (
      <>
        <LegalTable
          head={["Behaviour", "Detail"]}
          rows={[
            ["Reads only what any visitor could", "Public pages over plain HTTP(S) on the standard ports. It does not log in, submit forms, or execute JavaScript."],
            ["Respects robots.txt", <>It reads <code>/robots.txt</code> first and follows it as specified in RFC 9309, identifying itself as <code>FIGBot</code>. A page it is disallowed from is not fetched.</>],
            ["Goes slowly", "One request at a time per site, with about 0.8 seconds between requests."],
            ["Stays small", "Up to 40 pages per scan (6 for a free scan), each capped at 5 MB, with a 12-second timeout and at most 5 redirects."],
            ["Stays public", "It refuses private, internal and non-public addresses, and re-checks the destination on every redirect."],
          ]}
        />
      </>
    ),
  },
  {
    id: "block",
    title: "How to block it",
    body: (
      <>
        <p>Add this to your <code>robots.txt</code> and FIGBot will not read any page on your site:</p>
        <p><code>User-agent: FIGBot</code><br /><code>Disallow: /</code></p>
        <p>To allow it on most of your site but keep it out of one part, disallow just that path instead (for example <code>Disallow: /private/</code>). Changes take effect the next time FIGBot checks your <code>robots.txt</code>, which is at the start of every scan.</p>
        <p>You can also block the user agent at your server or firewall. If you do, FIG will report that the site could not be read, rather than trying another way in.</p>
      </>
    ),
  },
  {
    id: "library",
    title: "If your site is in the public library",
    body: (
      <>
        <p>Anyone can run a free scan of a public site, and free scans appear in the <Link href="/library">public library</Link> by default. If you own a site and you would like its entry removed, or would like FIG to stop scanning it, email <strong>{OPERATOR.email}</strong> from an address at your domain, or tell us which domain and how we can confirm it is yours. We will remove it. Blocking FIGBot in <code>robots.txt</code> also stops any new scan of it.</p>
        <p>FIG&rsquo;s findings are informed guesses about design patterns, never a statement that anyone or anything wrote your site. See the <Link href="/terms">Terms of Service</Link> and <Link href="/privacy">Privacy Policy</Link>.</p>
      </>
    ),
  },
  {
    id: "contact",
    title: "Contact",
    body: (
      <p>Something wrong, too fast, or not respecting your <code>robots.txt</code>? Tell us: <strong>{OPERATOR.email}</strong>, {OPERATOR.address}. Please include the time of the request and your site&rsquo;s domain, and we will look into it.</p>
    ),
  },
];

export default function BotPage() {
  return (
    <LegalPage
      path="/bot"
      title="About FIGBot"
      intro={<p>You are probably here because &ldquo;FIGBot&rdquo; showed up in your logs. Here is what it is, exactly how it behaves, and how to stop it in one line.</p>}
      sections={sections}
    />
  );
}
