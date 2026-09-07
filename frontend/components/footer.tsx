// One row. No columns, no newsletter, no social icons, no sitemap.
export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="container-page flex flex-col items-center justify-between gap-3 py-10 sm:flex-row">
        <span className="text-small text-muted">© 2026 tellcheck</span>
        <div className="text-small flex items-center gap-2 text-muted">
          <a href="#" className="transition-colors hover:text-foreground">
            Privacy
          </a>
          <span aria-hidden>·</span>
          <a href="#" className="transition-colors hover:text-foreground">
            Terms
          </a>
          <span aria-hidden>·</span>
          <a href="#" className="transition-colors hover:text-foreground">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
