import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { WhatItCatches } from "@/components/what-it-catches";
import { ExampleOutput } from "@/components/example-output";
import { Pricing } from "@/components/pricing";
import { Faq } from "@/components/faq";
import { BottomCta } from "@/components/bottom-cta";
import { Footer } from "@/components/footer";

export default function Page() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <WhatItCatches />
        <ExampleOutput />
        <Pricing />
        <Faq />
        <BottomCta />
      </main>
      <Footer />
    </>
  );
}
