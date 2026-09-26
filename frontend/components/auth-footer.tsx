import Link from "next/link";

export function AuthFooter() {
  return (
    <footer className="page-shell auth-simple-footer">
      <span>Your password goes straight to our sign-in provider and never touches FIG&rsquo;s servers.</span>
      <nav aria-label="Legal"><Link href="/privacy">Privacy policy</Link><Link href="/terms">Terms &amp; Conditions</Link><span>© {new Date().getFullYear()} FIG</span></nav>
    </footer>
  );
}
