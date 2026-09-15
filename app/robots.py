"""robots.txt, read the way RFC 9309 and Google read it.

Python's `urllib.robotparser` is not used. On launchvault.ca (Test #1) it let
the crawler read pages the site disallows, for two separate reasons:

  * it ends a group at a blank line, so a block of `Disallow:` lines separated
    from its `User-agent:` line by an empty line is silently dropped;
  * it applies the first matching rule in file order, so an `Allow: /` at the
    top of a group allows everything beneath it.

RFC 9309 groups rules by user-agent lines alone -- blank lines mean nothing --
picks the most specific rule (the longest matching path) with Allow winning a
tie, and supports `*` and a trailing `$` in paths, neither of which urllib
supports at all.

Pure: no network. The scraper fetches the file and hands the text in.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urlsplit


def _token(user_agent: str) -> str:
    """The product token groups are matched on: `FIGBot/0.2 (+...)` -> `figbot`."""
    return user_agent.strip().split("/", 1)[0].split(" ", 1)[0].strip().lower()


@dataclass
class Rule:
    allow: bool
    path: str
    pattern: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        anchored = self.path.endswith("$")
        body = self.path[:-1] if anchored else self.path
        regex = ".*".join(re.escape(unquote(part)) for part in body.split("*"))
        self.pattern = re.compile(regex + ("$" if anchored else ""))

    def matches(self, target: str) -> bool:
        return self.pattern.match(target) is not None

    def __str__(self) -> str:
        return f"{'Allow' if self.allow else 'Disallow'}: {self.path}"


@dataclass
class Group:
    agents: list[str] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)


@dataclass
class Robots:
    groups: list[Group] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    allow_all: bool = False
    disallow_all: bool = False

    @classmethod
    def parse(cls, text: str) -> "Robots":
        robots = cls()
        current: Group | None = None
        collecting_agents = False

        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue                    # blank lines and junk carry no meaning
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()

            if key == "user-agent":
                # Consecutive user-agent lines share one group; one that follows
                # rules starts the next group.
                if current is None or not collecting_agents:
                    current = Group()
                    robots.groups.append(current)
                current.agents.append(_token(value))
                collecting_agents = True
            elif key in ("allow", "disallow"):
                collecting_agents = False
                # A rule before any user-agent line belongs to no group, and an
                # empty Disallow restricts nothing.
                if current is not None and value:
                    current.rules.append(Rule(allow=(key == "allow"), path=value))
            elif key == "sitemap" and value:
                robots.sitemaps.append(value)
        return robots

    def rules_for(self, user_agent: str) -> list[Rule]:
        """Rules from every group naming this crawler's product token, or from
        every `*` group when none does (RFC 9309, section 2.2.1)."""
        token = _token(user_agent)
        named = [g for g in self.groups if token in g.agents]
        chosen = named or [g for g in self.groups if "*" in g.agents]
        return [rule for group in chosen for rule in group.rules]

    def allowed(self, user_agent: str, url: str) -> bool:
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        parts = urlsplit(url)
        target = unquote(parts.path or "/") + (f"?{unquote(parts.query)}" if parts.query else "")
        if target == "/robots.txt":
            return True

        best: Rule | None = None
        for rule in self.rules_for(user_agent):
            if not rule.matches(target):
                continue
            if (best is None or len(rule.path) > len(best.path)
                    or (len(rule.path) == len(best.path) and rule.allow and not best.allow)):
                best = rule
        return True if best is None else best.allow

    def describe(self, user_agent: str) -> list[str]:
        """The rules that apply to this crawler, for a scan's trace."""
        return [str(rule) for rule in self.rules_for(user_agent)]
