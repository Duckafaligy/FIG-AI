"use client";

/**
 * URL field + attached CTA, styled as one search-bar unit.
 * Reused verbatim in the hero and the bottom CTA.
 */
export function UrlInput({
  buttonLabel = "Check a site free",
}: {
  buttonLabel?: string;
}) {
  return (
    <form
      className="flex w-full max-w-[520px] items-stretch"
      onSubmit={(e) => e.preventDefault()}
    >
      <label htmlFor="scan-url" className="sr-only">
        Site URL to check
      </label>
      <input
        id="scan-url"
        type="url"
        inputMode="url"
        autoComplete="off"
        spellCheck={false}
        placeholder="https://your-project.vercel.app"
        className="min-w-0 flex-1 rounded-l-md border border-r-0 border-border bg-surface px-4 py-3 font-mono text-[14px] text-foreground placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <button
        type="submit"
        className="shrink-0 rounded-r-md bg-accent px-4 py-3 text-[14px] font-medium text-background transition-opacity hover:opacity-90"
      >
        {buttonLabel}
      </button>
    </form>
  );
}
