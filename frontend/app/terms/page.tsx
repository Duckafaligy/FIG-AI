import type { Metadata } from "next";
import Link from "next/link";
import { Callout, LegalPage, type LegalSection } from "@/components/legal-page";
import { OPERATOR, TRIAL_DAYS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Terms of Service — FIG",
  description: "The rules for using FIG: what it does, what you agree to, how billing works, and what each side is responsible for.",
  alternates: { canonical: "/terms" },
};

/**
 * A conventional SaaS terms structure (acceptance, eligibility, the service,
 * acceptable use, your content, fees, IP, warranties, liability, termination,
 * governing law) with FIG-specific parts written from how the product actually
 * works: scans are probabilistic reads of public pages, the product is a
 * self-check tool and not a way to police other people (CLAUDE.md's "ONE rule"),
 * and billing is per active site. Not legal advice; have it reviewed.
 */
const sections: LegalSection[] = [
  {
    id: "agreement",
    title: "Agreement, and who can use FIG",
    body: (
      <>
        <p>These terms are an agreement between you and <strong>{OPERATOR.name}</strong> (&ldquo;FIG&rdquo;, &ldquo;we&rdquo;) about your use of the FIG website and service. By creating an account, running a scan, or otherwise using FIG, you agree to them and to our <Link href="/privacy">Privacy Policy</Link>. If you do not agree, do not use FIG.</p>
        <p>You must be at least <strong>13</strong>. If you are under 18 (or the age of majority where you live), you may use FIG only with the permission of a parent or guardian, who is responsible for your use, including any payment. If you use FIG for an organisation, you confirm you have the authority to bind it.</p>
      </>
    ),
  },
  {
    id: "service",
    title: "What FIG is, and what it is not",
    body: (
      <>
        <p>FIG scans the public pages of a website and reports patterns that are <em>commonly associated</em> with generic or templated design, each with an explanation and a suggested fix. It also offers workspaces, a content queue, connections to services such as Google Analytics, Search Console and WordPress, and a public library of free scans.</p>
        <Callout>
          <p><strong>FIG is a self-check and learning tool.</strong> A finding is a probabilistic signal, not a fact and not a verdict. FIG cannot tell you that a person or a program wrote something, and it does not try to. Please do not treat its output as proof of anything about anyone.</p>
        </Callout>
        <p>We may change, add or remove features. Some features may be labelled beta or unavailable; where a feature is not built, the product says so.</p>
      </>
    ),
  },
  {
    id: "use",
    title: "Acceptable use",
    body: (
      <>
        <p>You agree not to:</p>
        <ul>
          <li><strong>Use FIG to accuse, investigate or discipline other people.</strong> That includes checking a classmate&rsquo;s, student&rsquo;s or employee&rsquo;s work to decide whether they used AI, for grading, plagiarism or academic-integrity enforcement, or to publish claims about a named person. FIG was built to help people improve their <em>own</em> work and will not be used as surveillance.</li>
          <li>Scan a site you have no reason to be reading, or use FIG to probe, attack, overload or gain unauthorised access to any system. FIG only reads public pages and respects <code>robots.txt</code>; do not try to get around either.</li>
          <li>Get around usage limits, rate limits, or the safety checks that stop FIG being pointed at private or internal addresses.</li>
          <li>Share your account or API keys, resell FIG without our written agreement, or copy, scrape or reverse engineer the service, including its rules and reference lists, beyond what the law allows.</li>
          <li>Upload or connect anything unlawful, or anything you have no right to use.</li>
          <li>Connect a website or account you do not own or have permission to change.</li>
        </ul>
        <p>We may limit, suspend or remove access that breaks these rules.</p>
      </>
    ),
  },
  {
    id: "results",
    title: "Results and your decisions",
    body: (
      <>
        <p>Scores, findings, explanations and suggested fixes are automated, can be wrong or incomplete, and are provided for information. Explanations are written with the help of an AI model and may contain mistakes. A scan cannot run JavaScript, so a page that only fills in after it loads may read as thinner than it is. You decide what to change, and you are responsible for the changes you make and approve. FIG is not legal, SEO, accessibility or professional advice, and we do not promise any ranking, traffic or business outcome.</p>
      </>
    ),
  },
  {
    id: "content",
    title: "Your content and connected services",
    body: (
      <>
        <p>You keep ownership of what you put into FIG, such as your drafts and project details. You give us a limited licence to host, process and display it, and to run scans on the sites you add, only to provide the service to you.</p>
        <p>When you connect a service (Google, WordPress), you confirm you are allowed to, and that the third party&rsquo;s own terms allow it. FIG applies a change to a connected site only after you approve it, and keeps a record of what it replaced so you can revert it. You are responsible for checking a change before you approve it. Disconnecting a service deletes the stored credential.</p>
      </>
    ),
  },
  {
    id: "library",
    title: "Free scans and the public library",
    body: (
      <p>Free scans need no account, but they are public by default: the scanned domain, its score and headline finding appear in the public library unless you choose to keep the scan anonymous. Only run a free scan of a site you are comfortable having listed, or tick the anonymous option. If you own a listed site and want its entry removed, email <strong>{OPERATOR.email}</strong>. Scans of projects in your signed-in workspace are private unless you turn on a shareable report.</p>
    ),
  },
  {
    id: "fees",
    title: "Subscriptions, fees and payment",
    body: (
      <>
        <p>New accounts get a free trial of <strong>{TRIAL_DAYS} days</strong>. We do not take a card at sign-up, so <strong>nothing is charged unless you start a subscription yourself</strong>. Once the trial ends, we may require a paid subscription to keep using workspace features, and we will tell you before that changes anything. Business and Education plans are listed on the <Link href="/pricing">pricing page</Link>. Plan inclusions and payment details are confirmed before purchase. Existing subscriptions retain their agreed billing terms unless a change is agreed with you.</p>
        <ul>
          <li><strong>Billing.</strong> Payments are handled by Stripe. Subscriptions renew automatically each month until you cancel, and are charged in advance to the payment method you provide. You authorise those charges.</li>
          <li><strong>Changing your number of sites</strong> during a billing period adjusts the amount you owe from that point, prorated, so you pay for what you use.</li>
          <li><strong>Price changes.</strong> We will give you at least 30 days&rsquo; notice before a price change affects you. You can cancel before it does.</li>
          <li><strong>Taxes.</strong> Prices exclude taxes unless shown otherwise. You are responsible for any applicable sales tax, VAT or GST.</li>
          <li><strong>Failed payments.</strong> If a payment fails, Stripe will retry. If it cannot be collected, we may suspend or end the subscription.</li>
          <li><strong>Cancelling and refunds</strong> are covered in our <Link href="/refunds">Refunds &amp; cancellation policy</Link>, which is part of these terms.</li>
        </ul>
      </>
    ),
  },
  {
    id: "availability",
    title: "Availability and changes to the service",
    body: (
      <p>We work to keep FIG running, but we do not promise it will always be available, uninterrupted or error-free, and we may pause it for maintenance. FIG is an early product, and we may change or discontinue parts of it. If we end the service as a whole, we will give you reasonable notice and a way to take your data with you.</p>
    ),
  },
  {
    id: "ip",
    title: "Our property, and your feedback",
    body: (
      <p>FIG, its software, design, rules, reference lists and text are ours or our licensors&rsquo; and are protected by law. Apart from the right to use FIG under these terms, you get no ownership of them. If you send us ideas or feedback, you let us use them freely, without owing you anything, though we will not publish your name without asking.</p>
    ),
  },
  {
    id: "termination",
    title: "Ending your use",
    body: (
      <p>You can stop using FIG and cancel at any time. We may suspend or end your access if you break these terms, if we must by law, or if your use puts the service or others at risk. We will try to tell you why, and where we reasonably can, give you a chance to fix it first. Sections that by their nature should survive (such as ownership, disclaimers, liability and governing law) survive the end of the agreement. You can ask us to delete your data as described in the Privacy Policy.</p>
    ),
  },
  {
    id: "warranty",
    title: "No warranties",
    body: (
      <p>FIG is provided <strong>&ldquo;as is&rdquo; and &ldquo;as available&rdquo;</strong>. To the fullest extent the law allows, we give no warranties, express or implied, including of merchantability, fitness for a particular purpose, accuracy, and non-infringement. We do not warrant that scans will find every issue, that findings will be correct, or that a fix will improve your site.</p>
    ),
  },
  {
    id: "liability",
    title: "Limits on our liability",
    body: (
      <>
        <p>To the fullest extent the law allows, FIG and the people behind it are not liable for indirect, incidental, special, consequential or punitive damages, or for lost profits, revenue, data or goodwill, arising from your use of FIG. Our total liability for any claim relating to FIG is limited to the greater of <strong>the amount you paid us in the 12 months before the claim, or CAD/USD 100</strong>.</p>
        <p>Nothing in these terms limits liability that cannot be limited by law, including for fraud, for death or personal injury caused by negligence, or your rights as a consumer under mandatory law where you live.</p>
      </>
    ),
  },
  {
    id: "indemnity",
    title: "If your use causes a problem",
    body: (
      <p>You are responsible for your use of FIG. If a claim is brought against us because you connected a site or account you had no right to, ran FIG against a system you had no permission to test, or broke these terms, you agree to cover our reasonable costs of dealing with it, to the extent the law allows. We will tell you promptly and let you help.</p>
    ),
  },
  {
    id: "law",
    title: "Governing law and disputes",
    body: (
      <>
        <p>These terms are governed by the laws of <strong>{OPERATOR.jurisdiction}</strong>, without regard to conflict-of-laws rules. Courts there have jurisdiction over disputes, except that if you are a consumer, you keep any right to bring a claim in the courts where you live and to rely on the mandatory consumer protections of your country.</p>
        <p>Before starting a formal dispute, please email us at <strong>{OPERATOR.email}</strong> and give us 30 days to sort it out. Most problems can be.</p>
      </>
    ),
  },
  {
    id: "general",
    title: "General",
    body: (
      <>
        <p><strong>Changes.</strong> We may update these terms. For changes that matter we will tell you, by email or in the product, at least 30 days before they apply to you; using FIG afterwards means you accept them. If you do not, cancel before then.</p>
        <p><strong>The rest.</strong> These terms, the Privacy Policy and the Refunds &amp; cancellation policy are the whole agreement between us. If a part is found unenforceable, the rest stays in force. Not enforcing a right is not giving it up. You may not transfer the agreement without our consent.</p>
        <p><strong>Contact.</strong> {OPERATOR.name}, {OPERATOR.address}, {OPERATOR.email}.</p>
      </>
    ),
  },
];

export default function TermsPage() {
  return (
    <LegalPage
      path="/terms"
      title="Terms of Service"
      intro={<p>These are the rules for using FIG, in plain language where we can manage it. The short version: use it to look at and improve your own work, be honest about what you connect, and remember its findings are informed guesses, not verdicts.</p>}
      sections={sections}
    />
  );
}
