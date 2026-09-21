import {
  siBigcommerce,
  siShopify,
  siWebflow,
  siWix,
  siWordpress
} from "simple-icons/icons";

// Sites FIG can read, not integrations: it scans public HTML, so the platform
// doesn't matter. Only WordPress (approved fixes), Google Analytics and Search
// Console are actual connections, and the copy around this says so.
const platforms = [siShopify, siWix, siWebflow, siWordpress, siBigcommerce];

export function PlatformLogos() {
  return (
    <div className="logo-row platform-logo-row">
      {platforms.map((platform, index) => (
        <span className={`platform-logo${platform.slug === "wix" ? " platform-logo--wordmark" : ""}`} key={platform.slug} title={platform.title}>
          <svg aria-label={platform.title} role="img" viewBox="0 0 24 24">
            <path d={platform.path} fill={`#${platform.hex}`} />
          </svg>
          {platform.slug !== "wix" && <span>{platform.title}</span>}
          {index < platforms.length - 1 && <i className="platform-logo-divider" aria-hidden="true" />}
        </span>
      ))}
    </div>
  );
}
