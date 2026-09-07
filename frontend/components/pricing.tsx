import type { ReactNode } from "react";
import { Check } from "lucide-react";
import { Reveal } from "./reveal";

const learning = [
  "Check any public URL",
  "Results cached weekly per domain",
  "First 3 checks without an account",
  "History visible for 30 days",
];

const project = [
  "Everything in Learning",
  "Verify domain ownership (DNS TXT or meta tag)",
  "Daily automatic scheduled scans",
  "On-demand re-checks (10/mo included)",
  "Design drift alerts (coming soon)",
];

function Feature({ children }: { children: ReactNode }) {
  return (
    <li className="flex gap-2.5 text-[15px] text-foreground">
      <Check className="mt-1 h-3.5 w-3.5 shrink-0 text-muted" strokeWidth={2} />
      <span>{children}</span>
    </li>
  );
}

export function Pricing() {
  return (
    <section id="pricing" className="section scroll-mt-24">
      <div className="container-page">
        <Reveal>
          <h2 className="text-section text-foreground">Pricing</h2>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* Learning — free */}
          <Reveal>
            <div className="flex h-full flex-col rounded-lg border border-border bg-surface p-6 md:p-8">
              <h3 className="text-[15px] font-medium text-foreground">
                Learning
              </h3>
              <div className="mt-4 text-[32px] font-semibold leading-none text-foreground">
                Free
              </div>
              <p className="text-body mt-2 text-muted">For studying any site</p>

              <ul className="mt-6 space-y-3">
                {learning.map((f) => (
                  <Feature key={f}>{f}</Feature>
                ))}
              </ul>

              <a
                href="#try"
                className="mt-8 inline-flex items-center justify-center rounded-md border border-border px-5 py-3 text-[15px] font-medium text-foreground transition-colors hover:border-foreground md:mt-auto"
              >
                Start checking
              </a>
            </div>
          </Reveal>

          {/* Your project — paid. Accent border is the ONLY visual distinction. */}
          <Reveal delay={0.08}>
            <div
              className="flex h-full flex-col rounded-lg border bg-surface p-6 md:p-8"
              style={{ borderColor: "var(--accent)" }}
            >
              <h3 className="text-[15px] font-medium text-foreground">
                Your project
              </h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-[32px] font-semibold leading-none text-foreground">
                  $9
                </span>
                <span className="text-body text-muted">/mo</span>
              </div>
              <p className="text-body mt-2 text-muted">
                For monitoring your own site
              </p>

              <ul className="mt-6 space-y-3">
                {project.map((f) => (
                  <Feature key={f}>{f}</Feature>
                ))}
              </ul>

              <a
                href="#try"
                className="mt-auto inline-flex items-center justify-center rounded-md bg-accent px-5 py-3 text-[15px] font-medium text-background transition-opacity hover:opacity-90"
              >
                Start with 7-day trial
              </a>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
