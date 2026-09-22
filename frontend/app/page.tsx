import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { FreeScanForm } from "@/components/free-scan-form";
import {
  BarChart3,
  Braces,
  Check,
  Eye,
  FileCheck2,
  FileText,
  Layers3,
  Link2,
  MessageSquareText,
  MoveRight,
  PenLine,
  Quote,
  Scale,
  Search,
  Upload,
} from "lucide-react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { JsonLd, faqJsonLd } from "@/components/json-ld";
import { PlatformLogos } from "@/components/platform-logos";
import { ProductLaptop } from "@/components/product-laptop";
import { PublicNav } from "@/components/public-nav";
import { TRIAL_DAYS } from "@/lib/legal";
import { PlanCatalogue } from "@/components/plan-catalogue";

export const metadata: Metadata = {
  title: "FIG — see what makes your site read as generic",
  description: "Paste a URL and FIG checks 19 patterns across design, structure, search and answers, then shows where each is and how to fix it. Free, no account.",
  alternates: { canonical: "/" },
};

/**
 * Everything on this page describes something FIG does today, and the numbers
 * are ones that can be checked: 19 checks in four layers (app/rules/checks.py),
 * a free scan of up to 6 pages with no account, prices from lib/pricing.ts
 * (held equal to the backend by test_pricing_sync.py). The old outcome stats and
 * customer quotes were invented, so they are gone rather than relabelled.
 */

const featureCards = [
  { icon: PenLine, tone: "violet", title: "Design and copy tells", copy: "Uniform cards, numbered labels, filler phrases, default colours, flat headings and overused icons, each with the evidence." },
  { icon: Layers3, tone: "blue", title: "Page structure", copy: "Sections out of a sensible order, missing or extra H1s, skipped heading levels and thin pages." },
  { icon: Search, tone: "indigo", title: "Search basics", copy: "Titles, meta descriptions, canonical links, language, image alt text and orphan pages: what a crawler can reach." },
  { icon: Quote, tone: "indigo", title: "Answer readiness", copy: "Structured data, Q&A blocks and specific claims: what a model could quote from your pages." },
  { icon: FileCheck2, tone: "green", title: "A fix for every finding", copy: "Each one says where it is, why it reads as generic, and one concrete change to make." },
  { icon: BarChart3, tone: "blue", title: "History and re-scans", copy: "Run it again after you change something and see what moved." },
  { icon: FileText, tone: "violet", title: "A content queue", copy: "Gaps become briefs. Paste a draft and it is scored on nine rules, then moves through your review." },
  { icon: Link2, tone: "amber", title: "Connect your tools", copy: "Google Analytics and Search Console, read-only, plus WordPress fixes that apply only when you approve them." },
];

const workflowSteps = [
  { icon: Link2, title: "Scan", copy: "Paste a public URL. Up to 6 pages free, no account." },
  { icon: FileText, title: "Read", copy: "See findings grouped by craft, structure, search and answers." },
  { icon: PenLine, title: "Fix", copy: "Every finding comes with a concrete change." },
  { icon: Check, title: "Approve", copy: "Connected WordPress fixes apply only when you say so." },
  { icon: BarChart3, title: "Re-scan", copy: "Run it again and compare the results." },
  { icon: Upload, title: "Share", copy: "Optionally turn on a public report link." },
];

const glance = [
  { icon: Search, value: "19", label: "checks, each a stated rule", tone: "purple" },
  { icon: Layers3, value: "4", label: "layers: craft, structure, search, answers", tone: "blue" },
  { icon: FileCheck2, value: "$0", label: "to scan a public site, no account", tone: "green" },
  { icon: Scale, value: "0", label: "accusations: findings are signals", tone: "amber" },
];

