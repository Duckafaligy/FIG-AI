"use client";

const links = [
  { label: "How it works", href: "#how-it-works" },
  { label: "What it catches", href: "#what-it-catches" },
  { label: "Pricing", href: "#pricing" },
];

/**
 * Floating pill navbar — always expanded. Full nav links stay visible at
 * every scroll position on desktop; mobile (<768px) shows only the wordmark
 * and the "Try free" CTA.
 */
export function Navbar() {
  return (
    <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 px-4">
      <nav
        className="flex items-center gap-3 rounded-full py-2 pl-5 pr-2"
        style={{
          background: "rgba(20, 20, 20, 0.8)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.4)",
        }}
      >
        <a
          href="#top"
          className="text-[15px] font-semibold lowercase tracking-tight text-foreground"
        >
          tellcheck
        </a>

        {/* Nav links — desktop only, always shown. */}
        <div className="hidden items-center gap-4 md:flex">
          <span className="h-4 w-px bg-border" aria-hidden />
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-[14px] text-muted transition-colors hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </div>

        <a
          href="#try"
          className="rounded-md bg-accent px-3.5 py-1.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90"
        >
          Try free
        </a>
      </nav>
    </div>
  );
}
