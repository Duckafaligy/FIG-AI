"""Deterministic pattern detection — $0 to run, no LLM calls.

The reference lists below (KNOWN_DEFAULT_COLORS, GENERIC_COPY_PHRASES,
OVERUSED_ICON_NAMES) are the actual differentiating IP of this product, more
than any individual check function. Grow and tune them against real
AI-generated sites (Lovable/v0/Bolt output) vs. real hand-crafted ones —
see "Not yet wired up" #5 in CLAUDE.md.

Checks are grouped into the four layers the product reports on:

    craft      how the page reads — the slop layer
    structure  whether the sections are in an order that makes sense
    search     whether a crawler can reach and understand it
    answers    whether a model has anything specific it can quote back

Every Flag carries its own `why` and `fix`. ai_explain may rewrite them for a
specific page, but nothing here depends on an LLM being available.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from app.rules.sections import check_section_order
from app.scraper import PageSignal

# --- Reference lists ---------------------------------------------------

# Unmodified defaults from popular component libraries / AI page builders.
# Multiple names intentionally map to the same hex — several libraries
# ship near-identical purple/indigo/violet defaults, so a page can trip
# this by matching any one of them.
KNOWN_DEFAULT_COLORS: dict[str, str] = {
    "tailwind-indigo-600": "#4F46E5",
    "tailwind-indigo-500": "#6366F1",
    "tailwind-violet-600": "#7C3AED",
    "tailwind-violet-500": "#8B5CF6",
    "tailwind-purple-600": "#9333EA",
    "tailwind-blue-600": "#2563EB",
    "tailwind-blue-500": "#3B82F6",
    "tailwind-slate-900": "#0F172A",
    "tailwind-slate-50": "#F8FAFC",
    "tailwind-emerald-500": "#10B981",
    "tailwind-pink-500": "#EC4899",
    "shadcn-primary": "#18181B",
    "shadcn-ring": "#A1A1AA",
    "generic-gradient-blue": "#3B82F6",
    # Added 2026-09-17: each of these is >12 RGB-distance from every entry
    # above (checked against COLOR_MATCH_THRESHOLD), so they widen real
    # coverage rather than padding the list with near-duplicates that would
    # already match. Red/amber/cyan/sky/rose/teal are Tailwind's other
    # accent hues, left unmodified just as often as the indigo/violet/blue
    # ones already here.
    "tailwind-red-500": "#EF4444",
    "tailwind-amber-500": "#F59E0B",
    "tailwind-cyan-500": "#06B6D4",
    "tailwind-sky-500": "#0EA5E9",
    "tailwind-rose-500": "#F43F5E",
    "tailwind-teal-500": "#14B8A6",
    # Vercel's own brand blue, ubiquitous in v0.dev-generated output
    # specifically (v0 is a Vercel product) -- distinct from the generic
    # Tailwind blues above by a wide margin.
    "vercel-geist-blue": "#0070F3",
}

GENERIC_COPY_PHRASES: list[str] = [
    "elevate your",
    "unlock your",
    "unlock the power of",
    "supercharge your",
    "streamline your",
    "revolutionize the way",
    "take it to the next level",
    "seamlessly integrate",
    "effortlessly manage",
    "built for speed and scale",
    "get started in minutes",
    "your all-in-one solution",
    "empower your team",
    "transform the way you",
    "designed to help you",
    "the future of",
    "next-generation",
    "cutting-edge",
    "game-changing",
    "in today's fast-paced world",
    "whether you're a",
    "dive in",
    "let's dive into",
    "at the end of the day",
    "it's not just about",
    "we believe that",
    "in a world where",
    "tailored to your needs",
    "best-in-class",
    "world-class",
    "robust and scalable",
    "delve into",
    # Added 2026-09-17: distinct from the phrases above, not near-duplicate
    # rewordings of them -- picked for being widely and specifically
    # documented as generic-AI-copy tells, not just common marketing
    # language (which risks flagging genuinely hand-written copy).
    "in today's digital landscape",
    "look no further",
    "harness the power of",
    "unleash the potential",
    "one-stop shop",
    "gone are the days",
    "picture this",
    "navigate the complexities of",
    "stay ahead of the curve",
    "say goodbye to",
]

OVERUSED_ICON_NAMES: list[str] = [
    "sparkles", "arrow-right", "arrowright", "zap", "rocket",
    "shield-check", "shieldcheck", "check-circle", "checkcircle",
    "star", "trending-up", "trendingup", "bolt", "lightning-bolt",
    "wand", "wand-2", "wand2", "chevron-right", "chevronright",
    # Added 2026-09-17: lucide-react (the icon set this frontend itself
    # uses) renamed CheckCircle/CheckCircle2 to CircleCheck/CircleCheckBig
    # around v0.263 -- newer generated output uses the new names, which the
    # list above would otherwise miss entirely.
    "circle-check", "circlecheck", "circle-check-big", "circlecheckbig",
]

# --- Flag type -----------------------------------------------------------

SEVERITY_WEIGHT = {"info": 0.5, "low": 1.0, "medium": 2.0, "high": 3.5}


@dataclass
class Flag:
    check: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    count: int = 0
    # Added for the layered report. Defaults keep the original four-field
    # construction working anywhere it is still used.
    layer: str = "craft"
    severity: str = "medium"
    why: str = ""
    fix: str = ""
    page_url: str = ""

    @property
    def weight(self) -> float:
        return SEVERITY_WEIGHT.get(self.severity, 2.0)


# --- Craft: how the page reads -------------------------------------------

ROUNDED_TOKEN_RE = re.compile(r"^rounded(-\w+)?$")
SHADOW_TOKEN_RE = re.compile(r"^shadow(-\w+)?$")
CARD_LIKE_TAGS = {"div", "article", "li", "section"}
UNIFORMITY_MIN_CARDS = 3
UNIFORMITY_MIN_RATIO = 0.6


def check_component_uniformity(signal: PageSignal) -> Flag | None:
    card_like = [el for el in signal.elements if el.tag in CARD_LIKE_TAGS and len(el.classes) >= 2]
    if len(card_like) < UNIFORMITY_MIN_CARDS:
        return None

    combo_counts: Counter[tuple[str, str]] = Counter()
    for el in card_like:
        rounded = next((c for c in el.classes if ROUNDED_TOKEN_RE.match(c)), None)
        shadow = next((c for c in el.classes if SHADOW_TOKEN_RE.match(c)), None)
        if rounded and shadow:
            combo_counts[(rounded, shadow)] += 1

    if not combo_counts:
        return None

    (top_rounded, top_shadow), top_count = combo_counts.most_common(1)[0]
    if top_count >= UNIFORMITY_MIN_CARDS and top_count / len(card_like) >= UNIFORMITY_MIN_RATIO:
        return Flag(
            check="component_uniformity",
            layer="craft",
            severity="medium",
            summary=(
                f"{top_count} of {len(card_like)} card-like elements all use the exact same "
                f"'{top_rounded} {top_shadow}' combination"
            ),
            why="When every card carries an identical corner radius and drop shadow, nothing "
                "sits forward or back, so the page reads flat no matter how much is on it. "
                "This pattern is commonly associated with an accepted default rather than a "
                "chosen one.",
            fix="Give one tier of card a heavier surface — a stronger border or a lifted "
                "background — and let the rest sit quieter.",
            evidence=[f"{top_rounded} {top_shadow}"],
            count=top_count,
        )
    return None


EYEBROW_RE = re.compile(r"^(?:step\s*)?0?[1-9]\.?$", re.IGNORECASE)
EYEBROW_MIN_COUNT = 3


def check_numbered_eyebrows(signal: PageSignal) -> Flag | None:
    seen: list[str] = []
    for text in signal.paragraphs:
        stripped = text.strip()
        if EYEBROW_RE.match(stripped) and stripped not in seen:
            seen.append(stripped)

    if len(seen) >= EYEBROW_MIN_COUNT:
        return Flag(
            check="numbered_eyebrows",
            layer="craft",
            severity="low",
            summary=(
                f"Found {len(seen)} short numbered labels ({', '.join(seen[:5])}) — "
                f"a common auto-generated 'step/feature' eyebrow pattern"
            ),
            why="Numbering every section is a layout habit that fills space without deciding "
                "what matters. Readers skip it, and it is one of the more recognisable "
                "generated-page tells.",
            fix="Drop the numbers. If the order genuinely matters, say so in the heading itself.",
            evidence=seen[:8],
            count=len(seen),
        )
    return None


def check_generic_copy(signal: PageSignal) -> Flag | None:
    candidates = [text for text in (signal.headings + signal.paragraphs) if text]
    found: list[str] = []
    for phrase in GENERIC_COPY_PHRASES:
        for text in candidates:
            if phrase in text.lower():
                found.append(f'"{text.strip()[:120]}"')
                break

    if found:
        return Flag(
            check="generic_copy",
            layer="craft",
            severity="high" if len(found) >= 4 else "medium",
            summary=f"{len(found)} instance(s) of generic marketing phrasing found in headings/copy",
            why="These verbs describe no product in particular, which is why they turn up "
                "everywhere. A reader learns nothing from them, and a model reading the page "
                "has nothing specific it could repeat back about you.",
            fix="Replace each with the specific thing it does, in your own words. If a sentence "
                "would be true of any company, it is not saying anything.",
            evidence=found[:8],
            count=len(found),
        )
    return None


COLOR_MATCH_THRESHOLD = 12.0  # euclidean RGB distance; ~near-identical
COLOR_MATCH_MIN_COUNT = 2


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return r, g, b


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def check_color_distance(signal: PageSignal) -> Flag | None:
    page_colors = {c.upper() for c in signal.hex_colors}
    if not page_colors:
        return None

    known_rgb = {name: _hex_to_rgb(hex_val) for name, hex_val in KNOWN_DEFAULT_COLORS.items()}

    matches: dict[str, str] = {}
    for page_hex in page_colors:
        try:
            page_rgb = _hex_to_rgb(page_hex)
        except ValueError:
            continue
        for name, ref_rgb in known_rgb.items():
            if _color_distance(page_rgb, ref_rgb) <= COLOR_MATCH_THRESHOLD:
                matches[page_hex] = name
                break

    if len(matches) >= COLOR_MATCH_MIN_COUNT:
        return Flag(
            check="default_color_palette",
            layer="craft",
            severity="medium",
            summary=(
                f"{len(matches)} colors on the page are unmodified defaults from common "
                f"component libraries/page builders"
            ),
            why="Framework defaults are recognisable precisely because nobody changed them. "
                "It is the quickest signal that a theme was accepted rather than chosen.",
            fix="Shift the hue and lightness away from the default, even slightly. A 10–15 "
                "degree hue rotation is usually enough to stop it reading as stock.",
            evidence=[f"{page_hex} ≈ {name}" for page_hex, name in matches.items()][:8],
            count=len(matches),
        )
    return None


FLAT_TYPOGRAPHY_MIN_HEADINGS = 4
FLAT_TYPOGRAPHY_MAX_DISTINCT_LEVELS = 2
FLAT_TYPOGRAPHY_MIN_DOMINANT_RATIO = 0.75
# A long-form reference document -- a policy, a set of terms, a FAQ page --
# legitimately reads as one h1 plus a flat run of h2 sections: each section is
# a self-contained clause, so there is nothing to nest under it, and further
# heading levels would be decoration, not structure. That is a different shape
# from the pattern this check exists to catch: a template's row of short,
# near-identical cards or steps all sitting at the same heading level with
# barely any content under each one. Words-per-heading tells them apart --
# found by running this check against FIG's own privacy/terms pages, which
# were tripping it (~100-140 words per heading) while genuinely flat template
# sections run closer to 10-30. This is an approximation (page-wide word count
# over heading count, not per-section), so it errs toward not exempting a page
# unless the density is unambiguously document-like.
FLAT_TYPOGRAPHY_MIN_WORDS_PER_HEADING_TO_EXEMPT = 60


def check_flat_typography(signal: PageSignal) -> Flag | None:
    heading_levels = Counter(signal.heading_tags)
    total = len(signal.heading_tags)
    if total < FLAT_TYPOGRAPHY_MIN_HEADINGS or not heading_levels:
        return None

    dominant_level, dominant_count = heading_levels.most_common(1)[0]
    if (
        len(heading_levels) <= FLAT_TYPOGRAPHY_MAX_DISTINCT_LEVELS
        and dominant_count / total >= FLAT_TYPOGRAPHY_MIN_DOMINANT_RATIO
        and not (
            heading_levels.get("h1", 0) == 1
            and signal.word_count / total >= FLAT_TYPOGRAPHY_MIN_WORDS_PER_HEADING_TO_EXEMPT
        )
    ):
        return Flag(
            check="flat_typography",
            layer="craft",
            severity="medium",
            summary=(
                f"{dominant_count} of {total} headings are all <{dominant_level}> — "
                f"little real heading hierarchy despite repeated sections"
            ),
            why="A hierarchy that barely changes gives a reader nothing to land on. The eye "
                "needs a clear first stop, and a crawler needs to know which heading owns "
                "which block of text.",
            fix="Widen the gap: one h1, real h2s for sections, h3s inside them. Cut a level "
                "if you are carrying four.",
            evidence=[f"<{level}> x{count}" for level, count in heading_levels.most_common()],
            count=total,
        )
    return None


OVERUSED_ICON_MIN_COUNT = 2


def check_overused_icons(signal: PageSignal) -> Flag | None:
    found = Counter(token for token in signal.icon_tokens if token in OVERUSED_ICON_NAMES)
    total = sum(found.values())
    if total >= OVERUSED_ICON_MIN_COUNT:
        return Flag(
            check="overused_icons",
            layer="craft",
            severity="low",
            summary=f"{total} uses of icons commonly overused in generated UI ({', '.join(found.keys())})",
            why="The same handful of glyphs carry most generated pages. They are not wrong, "
                "they are invisible from familiarity.",
            fix="Keep them where they earn it, but let at least one visual on the page be "
                "specific to you.",
            evidence=[f"{name} x{count}" for name, count in found.most_common()],
            count=total,
        )
    return None


# --- Structure: is the page in an order that makes sense -----------------


def check_section_order_flags(signal: PageSignal) -> list[Flag]:
    out: list[Flag] = []
    for raw in check_section_order(signal):
        out.append(Flag(
            check="section_order",
            layer="structure",
            severity="high",
            summary=raw["summary"],
            why=raw["why"],
            fix=raw["fix"],
            evidence=raw["evidence"],
            count=raw["count"],
            page_url=signal.url,
        ))
    return out


def check_h1(signal: PageSignal) -> Flag | None:
    if signal.h1_count == 1:
        return None
    if signal.h1_count == 0:
        return Flag(
            check="missing_h1", layer="structure", severity="medium",
            summary="The page has no h1",
            why="The h1 is the one heading that says what this page is. Without it both a "
                "reader skimming and a crawler indexing have to infer it from context.",
            fix="Promote the main headline to an h1. There should be exactly one.",
            count=0, page_url=signal.url,
        )
    return Flag(
        check="multiple_h1", layer="structure", severity="low",
        summary=f"The page carries {signal.h1_count} h1 headings",
        why="More than one h1 means more than one claim about what the page is about. "
            "Nothing breaks, but the hierarchy stops being a hierarchy.",
        fix="Keep one h1 and demote the rest to h2.",
        evidence=signal.headings[:5], count=signal.h1_count, page_url=signal.url,
    )


def check_heading_skips(signal: PageSignal) -> Flag | None:
    levels = [int(t[1]) for t in signal.heading_tags]
    skips: list[str] = []
    for a, b in zip(levels, levels[1:]):
        if b - a >= 2:
            skips.append(f"h{a} → h{b}")
    if len(skips) >= 2:
        return Flag(
            check="heading_skips", layer="structure", severity="low",
            summary=f"{len(skips)} places where the heading level jumps more than one step",
            why="Skipping a level breaks the outline a screen reader and a crawler build from "
                "the page. The visual result can look fine while the structure underneath does not.",
            fix="Step down one level at a time, and use CSS rather than tag choice to control size.",
            evidence=skips[:6], count=len(skips), page_url=signal.url,
        )
    return None


THIN_PAGE_WORDS = 120


def check_thin_page(signal: PageSignal) -> Flag | None:
    if signal.word_count and signal.word_count < THIN_PAGE_WORDS:
        return Flag(
            check="thin_page", layer="structure", severity="medium",
            summary=f"Only {signal.word_count} words of body copy on this page",
            why="A page this short rarely answers the question that brought someone to it, "
                "and gives a model almost nothing to draw on when it is asked about you.",
            fix="Either grow the page into something that answers a real question, or fold it "
                "into a page that already does.",
            count=signal.word_count, page_url=signal.url,
        )
    return None


# --- Search: can a crawler reach and understand it -----------------------


def check_meta_description(signal: PageSignal) -> Flag | None:
    if not signal.meta_description:
        return Flag(
            check="missing_meta_description", layer="search", severity="medium",
            summary="No meta description on this page",
            why="Without one, the snippet under your result is whatever the engine decides to "
                "cut out of the page. That is your first impression, chosen by someone else.",
            fix="Write a 120–155 character description that says what is on this specific page.",
            page_url=signal.url,
        )
    n = len(signal.meta_description)
    if n < 60 or n > 175:
        return Flag(
            check="meta_description_length", layer="search", severity="low",
            summary=f"Meta description is {n} characters ({'short' if n < 60 else 'long'})",
            why="Under about 60 characters wastes the space; over about 160 gets cut mid-sentence.",
            fix="Aim for 120–155 characters.",
            evidence=[signal.meta_description[:180]], count=n, page_url=signal.url,
        )
    return None


def check_title(signal: PageSignal) -> Flag | None:
    if not signal.title:
        return Flag(
            check="missing_title", layer="search", severity="high",
            summary="The page has no <title>",
            why="The title is the single strongest thing you control about how a page is "
                "listed and understood.",
            fix="Add a title that names the page and the site, under 60 characters.",
            page_url=signal.url,
        )
    if len(signal.title) > 65:
        return Flag(
            check="title_length", layer="search", severity="low",
            summary=f"Title is {len(signal.title)} characters and will be truncated",
            why="Anything past roughly 60 characters is cut in most result listings, so the "
                "end of your title is written for nobody.",
            fix="Put the distinguishing words first and trim to under 60.",
            evidence=[signal.title], count=len(signal.title), page_url=signal.url,
        )
    return None


def check_canonical(signal: PageSignal) -> Flag | None:
    if not signal.canonical:
        return Flag(
            check="missing_canonical", layer="search", severity="low",
            summary="No canonical link on this page",
            why="Without a canonical, the same page reached by two URLs can be treated as two "
                "pages, splitting whatever weight it has earned.",
            fix='Add <link rel="canonical" href="..."> pointing at the preferred URL.',
            page_url=signal.url,
        )
    return None


def check_lang(signal: PageSignal) -> Flag | None:
    if not signal.lang:
        return Flag(
            check="missing_lang", layer="search", severity="low",
            summary="The <html> element has no lang attribute",
            why="Screen readers use it to pick a voice and crawlers use it to decide who to "
                "show the page to. It is one attribute.",
            fix='Add lang="en" (or the right language) to the <html> tag.',
            page_url=signal.url,
        )
    return None


ALT_RATIO = 0.4


def check_image_alt(signal: PageSignal) -> Flag | None:
    if signal.images_total >= 3 and signal.images_missing_alt / signal.images_total >= ALT_RATIO:
        return Flag(
            check="missing_alt", layer="search", severity="medium",
            summary=(f"{signal.images_missing_alt} of {signal.images_total} images have no "
                     f"alt text"),
            why="A crawler reads alt text. An empty alt on a meaningful image removes it from "
                "everything a model could learn about you — and removes it from the page "
                "entirely for anyone using a screen reader.",
            fix="Describe the meaningful images. Mark the purely decorative ones alt=\"\" on "
                "purpose so the distinction is deliberate.",
            count=signal.images_missing_alt, page_url=signal.url,
        )
    return None


def check_orphan(signal: PageSignal) -> Flag | None:
    if len(signal.internal_links) <= 2 and signal.word_count > 150:
        return Flag(
            check="few_internal_links", layer="search", severity="low",
            summary=f"Only {len(signal.internal_links)} internal links from this page",
            why="Pages that link nowhere are dead ends for both a reader and a crawler working "
                "out which of your pages matter.",
            fix="Link out to the two or three pages a reader would most plausibly want next.",
            count=len(signal.internal_links), page_url=signal.url,
        )
    return None


# --- Answers: is there anything a model can quote ------------------------

USEFUL_SCHEMA = {"organization", "localbusiness", "product", "faqpage", "article",
                 "breadcrumblist", "webpage", "person", "service", "softwareapplication"}


def check_structured_data(signal: PageSignal) -> Flag | None:
    types = {t.lower() for t in signal.jsonld_types}
    if not types:
        return Flag(
            check="no_structured_data", layer="answers", severity="high",
            summary="No JSON-LD structured data on this page",
            why="Structured data is the one place you get to state plainly what you are, who "
                "you are, and what you sell, in a form a machine does not have to guess at. "
                "Without it a model is inferring all of that from prose.",
            fix="Add an Organization or LocalBusiness block on the homepage and Product or "
                "Article blocks on the pages that warrant them.",
            page_url=signal.url,
        )
    if not (types & USEFUL_SCHEMA):
        return Flag(
            check="thin_structured_data", layer="answers", severity="low",
            summary=f"Structured data present but only: {', '.join(sorted(types))}",
            why="What is there does not describe the business or the thing on the page, so it "
                "does not help anything answer a question about you.",
            fix="Add an Organization block, and a Product/Article block on the relevant pages.",
            evidence=sorted(types), page_url=signal.url,
        )
    return None


FAQ_MIN_WORDS = 400
# Below this a page is more likely a short utility page -- sign-in, contact,
# a thank-you screen -- than something trying to be found or quoted, so a
# missing Q&A block isn't the tell it is on a real content page. Raised from
# 250: FIG's own sign-in (264 words) and sign-up (380 words) pages were both
# firing, and neither is competing to answer a search query. 400 still catches
# genuine short-form content pages; it was chosen to sit above ordinary
# transactional-page word counts rather than below them.


def check_faq(signal: PageSignal) -> Flag | None:
    if signal.has_faq_block:
        return None
    if signal.word_count < FAQ_MIN_WORDS:
        return None
    return Flag(
        check="no_answerable_questions", layer="answers", severity="medium",
        summary="No question-and-answer block on this page",
        why="Models answer questions, so pages that already contain a plainly-worded question "
            "and a direct answer are the easiest thing for one to lift. A page with no "
            "questions on it has to be paraphrased instead, and paraphrase loses you.",
        fix="Add three or four real questions people ask, each with a direct two-sentence "
            "answer, and mark them up as FAQPage.",
        page_url=signal.url,
    )


# --- site-level "answers" checks: can an AI answer engine even reach this
# site, not just whether the page gives it something worth quoting. Both
# operate on the whole site (robots.txt, /llms.txt), not one PageSignal, so
# they're called once per scan from app/pipeline.py rather than from
# run_all_checks() -- see that module and app/scraper.py:crawl().
#
# Curated, not exhaustive, matching this file's existing reference-list
# philosophy: the community-maintained ai-robots-txt/ai.robots.txt project
# lists 240+ tokens, most of them long-tail scrapers nobody's heard of. This
# list is the handful independently documented by their own company that a
# site owner would actually recognize and want to check.
AI_CRAWLER_TOKENS: dict[str, str] = {
    "GPTBot": "ChatGPT's training crawler (OpenAI)",
    "ChatGPT-User": "ChatGPT's user-invoked browsing agent (OpenAI)",
    "OAI-SearchBot": "ChatGPT's search feature crawler (OpenAI)",
    "ClaudeBot": "Claude's crawler (Anthropic)",
    "Claude-User": "Claude's user-invoked browsing agent (Anthropic)",
    "PerplexityBot": "Perplexity's crawler",
    "Google-Extended": "Google's AI training / Gemini opt-out token",
    "Applebot-Extended": "Apple Intelligence's crawler",
    "Bytespider": "ByteDance/TikTok's AI crawler",
    "CCBot": "Common Crawl -- feeds the training data of many other models",
    "Meta-ExternalAgent": "Meta AI's crawler",
    "Amazonbot": "Amazon's AI crawler",
}


def check_ai_crawler_access(blocked: list[str]) -> Flag | None:
    """`blocked` is the list of AI_CRAWLER_TOKENS names app/scraper.py:crawl()
    found disallowed from `/` by this site's actual robots.txt -- the
    parsing itself reuses app/robots.py's RFC 9309 reader, not a second
    implementation. A site blocking one of these cannot be cited by that
    crawler's answer engine no matter how good its content is; this can't
    be inferred from a page, so it isn't a per-page Flag."""
    if not blocked:
        return None
    return Flag(
        check="ai_crawlers_blocked", layer="answers", severity="high",
        summary=f"robots.txt blocks {len(blocked)} AI crawler{'s' if len(blocked) != 1 else ''} "
                f"from this site: {', '.join(sorted(blocked))}",
        why="This is a probabilistic, not certain, signal: a blocked crawler's answer engine "
            "generally can't quote or cite pages it was never allowed to read. Some sites "
            "block these on purpose (a licensing or training-data decision, not an accident) "
            "-- if that's true here, this is working as intended.",
        fix="If being findable by AI answer engines matters for this site, remove or narrow "
            "the Disallow rule for the crawlers listed above in robots.txt.",
        evidence=sorted(blocked),
    )


