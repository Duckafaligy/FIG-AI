import type { Metadata } from "next";
import { PageMotion } from "@/components/page-motion";
import "./globals.css";
import "./redesign.css";
import "./dashboard-redesign.css";
import "./dashboard-details.css";
import "./laptop-polish.css";
import "./visual-polish.css";
import "./interaction-polish.css";
import "./navigation-polish.css";
import "./library-workspace.css";

export const metadata: Metadata = {
  title: "FIG — Content that gets found",
  description: "Plan, create, optimize, and publish search-ready content with FIG."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><PageMotion />{children}</body>
    </html>
  );
}
