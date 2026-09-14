"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Brand } from "./brand";

export function PublicNav({ active }: { active?: "pricing" }) {
  const [open, setOpen] = useState(false);

  return (
    <header className="public-nav-wrap">
      <nav className="public-nav page-shell" aria-label="Primary navigation">
        <Brand />
        <button className="mobile-nav-toggle" onClick={() => setOpen(!open)} aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className={`public-nav-links ${open ? "is-open" : ""}`}>
          <Link href="/pricing" className={active === "pricing" ? "is-active" : ""}>Pricing</Link>
          <Link href="/app">Demo</Link>
          <Link href="/signin">Sign in</Link>
          <Link className="button button--small" href="/signup">Start free</Link>
        </div>
      </nav>
    </header>
  );
}