def check_llms_txt(present: bool) -> Flag | None:
    """`present` comes from app/scraper.py:crawl() checking for a real
    /llms.txt (llmstxt.org's spec: a Markdown file that tells an AI agent
    what on the site is worth fetching, the llms.txt equivalent of a
    sitemap). Unlike robots.txt this is opt-in signage, not access control
    -- its absence is a missed opportunity, not a block, so this stays
    lower severity than check_ai_crawler_access."""
    if present:
        return None
    return Flag(
        check="missing_llms_txt", layer="answers", severity="low",
        summary="No /llms.txt found",
        why="llms.txt is a routing guide for AI agents, not an access-control file -- it "
            "points a model at what's actually worth reading on the site instead of leaving "
            "it to guess from a sitemap built for search engines.",
        fix="Add a Markdown file at /llms.txt: an H1 with the site's name, a one-line "
            "summary, and links to the pages most worth an agent's attention.",
    )


SPECIFICITY_MIN_NUMBERS = 4


def check_specificity(signal: PageSignal) -> Flag | None:
    if signal.word_count < 200:
        return None
    per_100 = signal.numbers_in_copy / max(signal.word_count / 100, 1)
    if signal.numbers_in_copy < SPECIFICITY_MIN_NUMBERS and per_100 < 1.0:
        return Flag(
            check="low_specificity", layer="answers", severity="medium",
            summary=(f"{signal.numbers_in_copy} concrete numbers across {signal.word_count} "
                     f"words of copy"),
            why="Specifics are what get quoted. Prices, dates, counts, place names and product "
                "names give a model something it can repeat with confidence; adjectives do not.",
            fix="Put at least one real number or name in each section — what it costs, how "
                "long it takes, how many, where.",
            count=signal.numbers_in_copy, page_url=signal.url,
        )
    return None


