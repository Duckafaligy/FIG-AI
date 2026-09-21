import type { Metadata } from "next";
import Link from "next/link";
import { Callout, LegalPage, LegalTable, type LegalSection } from "@/components/legal-page";
import { OPERATOR, SERVICE_PROVIDERS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Privacy Policy — FIG",
  description: "What FIG collects, why, who it is shared with, how long it is kept, and the rights you have over it.",
};

/**
 * Structure follows GDPR Art. 13 (identity, purposes and legal bases, recipients,
 * transfers, retention, rights, complaint), plus CCPA/CPRA's categories and
 * "we do not sell or share", PIPEDA's accountability and access, and Google's
 * API Services User Data Policy (the Limited Use statement in section 6 is
 * required wording). Every factual claim was checked against the code; the
 * comments name where, so it can be re-checked when the code changes.
 */
const sections: LegalSection[] = [
  {
    id: "who",
    title: "Who we are",
    body: (
      <>
        <p>FIG is a self-check tool. You give it a website, it looks at the public pages, and it tells you which patterns are commonly associated with generic, templated design, with an explanation and a suggested fix. This policy explains what personal information FIG handles to do that.</p>
        <p>The operator of FIG, and the &ldquo;controller&rdquo; of your personal information, is <strong>{OPERATOR.name}</strong> (&ldquo;FIG&rdquo;, &ldquo;we&rdquo;). You can reach us at <strong>{OPERATOR.email}</strong> or <strong>{OPERATOR.address}</strong>. Privacy questions and requests go to that email address.</p>
      </>
    ),
  },
  {
    id: "collect",
    title: "What we collect, and why",
    body: (
      <>
        <p>We collect only what the product needs. Here is all of it.</p>
        <LegalTable
          head={["What", "Where it comes from", "Why we need it"]}
          rows={[
            [<><strong>Account details</strong>: your email, your name, and your workspace name</>, "You, when you sign up", "To create and run your account and to contact you about it"],
            [<><strong>Your password</strong></>, "You, when you sign up or reset it", "Sign-in. It goes straight to our authentication provider (Supabase), which stores only a one-way hash. It never reaches FIG's own servers or logs."],
            [<><strong>Projects</strong>: the websites you add, and the results of scanning them</>, "You, and our scanner reading those sites' public pages", "To run scans and show you findings and history"],
            [<><strong>Content drafts</strong> you write or paste into the content queue</>, "You", "To save, score and organise them"],
            [<><strong>Connected services</strong>: a WordPress application password, or a Google access token, if you connect them</>, "You, when you connect a service", "To read reports or apply changes you approve. Stored encrypted; see section 7."],
            [<><strong>Google reports</strong> from Analytics and Search Console, if you connect them</>, "Google, on your behalf", "To show your own traffic and search data in your workspace. See section 6."],
            [<><strong>Billing details</strong>: a Stripe customer and subscription reference, and your plan and status</>, "Stripe", "To charge you and show your plan. Your card number is entered on Stripe's page and is never seen or stored by FIG."],
            [<><strong>Free scans</strong> (no account): the address you enter, and the result</>, "You", "To run the scan and to show it in the public library. See section 5."],
            [<><strong>Anti-abuse identifiers</strong> for free scans: a scrambled (hashed) form of your IP address and a random device ID kept in your browser</>, "Your browser and network", "To stop one person running unlimited scans, which cost real money. The raw IP address is not stored in the record."],
            [<><strong>Technical logs</strong>: IP address, browser type, the page requested, and errors</>, "Your browser, recorded by our hosting providers", "To keep the service secure, working and free of abuse"],
          ]}
        />
        <p>We do not ask for, and you should not put in your drafts or project details, sensitive information such as health details, government ID numbers, or financial account numbers. We do not run advertising or behavioural-tracking tools, and we do not build profiles of you for marketing.</p>
      </>
    ),
  },
  {
    id: "bases",
    title: "Our legal bases (GDPR / UK GDPR)",
    body: (
      <>
        <p>If you are in the European Economic Area or the United Kingdom, we rely on these bases:</p>
        <ul>
          <li><strong>Contract.</strong> Handling your account, projects, drafts and billing is necessary to provide the service you asked for.</li>
          <li><strong>Legitimate interests.</strong> Security, abuse prevention and rate limiting (including the hashed identifiers for free scans), and keeping the service reliable. We weigh this against your rights, and we collect the minimum needed.</li>
          <li><strong>Consent.</strong> When you connect Google Analytics, Search Console or a CMS. You can withdraw it at any time by disconnecting; see section 7.</li>
          <li><strong>Legal obligation.</strong> Keeping the tax and accounting records the law requires for payments.</li>
        </ul>
      </>
    ),
  },
  {
    id: "cookies",
    title: "Cookies and similar storage",
    body: (
      <>
        <p>FIG uses two small items, and both are strictly necessary for the service to work:</p>
        <ul>
          <li><code>fig_session</code>: a cookie that keeps you signed in. It is HttpOnly (page scripts cannot read it), sent only over HTTPS, and expires after 14 days or when you sign out.</li>
          <li><code>fig_free_scan_device</code>: a random ID in your browser&rsquo;s local storage, used only to apply the free-scan limit fairly. It contains no personal information.</li>
        </ul>
        <p>We do not use advertising, analytics or social-media tracking cookies or scripts, so there is no cookie banner to accept. Because these two items are essential, they do not require consent under the EU ePrivacy rules.</p>
      </>
    ),
  },
  {
    id: "public",
    title: "Free scans and the public library",
    body: (
      <>
        <p>You can run a free scan without an account. FIG reads the site&rsquo;s own <em>public</em> pages, and the result is saved. So that nobody pays for the same scan twice, a recent result for the same domain is reused.</p>
        <Callout>
          <p><strong>Free scans are public by default.</strong> The site&rsquo;s domain, its score and its headline finding appear in the public library at <Link href="/library">/library</Link>. Tick the option to keep a scan anonymous and the library shows &ldquo;an anonymous site&rdquo; instead.</p>
        </Callout>
        <p>Only a site&rsquo;s already-public homepage and pages are read. Scans of a project in a signed-in workspace are private unless you switch on the shareable report for that project. If you are the owner of a site and want its library entry removed, email us and we will remove it. See also <Link href="/bot">About FIGBot</Link>.</p>
      </>
    ),
  },
  {
    id: "google",
    title: "Google user data",
    body: (
      <>
        <p>If you choose to connect Google Analytics or Search Console, FIG asks Google for <strong>read-only</strong> access (the <code>analytics.readonly</code> and <code>webmasters.readonly</code> scopes). We use it only to fetch your own site&rsquo;s traffic, impressions, clicks and top search queries, and to show them to you in your workspace. Nothing is written back to your Google account.</p>
        <Callout>
          <p>FIG&rsquo;s use and transfer to any other app of information received from Google APIs will adhere to the <a href="https://developers.google.com/terms/api-services-user-data-policy" rel="noopener noreferrer">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>
        </Callout>
        <p>In line with those requirements:</p>
        <ul>
          <li>We use Google data only to provide and improve the features you see in your workspace. We do not use it for advertising, and we do not sell it.</li>
          <li>We do not transfer it to anyone else, except as needed to run the service (for example our hosting), to comply with the law, or with your consent.</li>
          <li>People at FIG do not read it, except with your consent, to investigate abuse or a security issue, or where the law requires.</li>
          <li>We do not use it to develop, improve or train generalised AI or machine-learning models. The only AI step in FIG sends a site&rsquo;s hostname and short descriptions and examples of scan findings, never Google data.</li>
        </ul>
        <p>You can revoke access at any time from Settings → Integrations in FIG, or at <a href="https://myaccount.google.com/permissions" rel="noopener noreferrer">myaccount.google.com/permissions</a>.</p>
      </>
    ),
  },
  {
    id: "connections",
    title: "Connected services and how they are protected",
    body: (
      <>
        <p>Credentials you connect (a WordPress application password, a Google token) are encrypted before they are stored, and the key is held separately from the database. They are used only to do what you connected them for. <strong>When you disconnect a service in Settings, FIG deletes the stored credential</strong>, not just the link to it. Replacing a credential deletes the old one.</p>
        <p>Changes to a connected site are never applied without you approving them, and each keeps a record of what it replaced so it can be reverted.</p>
        <p>All traffic uses HTTPS. No system is perfectly secure. If a breach affects your personal information, we will tell you and the relevant authorities as the law requires.</p>
      </>
    ),
  },
  {
    id: "ai",
    title: "How AI is used",
    body: (
      <>
        <p>FIG&rsquo;s detection is ordinary code that checks pages against fixed rules. It does not use AI to decide what is flagged. AI is used in one place only: turning already-found patterns into a plain-language explanation and suggested fix.</p>
        <p>For that step we send our AI provider (Anthropic) a small amount of structured text: the site&rsquo;s hostname, short descriptions of the patterns found, and the short examples the rules matched (for instance a stock phrase, a colour value or an icon name quoted from the page). <strong>We do not send whole pages, your content drafts, your account details, or Google data.</strong> Anthropic processes it on our behalf as a service provider under its own terms and privacy policy.</p>
        <p>We do not make decisions about you by automated means that have legal or similarly significant effects.</p>
      </>
    ),
  },
  {
    id: "sharing",
    title: "Who we share it with",
    body: (
      <>
        <p>We <strong>do not sell your personal information</strong> and we do not share it for cross-context behavioural advertising. We share it only with the service providers below, who process it for us and only to run FIG, and where the law requires it.</p>
        <LegalTable
          head={["Provider", "What it does for FIG", "What it receives"]}
          rows={SERVICE_PROVIDERS.map((p) => [<strong key={p.name}>{p.name}</strong>, p.role, p.data])}
        />
        <p>If FIG is ever sold or merged, personal information may transfer to the new owner, who would have to honour this policy. We will tell you first.</p>
      </>
    ),
  },
  {
    id: "transfers",
    title: "Where your information goes",
    body: (
      <p>Our providers run servers in several countries, including the United States, so your information may be processed outside the country where you live. Where the law requires a safeguard for that, we rely on the provider&rsquo;s standard contractual clauses or an equivalent recognised mechanism. Ask us if you want details.</p>
    ),
  },
  {
    id: "retention",
    title: "How long we keep it",
    body: (
      <>
        <ul>
          <li><strong>Account and workspace data:</strong> while your account is open. After a verified deletion request we delete it within 30 days, apart from what the law requires us to keep.</li>
          <li><strong>Projects and scan history:</strong> while your account is open, because history is part of the product. Removing a project stops monitoring and billing for it but keeps its history until you ask us to delete it.</li>
          <li><strong>Free scans and library entries:</strong> until you ask us to remove them. The hashed identifiers are stored with the record and used only for the free-scan limits.</li>
          <li><strong>Payment records:</strong> Stripe and we keep invoice and transaction records for as long as tax and accounting law requires, commonly several years.</li>
          <li><strong>Backups and logs:</strong> held by our providers on their own short schedules, after which they are overwritten.</li>
        </ul>
      </>
    ),
  },
  {
    id: "rights",
    title: "Your rights, and how to use them",
    body: (
      <>
        <p>Depending on where you live, you have some or all of these rights over your personal information:</p>
        <ul>
          <li>to <strong>know</strong> what we hold about you and to get a copy (access and portability);</li>
          <li>to have it <strong>corrected</strong> if it is wrong;</li>
          <li>to have it <strong>deleted</strong>;</li>
          <li>to <strong>object to</strong> or <strong>restrict</strong> some uses, and to <strong>withdraw consent</strong> you gave;</li>
          <li>not to be <strong>treated worse</strong> for using these rights.</li>
        </ul>
        <p>These come from laws including the GDPR and UK GDPR, the California CCPA/CPRA, and Canada&rsquo;s PIPEDA and provincial privacy laws. We give the same rights to everyone, wherever you live.</p>
        <p><strong>To use them, email {OPERATOR.email}</strong> from the address on your account (we may ask one or two questions to confirm it is you). We reply within 30 days. You can also change your workspace name and disconnect services yourself in Settings.</p>
        <p>If you are unhappy with how we handle a request, you can complain to your data protection authority, for example the Office of the Privacy Commissioner of Canada, your EU or UK regulator, or the California Attorney General. We would like the chance to fix it first.</p>
      </>
    ),
  },
  {
    id: "children",
    title: "Children and students",
    body: (
      <p>FIG is built for students and people learning to build websites, so we take this seriously. FIG is for people aged <strong>13 and over</strong>. We do not knowingly collect personal information from anyone under 13, and will delete it if we learn we have. If you are under 18 (or the age of majority where you live), use FIG only with a parent or guardian&rsquo;s permission. FIG is a self-check tool: it does not give teachers, schools or anyone else access to your results unless you choose to share a report yourself.</p>
    ),
  },
  {
    id: "changes",
    title: "Changes and contact",
    body: (
      <>
        <p>If we change this policy in a way that matters, we will update the date at the top and, for significant changes, tell you by email or in the product before it takes effect.</p>
        <p>Questions? <strong>{OPERATOR.email}</strong> · {OPERATOR.address}. Related: <Link href="/terms">Terms of Service</Link> and <Link href="/refunds">Refunds &amp; cancellation</Link>.</p>
      </>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <LegalPage
      path="/privacy"
      title="Privacy Policy"
      intro={<p>This policy is written to be read. It says what FIG collects, why, who else touches it, how long it stays, and what you can do about it. If anything here is unclear, ask us and we will fix the wording.</p>}
      sections={sections}
    />
  );
}
