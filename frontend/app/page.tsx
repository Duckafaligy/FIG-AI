import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import {
  Activity,
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronRight,
  CircleCheck,
  Eye,
  FileSearch,
  Layers3,
  ListChecks,
  Network,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";
import { FreeScanForm } from "@/components/free-scan-form";
import { JsonLd, faqJsonLd } from "@/components/json-ld";
import { IntegrationLogo } from "@/components/integration-logo";
import { PublicNav } from "@/components/public-nav";

export const metadata: Metadata = {
  title: "FIG - content intelligence for websites",
  description: "Scan a public website and turn its content, search, and answer-readiness signals into a clear next move.",
  alternates: { canonical: "/" },
};

const faqItems = [
  { question: "What does a free scan include?", answer: "A free scan checks up to six public pages and groups findings across craft, structure, search, and answer-readiness." },
  { question: "Can I connect my existing tools?", answer: "FIG can read public websites and supports read-only Google Analytics and Search Console connections. WordPress changes require your approval." },
  { question: "Do I need an account?", answer: "No. Start with a public URL. Create an account when you want saved history, project workspaces, and connections." },
  { question: "Can I keep my scan private?", answer: "Yes. Enable the anonymous option before you run the scan and it will not be listed in the public library." },
  { question: "Which integrations do you support?", answer: "FIG supports Google Analytics, Google Search Console, Shopify, Webflow, Wix, and WordPress workflows." },
];

const integrations = ["Google Analytics", "Google Search Console", "Shopify", "Webflow", "Wix", "WordPress"];

const signals = [
  { icon: Search, label: "Search", value: "48.2K", change: "+18%" },
  { icon: Eye, label: "Visibility", value: "62%", change: "+11%" },
  { icon: Activity, label: "Impact", value: "84", change: "+16" },
];

const capabilities = [
  { icon: FileSearch, title: "Read the whole signal", copy: "Content, structure, search, and answer-readiness in one view." },
  { icon: Layers3, title: "Find the next move", copy: "Turn scattered findings into a ranked, workable list." },
  { icon: Zap, title: "Keep the momentum", copy: "Plan, publish, and re-scan without losing context." },
  { icon: CalendarDays, title: "Run the content rhythm", copy: "Keep briefs, reviews, and publishing dates in one calendar." },
  { icon: ListChecks, title: "Make every fix actionable", copy: "Move from a useful signal to a clear next step." },
  { icon: Network, title: "Connect the source data", copy: "Bring performance context into the same working view." },
];

function OverviewSurface() {
  return (
    <div className="neon-overview" aria-label="Example FIG project overview">
      <div className="neon-overview-bar">
        <span className="neon-overview-mark">E</span>
        <div><strong>Everglow Store</strong><small>Sample data, not a real customer</small></div>
        <span className="neon-live"><i /> Live</span>
      </div>
      <div className="neon-overview-metrics">
        {signals.map(({ icon: Icon, label, value, change }) => (
          <div key={label}>
            <Icon size={15} />
            <small>{label}</small>
            <strong>{value}</strong>
            <em>{change}</em>
          </div>
        ))}
      </div>
      <div className="neon-overview-main">
        <div className="neon-chart-panel">
          <div className="neon-panel-heading"><strong>Performance</strong><span>28 days</span></div>
          <svg viewBox="0 0 520 180" role="img" aria-label="Rising organic traffic and impressions chart">
            <defs><linearGradient id="signalFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#b7ff45" stopOpacity=".36" /><stop offset="100%" stopColor="#b7ff45" stopOpacity="0" /></linearGradient></defs>
            <path className="neon-chart-grid" d="M0 33H520M0 78H520M0 123H520M0 168H520M52 0V180M156 0V180M260 0V180M364 0V180M468 0V180" />
            <path d="M0 158 C35 149 52 143 76 147 S114 121 140 129 S180 115 210 117 S244 96 278 102 S313 75 341 83 S380 60 408 66 S449 38 476 47 S503 26 520 18 V180 H0Z" fill="url(#signalFill)" />
            <path className="neon-chart-line" d="M0 158 C35 149 52 143 76 147 S114 121 140 129 S180 115 210 117 S244 96 278 102 S313 75 341 83 S380 60 408 66 S449 38 476 47 S503 26 520 18" />
            <path className="neon-chart-line neon-chart-line--muted" d="M0 170 C42 165 61 157 88 160 S133 146 160 151 S211 128 235 135 S287 120 310 127 S368 109 389 113 S430 89 457 96 S500 78 520 72" />
          </svg>
        </div>
        <div className="neon-opportunities">
          <div className="neon-panel-heading"><strong>Next moves</strong><span>04</span></div>
          <p><i /> Vitamin C serum <b>High</b></p>
          <p><i /> Improve internal links <b>Med</b></p>
          <p><i /> Add FAQ schema <b>Med</b></p>
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="public-page public-home neon-home">
      <JsonLd data={faqJsonLd(faqItems)} />
      <PublicNav />
      <main>
        <section className="neon-hero">
          <div className="page-shell neon-hero-grid">
            <div className="neon-hero-copy">
              <span className="neon-kicker"><Sparkles size={13} /> Content intelligence</span>
              <h1>Give your website <span>a clearer next move.</span></h1>
              <p>FIG reads the signals across your content, search, and answer-readiness - then turns them into a focused plan.</p>
              <div id="scan" className="neon-scan-wrap"><FreeScanForm /></div>
              <div className="neon-hero-links"><Link href="/projects">Open workspace <ArrowUpRight size={15} /></Link><span><CircleCheck size={15} /> Free scan, no account</span></div>
            </div>
            <div className="neon-hero-visual">
              <div className="neon-photo-frame"><Image src="https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=88" alt="Modern industrial workspace with a conference table" fill priority sizes="(max-width: 900px) 100vw, 52vw" /></div>
              <div className="neon-photo-veil" />
              <div className="neon-hero-surface"><OverviewSurface /></div>
              <div className="neon-corner-label">FIG / 01</div>
            </div>
          </div>
        </section>

        <section className="neon-proof-band" aria-label="FIG platform highlights"><div className="page-shell"><span>Made for the team behind the website.</span><div><b>CONTENT</b><b>SEARCH</b><b>ANSWER-READINESS</b><b>WORKFLOW</b></div></div></section>

        <section className="neon-section neon-system-section">
          <div className="page-shell">
            <div className="neon-system-grid">
              <div className="neon-system-image"><Image src="https://images.unsplash.com/photo-1751200065687-a126e7c304da?auto=format&fit=crop&w=1200&q=86" alt="Moody desk setup with a computer monitor" fill sizes="(max-width: 760px) 100vw, 42vw" /><div className="neon-system-story"><span>THE FIG SYSTEM</span><h2>From signal<br />to strategy.</h2><p>See what is working, find what is missing, and get a plan to move forward.</p><Link className="button" href="/projects">Explore the product <ArrowUpRight size={15} /></Link></div></div>
              <div className="neon-system-product"><OverviewSurface /></div>
            </div>
          </div>
        </section>

        <section className="neon-section neon-capability-section">
          <div className="page-shell">
            <div className="neon-section-heading neon-section-heading--row"><div><span>BUILT FOR CLARITY</span><h2>Focus without the fog.</h2></div><Link href="/projects">Explore the workspace <ArrowUpRight size={16} /></Link></div>
            <div className="neon-capability-grid">
              {capabilities.map(({ icon: Icon, title, copy }) => <article key={title}><div><Icon size={21} /></div><h3>{title}</h3><p>{copy}</p><ChevronRight size={18} /></article>)}
            </div>
          </div>
        </section>

        <section className="neon-workbench-section">
          <div className="page-shell neon-workbench-grid">
            <div className="neon-workbench-copy"><span>CONTENT RHYTHM</span><h2>Keep the next piece of work in view.</h2><p>Plan from the opportunity, not a blank page. FIG keeps the signal, the brief, and the publishing moment connected.</p><Link href="/projects">Open content calendar <ArrowUpRight size={16} /></Link></div>
            <div className="neon-calendar-surface" aria-label="Example content calendar">
              <div className="neon-calendar-top"><strong>May 2025</strong><div><span>‹</span><span>›</span><b>Today</b></div></div>
              <div className="neon-calendar-layout">
                <div className="neon-calendar-grid"><span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span><span>28</span><span>29</span><span>30</span><span>1</span><span>2</span><span>3</span><span>4</span><span>5<i /></span><span>6</span><span>7<i /></span><span>8</span><span>9<i /></span><span>10</span><span>11</span><span>12</span><span>13</span><span>14<i /></span><span>15</span><span>16<i /></span><span>17</span><span>18</span><span>19</span><span>20</span><span>21<i /></span><span>22</span><span>23</span><span>24</span><span>25</span></div>
                <div className="neon-calendar-list"><strong>Upcoming</strong><p><b>MAY<br />05</b><span>Vitamin C guide<small>Blog post · High</small></span><i /></p><p><b>MAY<br />07</b><span>Internal links audit<small>Optimization · Medium</small></span><i /></p><p><b>MAY<br />14</b><span>FAQ schema<small>Technical · Medium</small></span><i /></p><p><b>MAY<br />16</b><span>Skincare routine<small>Blog post · Medium</small></span><i /></p></div>
              </div>
            </div>
          </div>
        </section>

        <section className="neon-connect-section" id="integrations"><div className="page-shell"><span>WORKS WITH YOUR STACK</span><div>{integrations.map(name => <article key={name}><IntegrationLogo name={name} /><b>{name}</b></article>)}</div></div></section>

        <section className="neon-editorial-section">
          <div className="page-shell neon-editorial-grid">
            <div className="neon-editorial-photo"><Image src="https://images.unsplash.com/photo-1777019075773-a231fa4e4534?auto=format&fit=crop&w=1200&q=86" alt="Creative workstation with monitor and photography equipment" fill sizes="(max-width: 760px) 100vw, 46vw" /></div>
            <div className="neon-editorial-copy"><span>FROM SCAN TO SHIP</span><h2>Make the work feel obvious.</h2><p>Start with a public URL. FIG organizes the signal, ranks the opportunity, and keeps the next decision visible.</p><ol><li><b>01</b><span>Scan your site</span><Check size={17} /></li><li><b>02</b><span>Choose the next move</span><Check size={17} /></li><li><b>03</b><span>Publish with context</span><Check size={17} /></li></ol></div>
          </div>
        </section>

        <section className="neon-cta-section"><div className="page-shell neon-cta-grid"><div><span>START WITH A URL</span><h2>What could your website do next?</h2></div><div className="neon-cta-actions"><Link className="button" href="/#scan">Scan a website <ArrowUpRight size={17} /></Link><Link className="secondary-button" href="/signup">Create workspace</Link></div></div></section>

        <section className="neon-faq-section page-shell" id="faq"><div><span>GOOD QUESTIONS</span><h2>Quick answers.</h2></div><Faq items={faqItems} /></section>
      </main>
      <Footer />
    </div>
  );
}
