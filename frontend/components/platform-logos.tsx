import {
  siBigcommerce,
  siGoogleanalytics,
  siShopify,
  siWebflow,
  siWix,
  siWordpress
} from "simple-icons/icons";

const platforms = [siShopify, siWix, siWebflow, siWordpress, siBigcommerce, siGoogleanalytics];

export function PlatformLogos() {
  return (
    <div className="logo-row">
      {platforms.map((platform) => (
        <span className="platform-logo" key={platform.slug} title={platform.title}>
          <svg aria-label={platform.title} role="img" viewBox="0 0 24 24">
            <path d={platform.path} fill={`#${platform.hex}`} />
          </svg>
          <span>{platform.title}</span>
        </span>
      ))}
    </div>
  );
}