# --- runner --------------------------------------------------------------

SINGLE_CHECKS = (
    # craft
    check_component_uniformity,
    check_numbered_eyebrows,
    check_generic_copy,
    check_color_distance,
    check_flat_typography,
    check_overused_icons,
    # structure
    check_h1,
    check_heading_skips,
    check_thin_page,
    # search
    check_title,
    check_meta_description,
    check_canonical,
    check_lang,
    check_image_alt,
    check_orphan,
    # answers
    check_structured_data,
    check_faq,
    check_specificity,
)

MULTI_CHECKS = (check_section_order_flags,)

# Kept for anything still importing the original name.
ALL_CHECKS = SINGLE_CHECKS


# A page that opts itself out of search (<meta name="robots" content="noindex">
# -- a login screen, a password-reset link target, a thank-you page) still
# deserves the checks that are good practice regardless of indexing (a real
# title, a lang attribute, alt text, a sensible heading). It doesn't deserve
# the ones whose entire premise is being found or ranked: a noindexed page's
# missing canonical, empty meta description, thinness or lack of inbound
# links are not tells of anything -- they're the point. Found running this
# scanner on FIG's own /forgot-password (found while tuning against FIG's own
# pages, same as flat_typography/check_faq earlier).
NOINDEX_EXEMPT_CHECKS = frozenset({
    "missing_meta_description", "meta_description_length",
    "missing_canonical", "few_internal_links", "thin_page",
})


