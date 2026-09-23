import { siShopify, siWordpress, siWebflow, siWix, siGithub, siGoogleanalytics, siGooglesearchconsole, siSupabase, siAnthropic, siStripe } from "simple-icons/icons";
import type { SimpleIcon } from "simple-icons";

const logos: Record<string, SimpleIcon> = {
  Shopify: siShopify, WordPress: siWordpress, Webflow: siWebflow, Wix: siWix,
  GitHub: siGithub, "Google Analytics": siGoogleanalytics,
  "Google Search Console": siGooglesearchconsole, Supabase: siSupabase,
  Anthropic: siAnthropic, Stripe: siStripe,
};

export function IntegrationLogo({ name }: { name: string }) {
  if (name === "OpenAI") return <img src="/brands/openai.svg" alt="" width={25} height={25} aria-hidden="true" />;
  const logo = logos[name];
  if (!logo) return null;
  return <svg width="25" height="25" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d={logo.path} fill={`#${logo.hex}`} /></svg>;
}
