"""Section role classification and page-order checking.

Deterministic, $0, no LLM. A section's role is guessed from what is actually
in it — a price token, a form, a run of list items, a heading that names
itself — and the page is then checked against the order those roles normally
need to be in for the page to make its case before it asks for anything.

This is the check the product leads with, so the language it produces has to
stay descriptive: it reports that pricing sits above the section that
justifies it, never that the page is "wrong".
"""
from __future__ import annotations

import re

from app.scraper import PageSignal, SectionSignal

# --- roles --------------------------------------------------------------
# Rank is the order these normally run in. Two sections sharing a rank are
# interchangeable; a lower rank appearing below a higher one is an inversion.

ROLE_RANK: dict[str, int] = {
    "nav": 0,
    "hero": 1,
    "social_proof": 2,
    "problem": 3,
    "features": 4,
    "how": 4,
    "stats": 5,
    "testimonials": 6,
    "pricing": 7,
    "faq": 8,
    "cta": 9,
    "contact": 9,
    "footer": 10,
    "content": 5,      # generic prose; ranked mid so it never triggers on its own
}

ROLE_LABEL = {
    "nav": "navigation",
    "hero": "hero",
    "social_proof": "social proof",
    "problem": "problem statement",
    "features": "features",
    "how": "how it works",
    "stats": "stats",
    "testimonials": "testimonials",
    "pricing": "pricing",
    "faq": "FAQ",
    "cta": "call to action",
    "contact": "contact",
    "footer": "footer",
    "content": "body content",
}

_RE = {
    "pricing": re.compile(r"\b(pricing|plans?|packages?|tiers?|subscriptions?|cost)\b", re.I),
    "faq": re.compile(r"\b(faq|frequently asked|common questions|questions answered)\b", re.I),
    "testimonials": re.compile(
        r"\b(testimonials?|what (?:our )?(?:customers|clients|users) say|reviews?|"
        r"loved by|case stud(?:y|ies)|success stor)", re.I),
    "features": re.compile(
        r"\b(features?|what you get|benefits?|capabilit|everything you|"
        r"built for|why (?:choose|us)|what it (?:does|catches))\b", re.I),
    "how": re.compile(r"\b(how it works|how we work|the process|steps?|getting started|workflow)\b", re.I),
    "social_proof": re.compile(r"\b(trusted by|as seen (?:in|on)|used by|our (?:clients|partners)|backed by)\b", re.I),
    "stats": re.compile(r"\b(by the numbers|results?|impact|our numbers|stats)\b", re.I),
    "cta": re.compile(
        r"\b(get started|start (?:free|now|today)|try (?:it|free)|book a|"
        r"ready to|join|sign up|request a demo|talk to us|are you in)\b", re.I),
    "problem": re.compile(r"\b(the problem|why this matters|what goes wrong|sound familiar)\b", re.I),
    "contact": re.compile(r"\b(contact|get in touch|reach us|say hello)\b", re.I),
}


_PRICE_RE = re.compile(r"[$£€]\s?\d+")


def price_hits(section: SectionSignal) -> list[str]:
    """Actual currency amounts, not just any number."""
    return _PRICE_RE.findall(section.text or "")


def classify(section: SectionSignal, position: int, total: int) -> str:
    """One section to one role. Order of the tests matters: the specific,
    high-confidence signals are checked before the shape-based fallbacks."""
    tag = section.tag.lower()
    hay = f"{section.heading} {' '.join(section.classes)} {section.element_id}"

    if tag == "nav":
        return "nav"
    if tag == "footer":
        return "footer"
    # A trailing block that is mostly links and little prose is a footer even
    # when it is a plain <div>.
    if position >= total - 1 and section.link_count >= 6 and section.word_count < 220:
        return "footer"

    # The hero is decided by position before anything keyword-based, or a
    # first block that happens to mention a price gets read as the pricing
    # section.
    if position == 0 and (tag == "header" or section.heading_level in (0, 1, 2)):
        return "hero"

    if _RE["faq"].search(hay):
        return "faq"
    if _RE["pricing"].search(hay):
        return "pricing"
    # A price token on its own is much weaker evidence: it has to look like a
    # priced block rather than a sentence that happens to contain a number.
    if section.has_price and section.word_count < 700 and (
            section.list_items >= 3 or section.button_count >= 1 or len(price_hits(section)) >= 2):
        return "pricing?"
    if _RE["testimonials"].search(hay):
        return "testimonials"
    if _RE["how"].search(hay):
        return "how"
    if _RE["features"].search(hay):
        return "features"
    if _RE["social_proof"].search(hay):
        return "social_proof"
    if _RE["stats"].search(hay):
        return "stats"
    if _RE["problem"].search(hay):
        return "problem"
    if _RE["contact"].search(hay) and section.has_form:
        return "contact"

    # A logo strip: several images, almost no words.
    if section.image_count >= 3 and section.word_count < 40:
        return "social_proof"
    # Short, imperative, has a button, near the end: closing CTA.
    if section.word_count < 90 and section.button_count >= 1 and position >= total * 0.6:
        return "cta"
    if _RE["cta"].search(hay) and section.word_count < 200:
        return "cta"
    if section.list_items >= 6 and section.word_count < 400:
        return "features"

    return "content"


