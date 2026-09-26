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
  FileSearch,
  Layers3,
  ListChecks,
  Network,
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
  { icon: Activity, label: "Site score", value: "81", change: "+29" },
  { icon: ListChecks, label: "Open findings", value: "14", change: "-9" },
  { icon: FileSearch, label: "Pages read", value: "38", change: "last scan" },
];

const SCORES = [52, 55, 54, 61, 66, 64, 72, 77, 81];
const SCAN_DATES = ["Jul 6", "", "Jul 20", "", "Aug 3", "", "Aug 17", "", "Aug 31"];

function ScoreChart({ id }: { id: string }) {
  const w = 520, h = 190, left = 34, right = 22, top = 16, bottom = 26;
  const last = SCORES.length - 1;
  const x = (i: number) => left + (i * (w - left - right)) / last;
  const y = (v: number) => top + ((100 - v) / 60) * (h - top - bottom);
  const line = SCORES.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Sample site score rising from 52 to 81 across nine scans">
      <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#14c86b" stopOpacity=".26" /><stop offset="100%" stopColor="#14c86b" stopOpacity="0" /></linearGradient></defs>
      {[50, 75, 100].map(v => <g key={v}><line className="neon-score-grid" x1={left} x2={w - right} y1={y(v)} y2={y(v)} /><text className="neon-score-axis" x={left - 8} y={y(v) + 3} textAnchor="end">{v}</text></g>)}
      <path d={`${line} L${x(last)} ${h - bottom} L${left} ${h - bottom}Z`} fill={`url(#${id})`} />
      <path className="neon-score-line" d={line} />
      {SCORES.map((v, i) => <circle key={i} className={i === last ? "neon-score-dot neon-score-dot--last" : "neon-score-dot"} cx={x(i)} cy={y(v)} r={i === last ? 5 : 3} />)}
      <text className="neon-score-value" x={x(last) - 12} y={y(SCORES[last]) - 10} textAnchor="end">{SCORES[last]}</text>
      {SCAN_DATES.map((d, i) => d && <text key={i} className="neon-score-axis" x={x(i)} y={h - 6} textAnchor="middle">{d}</text>)}
    </svg>
  );
}

const capabilities = [
  { icon: FileSearch, title: "Read the whole signal", copy: "Content, structure, search, and answer-readiness in one view." },
  { icon: Layers3, title: "Find the next move", copy: "Turn scattered findings into a ranked, workable list." },
  { icon: Zap, title: "Keep the momentum", copy: "Plan, publish, and re-scan without losing context." },
  { icon: CalendarDays, title: "Run the content rhythm", copy: "Keep briefs, reviews, and publishing dates in one calendar." },
  { icon: ListChecks, title: "Make every fix actionable", copy: "Move from a useful signal to a clear next step." },
  { icon: Network, title: "Connect the source data", copy: "Bring performance context into the same working view." },
];

const WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
// May 2025 starts on a Thursday: three April days lead, one June day trails.
const CAL_DAYS = [
  ...[28, 29, 30].map(day => ({ day, muted: true })),
  ...Array.from({ length: 31 }, (_, i) => ({ day: i + 1, muted: false })),
  { day: 1, muted: true },
];
const UPCOMING = [
  { day: 5, chip: "Blog post", title: "Vitamin C guide", meta: "Blog post · High", tone: "muted" },
  { day: 7, chip: "Links", title: "Internal links audit", meta: "Optimization · Medium", tone: "green" },
  { day: 10, chip: "Required", title: "Post new blog", meta: "Required · Approval", tone: "green" },
  { day: 14, chip: "FAQ", title: "FAQ schema", meta: "Technical · Medium", tone: "ink" },
];

function ContentCalendar() {
  return (
    <div className="neon-cal" aria-label="Example content calendar">
      <div className="neon-cal-top"><strong>May 2025</strong><div className="neon-cal-nav" aria-hidden="true"><span>‹</span><span>›</span><b>Month</b></div></div>
      <div className="neon-cal-body">
        <div className="neon-cal-month">
          {WEEKDAYS.map(d => <span key={d} className="neon-cal-dow">{d}</span>)}
          {CAL_DAYS.map(({ day, muted }, i) => {
            const event = muted ? undefined : UPCOMING.find(u => u.day === day);
            return (
              <div key={i} className={`neon-cal-day${muted ? " is-muted" : ""}`}>
                <span>{day}</span>
                {event && <em className="neon-cal-chip"><i className={`tone-${event.tone}`} />{event.chip}</em>}
              </div>
            );
          })}
        </div>
        <div className="neon-cal-list">
          <strong>Upcoming</strong>
          {UPCOMING.map(u => <p key={u.day}><b>MAY {u.day}</b><span>{u.title}<small>{u.meta}</small></span><i className={`tone-${u.tone}`} /></p>)}
        </div>
      </div>
    </div>
  );
}

