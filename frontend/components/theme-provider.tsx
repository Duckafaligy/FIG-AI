"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

// Infra-only: only shadcn-authored markup reacts to this today. The
// existing 22 hand-written CSS files' --ink/--surface/etc. tokens have
// no dark counterparts yet, so this deliberately does NOT enable system
// detection or default to dark -- see PLAN Phase 4.
export function ThemeProvider({ children, ...props }: ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
