import { UrlInput } from "./url-input";
import { Reveal } from "./reveal";

// A closing beat — centering is intentional here, unlike the content sections.
export function BottomCta() {
  return (
    <section className="section">
      <div className="container-page flex flex-col items-center text-center">
        <Reveal>
          <h2 className="text-section text-foreground">
            Paste a URL. See what it catches.
          </h2>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="mt-8 flex flex-col items-center">
            <UrlInput />
            <p className="text-small mt-3 text-muted">No account needed.</p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
