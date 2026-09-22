"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { Brand } from "./brand";

export function PublicNav({ active }: { active?: "pricing" }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const menuId = useId();
  const toggle = useRef<HTMLButtonElement>(null);
  useEffect(() => { setOpen(false); }, [pathname]);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setOpen(false); toggle.current?.focus(); }
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);
  const closeMenu = () => setOpen(false);

  return (
    <header className="public-nav-wrap">
      <nav className="public-nav page-shell" aria-label="Primary navigation">
        <Brand />
        <button ref={toggle} type="button" className="mobile-nav-toggle" onClick={() => setOpen(!open)} aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} aria-controls={menuId}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div id={menuId} className={`public-nav-links ${active === "pricing" ? "public-nav-links--pricing" : ""} ${open ? "is-open" : ""}`}>
          <div className="public-nav-discover">
          <Link href="/library" aria-current={pathname === "/library" ? "page" : undefined} onClick={closeMenu}>Library</Link>
          <Link href="/pricing" className={pathname === "/pricing" ? "is-active" : ""} aria-current={pathname === "/pricing" ? "page" : undefined} onClick={closeMenu}>Pricing</Link>
          </div><div className="public-nav-account">
          <Link href="/signin" aria-current={pathname === "/signin" ? "page" : undefined} onClick={closeMenu}>Sign in</Link>
          <Link className="button button--small" href="/signup" aria-current={pathname === "/signup" ? "page" : undefined} onClick={closeMenu}>Sign up</Link>
          </div>
        </div>
      </nav>
    </header>
  );
}
