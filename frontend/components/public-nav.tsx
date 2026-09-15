"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Brand } from "./brand";

export function PublicNav({ active }: { active?: "pricing" }) {
  const [open, setOpen] = useState(false);
  const closeMenu = () => setOpen(false);

  return (
    <header className="public-nav-wrap">
      <nav className="public-nav page-shell" aria-label="Primary navigation">
        <Brand />
        <button className="mobile-nav-toggle" onClick={() => setOpen(!open)} aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className={`public-nav-links ${active === "pricing" ? "public-nav-links--pricing" : ""} ${open ? "is-open" : ""}`}>
          <Link href="/projects" onClick={closeMenu}>Demo</Link>
          {active === "pricing" && <Link href="/pricing" className="is-active" onClick={closeMenu}>Pricing</Link>}
          <Link href="/signin" onClick={closeMenu}>Sign in</Link>
          <Link className="button button--small" href="/signup" onClick={closeMenu}>Sign up</Link>
        </div>
      </nav>
    </header>
  );
}