def roles_for(signal: PageSignal) -> list[str]:
    """Classify, then settle the ambiguous ones.

    A page can only have one hero, and only the first block that merely looks
    priced is treated as the pricing section — otherwise a page that quotes a
    number in five places reads as five pricing sections, which is neither
    true nor useful.
    """
    total = len(signal.sections)
    raw = [classify(s, i, total) for i, s in enumerate(signal.sections)]

    seen_hero = False
    seen_pricing = "pricing" in raw
    out: list[str] = []
    for role in raw:
        if role == "hero":
            if seen_hero:
                role = "content"
            seen_hero = True
        elif role == "pricing?":
            # A weak match only counts if nothing named itself pricing and
            # nothing weaker has already claimed the slot.
            role = "content" if seen_pricing else "pricing"
            seen_pricing = True
        out.append(role)
    return out


# --- the order check ----------------------------------------------------

# Only inversions that actually cost a reader something are reported. A page
# putting testimonials above features is a style choice; a page putting the
# price above the reason is a conversion problem.
REPORTABLE = {
    ("pricing", "features"): (
        "pricing sits above the section that justifies it",
        "The page asks for a decision before it has made the case for one. A reader "
        "hitting a price with no context has nothing to weigh it against, so the "
        "number reads as expensive by default.",
        "Move pricing below the features or how-it-works section, or put a short "
        "summary of what is included directly above the price.",
    ),
    ("pricing", "how"): (
        "pricing sits above the explanation of how it works",
        "Someone who does not yet know what the product does cannot judge whether a "
        "price is fair. The section order is asking them to.",
        "Move the how-it-works section above pricing.",
    ),
    ("cta", "features"): (
        "the closing call to action appears before the page explains itself",
        "A closing CTA works because everything above it has already argued for the "
        "click. Placed early, it is asking a reader who has been given no reason yet.",
        "Keep an action in the hero if you want one, but move the closing CTA below "
        "the explanation.",
    ),
    ("faq", "features"): (
        "the FAQ runs before the page has said what the thing is",
        "An FAQ answers questions a reader has already formed. Placed first, it "
        "answers questions nobody has asked yet.",
        "Move the FAQ below the main explanation, near the closing action.",
    ),
    ("testimonials", "hero"): (
        "testimonials appear above the hero",
        "Praise lands only after a reader knows what is being praised.",
        "Move the hero to the top of the page.",
    ),
}


def check_section_order(signal: PageSignal) -> list[dict]:
    """Returns raw finding dicts; checks.py wraps them into Flags."""
    roles = roles_for(signal)
    if len(roles) < 3:
        return []

    first: dict[str, int] = {}
    for i, r in enumerate(roles):
        first.setdefault(r, i)

    out: list[dict] = []
    for (early, late), (summary, why, fix) in REPORTABLE.items():
        if early in first and late in first and first[early] < first[late]:
            out.append({
                "check": "section_order",
                "summary": (
                    f"On {_path(signal.url)}, {summary} "
                    f"({ROLE_LABEL[early]} is section {first[early] + 1}, "
                    f"{ROLE_LABEL[late]} is section {first[late] + 1})"
                ),
                "why": why,
                "fix": fix,
                "evidence": [_order_line(roles)],
                "count": 1,
            })

    # A footer that is not last means something is rendering below it.
    if "footer" in first and first["footer"] < len(roles) - 1:
        trailing = [ROLE_LABEL[r] for r in roles[first["footer"] + 1:]]
        out.append({
            "check": "section_order",
            "summary": f"On {_path(signal.url)}, {len(trailing)} block(s) render below the footer",
            "why": "Anything below the footer is below where readers stop. It is being "
                   "paid for in page weight and read by almost nobody.",
            "fix": f"Move {', '.join(trailing[:3])} above the footer, or remove it.",
            "evidence": [_order_line(roles)],
            "count": len(trailing),
        })

    return out


def _order_line(roles: list[str]) -> str:
    return " → ".join(ROLE_LABEL.get(r, r) for r in roles)


def _path(url: str) -> str:
    from urllib.parse import urlparse
    p = urlparse(url).path or "/"
    return p if p != "" else "/"