const audiences = [
  {
    title: "Students and learners",
    copy: "See what makes your project read as generic, and learn to fix it yourself.",
    image: "https://images.unsplash.com/photo-1758876021859-bd2371d8f0a2?auto=format&fit=crop&w=900&q=88",
    alt: "Woman working on a laptop and taking notes in a shared office",
    position: "center 45%"
  },
  {
    title: "Freelancers and small teams",
    copy: "Check a site before you hand it over, and share a report with the client.",
    image: "https://images.unsplash.com/photo-1758873268023-15a6e6d739ed?auto=format&fit=crop&w=900&q=88",
    alt: "Professional wearing glasses at an office desk with a laptop",
    position: "center 45%"
  },
  {
    title: "Agencies",
    copy: "Keep your website projects organized in one workspace.",
    image: "https://images.unsplash.com/photo-1758873268745-dd2cf0d677b5?auto=format&fit=crop&w=900&q=88",
    alt: "Colleagues collaborating around a computer in a shared workspace",
    position: "center 45%"
  }
];

const principles = [
  { icon: Scale, title: "Signals, not accusations", copy: "A finding says a pattern is commonly associated with generic design. FIG never claims a person or a program wrote something." },
  { icon: Eye, title: "Your results are yours", copy: "Nobody else sees your results unless you turn on a share link. There is no leaderboard and no admin view." },
  { icon: Check, title: "Nothing changes without you", copy: "FIG edits a connected site only after you approve each change, and every change can be reverted." },
];

const frequentlyAsked = [
  {
    question: "Do I need an account to try FIG?",
    answer: "No. Paste a public URL and FIG scans up to 6 pages for free. Free scans appear in the public library with the site's domain unless you tick the option to keep yours anonymous. An account adds history, more pages and connections."
  },
  {
    question: "What does FIG actually check?",
    answer: "19 checks in four layers: craft (how it reads), structure (what sits where), search (what a crawler reaches) and answers (what a model could quote). They are ordinary code with a stated rule. AI is used only to write the plain-language explanation of each finding."
  },
  {
    question: "Does FIG say my site was written by AI?",
    answer: "No. Findings are patterns commonly associated with generic, templated design, and they are informed guesses, not verdicts. FIG can't tell you who or what wrote a page, and our terms ask you not to use it to judge other people's work."
  },
  {
    question: "What can FIG change on my site?",
    answer: "Only title and heading fixes on a connected WordPress site, and only after you approve each one; every change can be reverted. Everything else is advice you apply yourself. FIG doesn't write your content or publish new posts."
  },
  {
    question: "Which platforms does it work with?",
    answer: "FIG reads any public website, whatever it is built with. Google Analytics and Search Console connect read-only, and WordPress connects for approved fixes. Other platform connections aren't built yet."
  },
  {
    question: "What does it cost?",
    answer: "Business plans are Standard at $49/month and Premium at $99/month, with Enterprise by enquiry. Education is $19/month; School Registered is by enquiry. Prices are in USD. See Pricing to contact us about a plan."
  },
];

