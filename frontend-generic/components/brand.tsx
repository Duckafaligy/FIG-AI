import Link from "next/link";

export function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link className={`brand ${inverse ? "brand--inverse" : ""}`} href="/" aria-label="FIG home">
      FIG<span className="brand-dot">.</span>
    </Link>
  );
}
