"""The ONLY module in this codebase allowed to call an LLM.

Takes already-flagged, small structured data from rules/checks.py and turns
it into plain-language explanation + fix. Never receives the raw scraped
page — see the architecture note in CLAUDE.md. If you're tempted to add
another `anthropic` call somewhere else in the pipeline, write a rule
instead.

What it is sent is one item per *distinct* finding (the pipeline groups a
check that fired on twelve pages into one item), so a scan costs a handful of
calls however many pages it read. Items go in small batches: one call for a
whole scan once overflowed its token budget, and a truncated JSON array loses
every explanation rather than one.

Every call's token usage is counted and returned, so each scan's trace
records exactly what the AI step cost.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import anthropic

from app import config

MODEL = config.AI_MODEL

# Small enough that a batch always fits comfortably inside its own budget.
BATCH_SIZE = 6
TOKENS_PER_ITEM = 320
TOKEN_FLOOR = 768
TOKEN_CEILING = 8192

log = logging.getLogger("fig.ai_explain")

SYSTEM_PROMPT = """\
You explain website audit findings to the site's own owner, so they can \
understand each problem and fix it. You receive findings that deterministic \
rules have already detected -- small structured data, never the raw page. \
Each finding has a layer, and the layer decides what the finding is about:

- craft: design and copy patterns that commonly read as generic or \
template-made (stock palettes, uniform cards, filler phrases, numbered \
eyebrows). Explain why the pattern tends to read as generic.
- structure: how the page is organised -- heading hierarchy, section order, \
thin content. Explain the effect on a person reading or scanning the page.
- search: what a search crawler can reach and understand -- titles, meta \
descriptions, canonical tags, page language, alt text, internal links. \
Explain the effect on how the page is indexed and shown in search results.
- answers: what an AI answer engine has to work with -- structured data, \
questions answered in plain words, specific facts. Explain the effect on \
whether the page can be quoted or cited in an answer.

The input is a JSON object with "site" (the hostname) and "findings" (the list). When a fix names a URL, use that real hostname -- never a placeholder such as example.com or yourdomain.com.

For each finding write:
- "why": one or two sentences on why it matters, in terms of its layer.
- "fix": one concrete change for this site, using the evidence and example \
pages given. Specific, not generic advice.

Tone rules (must follow):
- Only craft findings are about generic or AI-made patterns. Never describe \
a structure, search or answers finding as AI-generated.
- Phrase craft findings probabilistically ("this pattern is commonly \
associated with..."). Never state that anything IS AI-written.
- This is a self-check for the site's owner, not an accusation. No blame and \
no accusatory language.
- Keep each field under 45 words.

Return ONLY a JSON array with one object per input finding, in the same \
order, each with exactly the keys "why" and "fix". No prose before or after."""


@dataclass
class Usage:
    """What the AI step spent on one scan."""

    model: str = MODEL
    resolved_model: str = ""
    calls: int = 0
    failed_batches: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    request_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def cost_usd(self) -> float:
        return round(self.input_tokens / 1_000_000 * config.AI_PRICE_INPUT_PER_MTOK
                     + self.output_tokens / 1_000_000 * config.AI_PRICE_OUTPUT_PER_MTOK, 6)

    def as_dict(self) -> dict:
        return {
            "model": self.model, "resolved_model": self.resolved_model,
            "calls": self.calls, "failed_batches": self.failed_batches,
            "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd, "request_ids": self.request_ids,
            "errors": self.errors,
        }


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # The SDK already retries 429s, 5xx and dropped connections twice.
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=60.0,
                                      max_retries=2)
    return _client


def _parse_json_array(text: str) -> list[dict]:
    """Tolerant of a fenced block or stray prose either side. A truncated
    response still raises — the caller treats that batch as unexplained
    rather than mispairing explanations with the wrong findings."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text.strip("`")
        text = text.split("\n", 1)[1] if text.lstrip().startswith("json") else text
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array in response")
    parsed = json.loads(text[start:end + 1])
    if not isinstance(parsed, list):
        raise ValueError("response was not a list")
    return parsed


def _explain_batch(client: anthropic.Anthropic, batch: list[dict], usage: Usage,
                   site: str = "") -> list[dict]:
    budget = min(TOKEN_CEILING, max(TOKEN_FLOOR, TOKENS_PER_ITEM * len(batch)))
    message = client.messages.create(
        model=MODEL,
        max_tokens=budget,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user",
                   "content": json.dumps({"site": site, "findings": batch}, ensure_ascii=False)}],
    )
    # Counted before anything below can fail: a response we cannot use was
    # still paid for.
    usage.calls += 1
    usage.input_tokens += message.usage.input_tokens
    usage.output_tokens += message.usage.output_tokens
    usage.resolved_model = message.model
    if message._request_id:
        usage.request_ids.append(message._request_id)

    if message.stop_reason == "refusal":
        raise ValueError("the model declined this batch")
    if message.stop_reason == "max_tokens":
        raise ValueError(f"response hit the {budget} token cap")

    text = "".join(block.text for block in message.content if block.type == "text")
    out = _parse_json_array(text)
    if len(out) != len(batch):
        raise ValueError(f"got {len(out)} explanations for {len(batch)} findings")
    return [
        {"why": str(o.get("why", "")).strip(), "fix": str(o.get("fix", "")).strip()}
        if isinstance(o, dict) else {}
        for o in out
    ]


def explain_flags(items: list[dict], site: str = "") -> tuple[list[dict], Usage]:
    """items must already be small structured data (layer, check, summary,
    evidence, counts) — never raw page HTML or text.

    Always returns one entry per input item, in order, plus the usage. A batch
    that fails yields empty dicts for its items, so the caller keeps the
    explanation the rule shipped with instead of pairing the wrong text with
    a finding.
    """
    usage = Usage()
    if not items:
        return [], usage

    client = _get_client()
    results: list[dict] = []

    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        try:
            results.extend(_explain_batch(client, batch, usage, site))
        except (anthropic.APIError, ValueError) as exc:
            last = i + len(batch) - 1
            log.warning("ai_explain batch %d-%d failed (%s); keeping rule text", i, last, exc)
            usage.failed_batches += 1
            usage.errors.append(f"items {i}-{last}: {type(exc).__name__}: {exc}")
            results.extend({} for _ in batch)

    return results, usage