def run_all_checks(signal: PageSignal) -> list[Flag]:
    flags: list[Flag] = []
    for check in SINGLE_CHECKS:
        flag = check(signal)
        if flag is not None:
            if signal.noindex and flag.check in NOINDEX_EXEMPT_CHECKS:
                continue
            if not flag.page_url:
                flag.page_url = signal.url
            flags.append(flag)
    for multi in MULTI_CHECKS:
        flags.extend(multi(signal))
    return flags


# --- checklist -------------------------------------------------------------

# A user-facing description of every check above, grouped the same way this
# file is. `ids` lists the Flag.check values a function can emit — a few
# functions (check_h1, check_title, check_meta_description,
# check_structured_data) emit one of two ids depending on which branch fires.
# Hand-maintained rather than introspected from the functions, same as the
# reference lists above: keep this in sync when a check's condition changes.
CHECKLIST: list[dict] = [
    # craft
    {"ids": ["component_uniformity"], "layer": "craft", "title": "Uniform card styling",
     "flags": "3 or more card-like elements sharing the exact same rounded-corner + "
              "shadow combination, on 60% or more of the cards found."},
    {"ids": ["numbered_eyebrows"], "layer": "craft", "title": "Numbered step/feature labels",
     "flags": "3 or more short standalone labels such as '01', '02', or 'Step 3' used "
              "as section eyebrows."},
    {"ids": ["generic_copy"], "layer": "craft", "title": "Generic marketing phrasing",
     "flags": "Headings or copy matching a maintained list of ~30 filler phrases "
              "('elevate your', 'unlock the power of', 'seamlessly integrate', ...)."},
    {"ids": ["default_color_palette"], "layer": "craft", "title": "Unmodified default colors",
     "flags": "2 or more hex colors on the page within a close RGB distance of known "
              "component-library or page-builder defaults (Tailwind, shadcn, common "
              "gradient blues)."},
    {"ids": ["flat_typography"], "layer": "craft", "title": "Flat heading hierarchy",
     "flags": "4 or more headings where 75% or more collapse into 2 or fewer distinct "
              "heading levels. Not flagged when there is exactly one h1 and each heading "
              "owns 60+ words on average -- a real long-form document read as one h1 "
              "plus flat h2 sections, not a row of thin templated cards."},
    {"ids": ["overused_icons"], "layer": "craft", "title": "Overused icon set",
     "flags": "2 or more uses of icons from a maintained list overused in generated UI "
              "(sparkles, arrow-right, zap, rocket, shield-check, star, ...)."},
    # structure
    {"ids": ["section_order"], "layer": "structure", "title": "Sections out of a sensible order",
     "flags": "A section (e.g. pricing) sitting before the section that would justify "
              "it, based on the role each section is classified as."},
    {"ids": ["missing_h1", "multiple_h1"], "layer": "structure", "title": "H1 count",
     "flags": "Zero h1 headings on the page, or more than one."},
    {"ids": ["heading_skips"], "layer": "structure", "title": "Heading level skips",
     "flags": "2 or more places where the heading level jumps more than one step, "
              "such as h2 straight to h4."},
    {"ids": ["thin_page"], "layer": "structure", "title": "Thin page",
     "flags": "Fewer than 120 words of body copy on the page. Not flagged on a page "
              "marked noindex."},
    # search
    {"ids": ["missing_title", "title_length"], "layer": "search", "title": "Page title",
     "flags": "No <title> tag, or a title over 65 characters that gets truncated in "
              "search results."},
    {"ids": ["missing_meta_description", "meta_description_length"], "layer": "search",
     "title": "Meta description",
     "flags": "No meta description, or one outside the 60-175 character range. Not "
              "flagged on a page marked noindex -- it never shows a search snippet."},
    {"ids": ["missing_canonical"], "layer": "search", "title": "Canonical link",
     "flags": "No <link rel=\"canonical\"> on the page. Not flagged on a page marked "
              "noindex -- canonical exists to dedupe search results."},
    {"ids": ["missing_lang"], "layer": "search", "title": "Language attribute",
     "flags": "No lang attribute on the <html> element."},
    {"ids": ["missing_alt"], "layer": "search", "title": "Image alt text",
     "flags": "3 or more images on the page, 40% or more missing alt text."},
    {"ids": ["few_internal_links"], "layer": "search", "title": "Orphan pages",
     "flags": "2 or fewer internal links from a page carrying 150+ words. Not flagged "
              "on a page marked noindex -- being hard to stumble into is often the point."},
    # answers
    {"ids": ["no_structured_data", "thin_structured_data"], "layer": "answers",
     "title": "Structured data (JSON-LD)",
     "flags": "No JSON-LD on the page, or JSON-LD present but none of it a useful type "
              "(Organization, Product, FAQPage, Article, ...)."},
    {"ids": ["no_answerable_questions"], "layer": "answers", "title": "No Q&A block",
     "flags": "400+ words of copy with no FAQ block and no plainly-worded question "
              "headings."},
    {"ids": ["low_specificity"], "layer": "answers", "title": "Low specificity",
     "flags": "200+ words of copy with fewer than 4 concrete numbers, and under 1 "
              "number per 100 words."},
    {"ids": ["ai_crawlers_blocked"], "layer": "answers", "title": "AI crawlers blocked",
     "flags": "Site-level, once per scan, not per page: robots.txt disallows one or more "
              "of a curated list of named AI-answer-engine crawlers (GPTBot, ClaudeBot, "
              "PerplexityBot, Google-Extended, ...) from the whole site."},
    {"ids": ["missing_llms_txt"], "layer": "answers", "title": "No /llms.txt",
     "flags": "Site-level, once per scan: no llms.txt found at the site root (llmstxt.org's "
              "spec -- a routing guide for AI agents, not an access-control file)."},
]


def checklist() -> list[dict]:
    """JSON-safe: every check FIG runs, what triggers it, grouped by layer.
    No AI call is involved — this is a direct, hand-maintained description of
    the deterministic rules above. Served at GET /v1/checklist so a user can
    see what a scan actually looked for before or after running one."""
    return CHECKLIST