function ProductPreviewCards() {
  return (
    <div className="platform-tour-cards" aria-label="Sample FIG workspace screens">
      <article className="platform-tour-card platform-tour-card--projects">
        <div className="tour-card-ui tour-card-ui--projects" aria-hidden="true">
          <div className="tour-project-content">
            <div className="tour-ui-heading"><b>All projects</b><span>1 project</span></div>
            <div className="tour-project-tile"><span className="tour-project-avatar">LV</span><div><b>LaunchVault.ca</b><small>AI learning & resources</small></div><Check size={9} /></div>
            <div className="tour-project-metrics"><span><strong>28</strong>Published</span><span><strong>4.2K</strong>Traffic</span><span><strong>84</strong>Impact score</span></div>
            <div className="tour-project-activity"><FileCheck2 size={9} /><span>AI agents guide · Ready for review</span></div>
          </div>
        </div>
        <h3>Your sites at a glance</h3>
        <p>Every site in one list, with its score and its top finding.</p>
      </article>
      <article className="platform-tour-card platform-tour-card--performance">
        <div className="tour-card-ui" aria-hidden="true">
          <div className="tour-ui-heading"><b>Content performance</b><span>Last 30 days</span></div>
          <div className="tour-mini-kpis"><div><small>Organic traffic</small><b>4.2K</b><em>↑ 18.7%</em></div><div><small>Impact score</small><b>84</b><em>↑ 6 points</em></div><div><small>Published</small><b>28</b><em>↑ 27%</em></div></div>
          <svg className="tour-mini-chart" viewBox="0 0 220 82" preserveAspectRatio="none">
            <path d="M0 69 C25 64 37 68 56 57 S89 55 108 43 S142 49 164 31 S198 30 220 16" fill="none" stroke="#6047ff" strokeWidth="3" />
            <path d="M0 76 C26 72 38 74 56 68 S89 63 108 57 S143 59 164 48 S199 44 220 36" fill="none" stroke="#2f80ed" strokeWidth="2.5" />
          </svg>
        </div>
        <h3>Search data beside your findings</h3>
        <p>Connect Search Console to see real traffic and queries next to what FIG found.</p>
      </article>
      <article className="platform-tour-card platform-tour-card--geo">
        <div className="tour-card-ui tour-card-ui--geo" aria-hidden="true">
          <div className="tour-ui-heading"><b>Answer readiness</b><span>LaunchVault.ca</span></div>
          <div className="tour-geo-content"><div className="tour-score-ring"><strong>78</strong><span>Answers score</span></div><div className="tour-geo-sources"><span>Structured data <b>✓</b></span><span>Q&A block <b>✓</b></span><span>Specific claims <b>!</b></span></div></div>
        </div>
        <h3>Answer readiness</h3>
        <p>Whether a model could quote your pages: structured data, Q&A and specifics.</p>
      </article>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="public-page public-home">
      <JsonLd data={faqJsonLd(frequentlyAsked)} />
      <PublicNav />
      <main>
        <section className="home-hero section-glow">
          <div className="home-hero-shape home-hero-shape--left" />
          <div className="home-hero-shape home-hero-shape--right" />
          <div className="page-shell home-hero-grid">
            <div className="home-hero-copy">
              <span className="eyebrow">Site self-check for SEO + GEO</span>
              <h1>Find what makes your site <span>read as generic</span></h1>
              <p>Paste a URL. FIG checks 19 patterns across design, structure, search and answer-readiness, then shows where each one is, why it matters and how to fix it.</p>
              <div id="scan"><FreeScanForm /></div>
              <div className="home-hero-actions">
                <Link className="button" href="/projects">Open workspace</Link>
                <Link className="secondary-button" href="/signup">Start free</Link>
              </div>
              <div className="home-hero-proof">
                <p>A self-check tool for the people who build the site. Findings are signals, never verdicts. Screens shown are sample data.</p>
              </div>
            </div>
            <div className="home-hero-product">
              <ProductLaptop variant="queue" />
            </div>
          </div>
        </section>

        <section className="home-integrations" id="integrations" aria-label="Sites FIG can read">
          <div className="page-shell">
            <span className="section-kicker">Reads any public site, whatever it is built with</span>
            <PlatformLogos />
          </div>
        </section>

        <section className="page-shell home-outcomes" aria-label="FIG at a glance">
          <span className="home-outcomes-label">FIG at a glance</span>
          {glance.map(({ icon: Icon, value, label, tone }) => (
            <article className={`home-outcome home-outcome--${tone}`} key={label}>
              <Icon size={20} />
              <strong>{value}</strong>
              <span>{label}</span>
            </article>
          ))}
        </section>

        <section className="section page-shell home-features" id="features">
          <div className="section-heading centered">
            <span className="section-kicker">What FIG checks</span>
            <h2>19 checks across four layers</h2>
            <p>Every check is ordinary code with a stated rule, so you can see exactly what triggers it. AI only writes the plain-language explanation.</p>
          </div>
          <div className="home-feature-grid">
            {featureCards.map(({ icon: Icon, tone, title, copy }) => (
              <article className={`home-feature-card home-feature-card--${tone}`} key={title}>
                <span className="home-feature-icon"><Icon size={21} /></span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section home-workflow" id="workflow">
          <div className="page-shell">
            <div className="section-heading centered">
              <span className="section-kicker">How FIG works</span>
              <h2>From a URL to a fixed page in six steps</h2>
              <p>No account is needed to start. Sign up when you want history and connections.</p>
            </div>
            <ol className="home-workflow-grid">
              {workflowSteps.map(({ icon: Icon, title, copy }, index) => (
                <li key={title}>
                  <span className="home-workflow-icon"><Icon size={20} /></span>
                  <div><small>{index + 1}</small><h3>{title}</h3></div>
                  <p>{copy}</p>
                  {index < workflowSteps.length - 1 && <MoveRight className="home-workflow-arrow" size={16} aria-hidden="true" />}
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section home-platform-tour">
          <div className="page-shell home-platform-tour-grid">
            <div className="home-platform-tour-copy">
              <span className="section-kicker">The workspace</span>
              <h2>One place for every site you check</h2>
              <p>See what needs attention and where to focus next. Sites, findings, history and a content queue live together. The screens here use sample data.</p>
              <Link href="/projects">Open your workspace <MoveRight size={15} /></Link>
            </div>
            <ProductPreviewCards />
          </div>
        </section>

        <section className="section home-geo-feature">
          <div className="page-shell home-geo-grid">
            <div className="home-geo-copy">
              <span className="eyebrow"><MessageSquareText size={13} />Answer-ready</span>
              <h2>Be found beyond Google</h2>
              <p>People increasingly get answers from a model, not a list of links. FIG checks whether yours could be quoted, next to the search basics.</p>
              <Link className="button" href="/projects">Explore your workspace</Link>
            </div>
            <div className="home-visibility-card">
              <div className="home-visibility-chart-panel">
                <div className="home-visibility-heading">
                  <div><strong>The answers layer</strong><small>3 checks · what a model can quote</small></div>
                </div>
                <p className="home-answers-copy">A page is easier to quote when it answers a question directly, says something specific, and tells machines what it is.</p>
              </div>
              <div className="home-visibility-sources">
                <span><Braces size={15} /><b>Structured data</b><strong>JSON-LD</strong></span>
                <span><MessageSquareText size={15} /><b>Question and answer block</b><strong>Q&amp;A</strong></span>
                <span><Search size={15} /><b>Specific, checkable claims</b><strong>Detail</strong></span>
              </div>
            </div>
          </div>
        </section>

        <section className="section page-shell home-audience" id="teams">
          <div className="home-audience-copy">
            <span className="section-kicker">Who it is for</span>
            <h2>Made for people who build websites</h2>
            <p>Whether you are learning, freelancing or running a client list, FIG keeps the next fix clear.</p>
          </div>
          <div className="home-audience-grid">
            {audiences.map((audience) => (
              <article key={audience.title}>
                <Image src={audience.image} width={900} height={700} alt={audience.alt} style={{ objectPosition: audience.position }} />
                <div><h3>{audience.title}</h3><p>{audience.copy}</p></div>
              </article>
            ))}
          </div>
        </section>

        <section className="section page-shell home-principles">
          <div className="home-principles-heading">
            <span className="section-kicker">How FIG behaves</span>
            <h2>A self-check tool, never a verdict</h2>
            <p>Three commitments we keep.</p>
          </div>
          <div className="home-principles-grid">
            {principles.map(({ icon: Icon, title, copy }) => (
              <article key={title}>
                <span className="home-feature-icon"><Icon size={21} /></span>
                <div><h3>{title}</h3><p>{copy}</p></div>
              </article>
            ))}
          </div>
        </section>

        <section className="section page-shell home-pricing-preview">
          <div className="home-pricing-heading">
            <div><span className="section-kicker">Business & education</span><h2>Find your next step with FIG</h2><p>For business owners improving their websites, and learners discovering how to build better ones.</p></div>
            <Link href="/pricing">View full pricing <MoveRight size={15} /></Link>
          </div>
          <PlanCatalogue />
        </section>

        <section className="section page-shell home-faq" id="faq">
          <div className="home-faq-heading"><span className="section-kicker">Frequently asked questions</span><h2>Everything you need to know</h2><p>Straight answers about what FIG does, and what it doesn&rsquo;t.</p></div>
          <Faq items={frequentlyAsked} />
        </section>

        <section className="page-shell home-cta">
          <div className="home-cta-copy"><span>Ready when you are</span><h2>Understand your website. Build with confidence.</h2><p>Run a free scan or create a workspace to keep your projects together.</p></div>
          <div className="home-cta-actions"><div><Link className="secondary-button secondary-button--light" href="/#scan">Scan a website</Link><Link className="button button--light" href="/signup">Create account</Link></div><small>A free scan needs no account.</small></div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
