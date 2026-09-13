"use client";

import { motion } from "framer-motion";
import { HeroBackground } from "./hero-background";
import { UrlInput } from "./url-input";
import { ScanCard } from "./scan-card";
import { Reveal } from "./reveal";

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      <HeroBackground />

      <div className="container-page relative grid grid-cols-1 items-center gap-14 pb-20 pt-36 md:grid-cols-[55fr_45fr] md:gap-12 md:pb-[120px] md:pt-44">
        {/* left column — deliberately left-aligned, never centered */}
        <div>
          <Reveal>
            <h1 className="text-hero text-foreground">
              See what makes
              <br />
              your site look
              <br />
              AI-generated.
            </h1>
          </Reveal>

          <Reveal delay={0.08}>
            <p className="text-body mt-5 max-w-[480px] text-muted">
              Paste any URL. Get a flag-by-flag breakdown of the patterns that
              read as generic — with a specific fix for each one.
            </p>
          </Reveal>

          <Reveal delay={0.16}>
            <div id="try" className="mt-10 scroll-mt-28">
              <UrlInput />
              <p className="text-small mt-3 text-muted">
                No account. First three checks free.
              </p>
            </div>
          </Reveal>
        </div>

        {/* right column — the product demo. One entrance animation, from the right. */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <ScanCard />
        </motion.div>
      </div>
    </section>
  );
}