function OverviewSurface({ id }: { id: string }) {
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
          <div className="neon-panel-heading"><strong>Site score</strong><span>9 scans</span></div>
          <ScoreChart id={`${id}-fill`} />
        </div>
        <div className="neon-opportunities">
          <div className="neon-panel-heading"><strong>Next fixes</strong><span>3</span></div>
          <p><i /> Add meta descriptions <b>High</b></p>
          <p><i /> Fix a skipped heading level <b>Med</b></p>
          <p><i /> Answer common questions <b>Med</b></p>
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
          <div className="neon-hero-photo" aria-hidden="true"><Image src="https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=2000&q=80" alt="" fill priority sizes="100vw" /></div>
          <div className="page-shell neon-hero-grid">
            <div className="neon-hero-copy">
              <span className="neon-kicker"><Sparkles size={13} /> Content intelligence</span>
              <h1>Give your website <span>a clearer next move.</span></h1>
              <p>FIG runs 21 checks across four layers, then shows where each issue is and how to fix it.</p>
              <div id="scan" className="neon-scan-wrap"><FreeScanForm /></div>
              <div className="neon-hero-links"><Link href="/projects">Open workspace <ArrowUpRight size={15} /></Link><span><CircleCheck size={15} /> Free scan, no account</span></div>
            </div>
            <div className="neon-hero-panel"><OverviewSurface id="hero" /></div>
          </div>
        </section>

        <section className="neon-proof-band" aria-label="FIG platform highlights"><div className="page-shell"><span>Made for the team behind the website.</span><div><b>CONTENT</b><b>SEARCH</b><b>ANSWER-READINESS</b><b>WORKFLOW</b></div></div></section>

        <section className="neon-section neon-system-section">
          <div className="page-shell">
            <div className="neon-system-grid">
              <div className="neon-system-image"><Image src="https://images.unsplash.com/photo-1751200065687-a126e7c304da?auto=format&fit=crop&w=1200&q=86" alt="Moody desk setup with a computer monitor" fill sizes="(max-width: 760px) 100vw, 42vw" /><div className="neon-system-story"><span>THE FIG SYSTEM</span><h2>From signal<br />to strategy.</h2><p>See what is working, find what is missing, and get a plan to move forward.</p><Link className="button" href="/projects">Explore the product <ArrowUpRight size={15} /></Link></div></div>
              <div className="neon-system-product"><OverviewSurface id="system" /></div>
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
            <ContentCalendar />
          </div>
        </section>

        <section className="neon-connect-section" id="integrations"><div className="page-shell"><span>WORKS WITH YOUR STACK</span><div>{integrations.map(name => <article key={name}><IntegrationLogo name={name} /><b>{name}</b></article>)}</div></div></section>

        <section className="neon-editorial-section">
          <div className="page-shell neon-editorial-grid">
            <div className="neon-editorial-photo"><Image src="https://images.unsplash.com/photo-1777019075773-a231fa4e4534?auto=format&fit=crop&w=1200&q=86" alt="Creative workstation with monitor and photography equipment" fill sizes="(max-width: 760px) 100vw, 46vw" /></div>
            <div className="neon-editorial-copy"><span>FROM SCAN TO SHIP</span><h2>Make the work feel obvious.</h2><p>Start with a public URL. FIG organizes the signal, ranks the opportunity, and keeps the next decision visible.</p><ol><li><b>01</b><span>Scan your site</span><Check size={17} /></li><li><b>02</b><span>Choose the next move</span><Check size={17} /></li><li><b>03</b><span>Publish with context</span><Check size={17} /></li></ol></div>
          </div>
        </section>

        <section className="neon-cta-section"><div className="page-shell neon-cta-grid"><div><h2>What could your website do next?</h2></div><div className="neon-cta-actions"><Link className="button" href="/signin">Sign in <ArrowUpRight size={17} /></Link><Link className="secondary-button" href="/signup">Sign up <ArrowUpRight size={17} /></Link></div></div></section>

        <section className="neon-faq-section page-shell" id="faq"><div><h2>Quick answers.</h2></div><Faq items={faqItems} /></section>
      </main>
      <Footer />
    </div>
  );
}
