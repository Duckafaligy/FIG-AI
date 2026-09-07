"""The ONLY module in this codebase allowed to call an LLM.

Takes already-flagged, small structured data from rules/checks.py and turns
it into plain-language explanation + fix. Never receives the raw scraped
page — see the architecture note in CLAUDE.md. If you're tempted to add
another `anthropic` call somewhere else in the pipeline, write a rule
instead.

Findings are sent in small batches. One call for a whole scan overflows the
token budget on any site with more than a handful of flags, and a truncated
JSON array means every explanation is lost rather than one — which is exactly
what happened the first time this ran against a real key.
"""
from __future__ import annotations

import json
import logging
import os

from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"  # cheap model — this task doesn't need more

# Small enough that a batch always fits comfortably inside its own budget.
BATCH_SIZE = 6
TOKENS_PER_FLAG = 260
TOKEN_FLOOR = 512
TOKEN_CEILING = 8192

log = logging.getLogger("fig.ai_explain")

SYSTEM_PROMPT = """\
You are helping someone understand why parts of their website read as \
generic AI-generated design, so they can learn to make more deliberate \
choices. You are given a list of already-detected pattern flags — small \
structured data, never the raw page. For each flag, write:

- "why": one or two sentences on why this pattern commonly reads as \
generic/AI-made
- "fix": one concrete, specific suggestion for this project (not generic \
advice)

Tone rules (must follow):
- Always phrase findings probabilistically and educationally, e.g. "this \
pattern is commonly associated with..." — never "this IS AI-written" or \
similar certainty claims.
- This is a self-check learning tool for the site's own owner, not an \
accusation. Never imply the author did something wrong, never use \
accusatory language.
- Keep each field under 45 words.

Return ONLY a JSON array, one object per input flag, in the same order, \
each with keys "why" and "fix". No prose before or after the array."""

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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


def _explain_batch(client: Anthropic, batch: list[dict]) -> list[dict]:
    budget = min(TOKEN_CEILING, max(TOKEN_FLOOR, TOKENS_PER_FLAG * len(batch)))
    message = client.messages.create(
        model=MODEL,
        max_tokens=budget,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(batch)}],
    )
    if message.stop_reason == "max_tokens":
        raise ValueError(f"response hit the {budget} token cap")
    out = _parse_json_array(message.content[0].text)
    if len(out) != len(batch):
        raise ValueError(f"got {len(out)} explanations for {len(batch)} flags")
    return out


def explain_flags(flags: list[dict]) -> list[dict]:
    """flags must already be small structured data (check name, summary,
    evidence, count) from rules/checks.py — never pass raw page HTML/text.

    Always returns one entry per input flag, in order. A batch that fails
    yields empty dicts for its flags, so the caller keeps the explanation the
    rule shipped with instead of pairing the wrong text with a finding.
    """
    if not flags:
        return []

    client = _get_client()
    results: list[dict] = []

    for i in range(0, len(flags), BATCH_SIZE):
        batch = flags[i:i + BATCH_SIZE]
        try:
            results.extend(_explain_batch(client, batch))
        except Exception as exc:                    # noqa: BLE001
            log.warning("ai_explain batch %d-%d failed (%s); keeping rule text",
                        i, i + len(batch) - 1, exc)
            results.extend({} for _ in batch)

    return results
