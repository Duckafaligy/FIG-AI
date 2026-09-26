import type { Metadata } from "next";
import { Footer } from "@/components/footer";
import { PublicNav } from "@/components/public-nav";
import { NeonCta } from "@/components/neon-cta";
import { PricingNeon } from "@/components/pricing-neon";

export const metadata: Metadata = {
  title: "Pricing - FIG",
  description: "Standard $49, Premium $99 and Education $19 per month. Every plan runs all 21 checks; plans differ in projects and scans per month.",
  alternates: { canonical: "/pricing" },
};


export default function PricingPage() {
  return (
    <div className="public-page pricing-page neon-home">
      <PublicNav active="pricing" />
      <main>
        <PricingNeon />
        <NeonCta />
      </main>
      <Footer />
    </div>
  );
}
