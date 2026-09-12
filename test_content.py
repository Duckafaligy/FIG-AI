"""Tests for the content queue's scorer and its state machine.

No network, no API key, no database — `score_post` and `move` are given plain
objects. Run it with:

    python test_content.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from app import content
from app.models import ContentPost

# A draft that passes every check, written to pass them for real reasons
# rather than by keyword-matching the rules.
GOOD = "\n\n".join([
    "# How much does a new roof cost",
    "How much does a new roof cost? Between $1,200 and $4,500 for most jobs, "
    "in 3 to 5 days, and this is what moves the number either way.",
    "## The short answer",
    "Most jobs run 3 to 5 days. We have done 340 of them since 2019, so that "
    "is a measured figure rather than a comfortable range.",
    "## What drives the price",
    "Access, how much comes out first, and whether it needs a permit. A "
    "second-floor job with no side entry adds about 8 hours of labour.",
    "## How long does it take?",
    "Four days is typical: one to strip out, two for the work, one for making "
    "good. Weather adds a day about one job in five.",
    " ".join(["Detail that a buyer actually wants to read before booking."] * 60),
    "See our [pricing](/pricing) and the [process page](/process).",
])

SLOP = "\n\n".join([
    "# Roofing",
    "Elevate your experience with our seamless, innovative approach. We "
    "unlock the full potential of your property at every touchpoint.",
    "Get in touch today to learn more.",
])


def _post(**kw):
    base = dict(title="How much does a new roof cost in 2026", category="guide",
                target_keyword="how much does a new roof cost", body=GOOD)
    base.update(kw)
    return ContentPost(**base)


def test_a_brief_with_no_draft_scores_nothing():
    r = content.score_post(_post(body=None))
    assert r["score"] is None, r
    assert r["words"] == 0
    print("[PASS] an unstarted brief scores None, not zero")


def test_a_finished_draft_passes_every_check():
    r = content.score_post(_post())
    assert r["score"] == 100, (r["score"], r["failed"])
    print("[PASS] the finished draft scores 100 with nothing failing")


def test_slop_fails_the_checks_that_matter():
    r = content.score_post(_post(body=SLOP))
    assert r["score"] < 50, r["score"]
    for must in ("Long enough for its category",
                 "Numbers, names or figures a model can quote",
                 "Three or more subheadings"):
        assert must in r["failed"], (must, r["failed"])
    print(f"[PASS] filler copy scores {r['score']} and fails on substance")


def test_length_bar_is_per_category():
    short = " ".join(["A real sentence about the subject."] * 55)   # ~330 words
    body = GOOD.split("\n\n")[0] + "\n\n" + GOOD.split("\n\n")[1] + "\n\n" + short
    as_guide = content.score_post(_post(category="guide", body=body))
    as_glossary = content.score_post(_post(category="glossary", body=body))
    assert "Long enough for its category" in as_guide["failed"]
    assert "Long enough for its category" not in as_glossary["failed"]
    print("[PASS] 330 words is short for a guide and fine for a glossary entry")


def test_stuffing_is_repetition_not_a_long_question():
    twice = content.score_post(_post())
    assert "The phrase is not repeated every other paragraph" not in twice["failed"]

    stuffed = _post(body="\n\n".join(
        ["# x", "how much does a new roof cost " * 40] + ["## a", "## b", "## c"]))
    r = content.score_post(stuffed)
    assert "The phrase is not repeated every other paragraph" in r["failed"], r["failed"]
    print("[PASS] a phrase asked twice is fine; the same phrase forty times is not")


def test_the_scores_are_ordered_by_quality():
    scores = [content.score_post(_post(body=b))["score"] for b in (GOOD, SLOP)]
    assert scores[0] > scores[1], scores
    print(f"[PASS] finished {scores[0]} > filler {scores[1]}")


def test_ring_geometry_matches_the_score():
    full = content.ring(100)
    half = content.ring(50)
    assert abs(full["dash"] - full["gap"]) < 0.5, full
    assert abs(half["dash"] * 2 - half["gap"]) < 0.5, half
    assert content.ring(None)["tone"] == "none"
    assert content.ring(85)["tone"] == "good"
    assert content.ring(70)["tone"] == "warn"
    assert content.ring(30)["tone"] == "bad"
    print("[PASS] the gauge arc is proportional and colour follows the band")


def test_only_legal_moves_are_allowed():
    # Review is not skippable, and publishing is not a state you can set.
    assert ("queued", "review") not in content.ALLOWED
    assert ("queued", "published") not in content.ALLOWED
    assert ("in_progress", "scheduled") not in content.ALLOWED
    assert ("review", "in_progress") in content.ALLOWED, "sending it back must work"
    print("[PASS] Review cannot be skipped on the way to Scheduled")


def test_the_writer_refuses_rather_than_pretending():
    # `draft` is the one place a model call would go, and it is not built.
    # This test exists so that stays a deliberate decision.
    post = _post()
    post.id, post.site_id = "p1", "s1"

    class Site:
        id, account_id = "s1", "a1"

    class Account:
        id = "a1"

    class FakeSession:
        def get(self, model, ident):
            return post if model is ContentPost else Site()

    try:
        content.draft(FakeSession(), Account(), "p1")
    except content.Refused as exc:
        assert "does not write" in str(exc), str(exc)
        assert post.body == GOOD, "draft() must not have altered anything"
        print("[PASS] the drafting step refuses out loud and changes nothing")
        return
    raise AssertionError("draft() should raise Refused, not quietly succeed")


def test_slug_is_url_safe():
    assert content._slug("Answer “What does it cost?” on a page of its own") \
        == "answer-what-does-it-cost-on-a-page-of-its-own"
    assert not content._slug("!!!").strip("-")
    print("[PASS] slugs come out url-safe")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
    print(f"\nAll {len(TESTS)} content-queue tests passed.")
