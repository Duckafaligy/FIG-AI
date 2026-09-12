"""Fills the database so the dashboard has something real in it.

The findings are not hand-typed. The seeder generates pages of varying quality
and runs them through the actual pipeline — parse_html, the rules engine,
scoring — so what you see on screen is genuinely what the checks produce.
Every site is an invented client of an invented agency; nothing here touches
the network or names a real business.

    python -m app.seed          # build it
    python -m app.seed --reset  # start over
    python -m app.seed --purge  # remove it once there is real data
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app import content
from app.auth import mint_key
from app.config import DEMO_ACCOUNT_SLUG
from app.db import init_db, session_scope
from app.models import (Account, ApiKey, ContentPost, Finding, Job, Page,
                        Scan, Site, User)
from app.rules.checks import run_all_checks
from app.rules.scoring import summarise
from app.rules.sections import roles_for
from app.scraper import parse_html

# --- the invented estate ------------------------------------------------

CLIENTS = [
    ("harborlinedental.com", "Harborline Dental", "slop"),
    ("keswick-legal.com", "Keswick Legal", "thin"),
    ("brightpathclinic.com", "Brightpath Clinic", "slop"),
    ("meridian-roofing.com", "Meridian Roofing", "order"),
    ("thistlebakery.co", "Thistle Bakery", "good"),
    ("kingsfordvets.com", "Kingsford Veterinary", "order"),
    ("aureliastudio.com", "Aurelia Studio", "good"),
    ("northgate-fitness.com", "Northgate Fitness", "slop"),
    ("copperfield-hvac.com", "Copperfield HVAC", "thin"),
    ("lark-accounting.com", "Lark Accounting", "order"),
    ("stonebridgeortho.com", "Stonebridge Orthodontics", "slop"),
    ("verdantlandscapes.co", "Verdant Landscapes", "good"),
    ("halcyon-interiors.com", "Halcyon Interiors", "thin"),
    ("pinewood-plumbing.com", "Pinewood Plumbing", "order"),
    ("summit-physio.com", "Summit Physiotherapy", "slop"),
    ("ridgelinelaw.com", "Ridgeline Law", "thin"),
    ("fernhill-optical.com", "Fernhill Optical", "order"),
    ("oakmontdental.co", "Oakmont Dental", "slop"),
    ("bramblecoffee.com", "Bramble Coffee", "good"),
    ("wexford-tiling.com", "Wexford Tiling", "thin"),
    ("cedarpoint-pt.com", "Cedar Point PT", "order"),
    ("marlowe-salon.com", "Marlowe Salon", "slop"),
]

PATHS = ["/", "/services", "/about", "/pricing", "/contact"]


# --- page fixtures ------------------------------------------------------
# Four shapes, matching the four things the checks look for. Each returns
# real HTML; the rules engine does the rest.


def _head(title: str, *, meta=True, canonical=True, lang=True, schema=True, host="") -> str:
    bits = [f"<title>{title}</title>"]
    if meta:
        bits.append(
            '<meta name="description" content="Appointments, opening hours and directions '
            'for a practice that has been on the same street since 1998.">')
    if canonical:
        bits.append(f'<link rel="canonical" href="https://{host}/">')
    if schema:
        bits.append('<script type="application/ld+json">'
                    '{"@context":"https://schema.org","@type":"LocalBusiness",'
                    f'"name":"{title}","telephone":"+1-555-0142"}}</script>')
    lang_attr = ' lang="en"' if lang else ""
    return f"<html{lang_attr}><head>{''.join(bits)}</head>"


def _slop_page(host: str, name: str, path: str) -> str:
    """The generated-page shape: numbered eyebrows, uniform cards, stock
    palette, the same four icons, filler copy, nothing in the head."""
    cards = "".join(
        f'<div class="rounded-2xl shadow-lg p-6"><h3>Elevate your {w}</h3>'
        f'<p>Seamlessly integrate best-in-class care and unlock your potential.</p></div>'
        for w in ("experience", "results", "routine", "confidence"))
    steps = "".join(
        f'<section><span>0{i}</span><h3>Step {i}</h3>'
        f'<p>Get started in minutes with our all-in-one solution.</p></section>'
        for i in (1, 2, 3))
    return f"""{_head(name, meta=False, canonical=False, lang=False, schema=False, host=host)}
<body>
  <section class="hero"><h3>{name}</h3>
    <p>Transform the way you think about care. Cutting-edge, next-generation, world-class.</p>
    <a class="btn" href="/contact">Get started</a></section>
  {steps}
  <section class="features"><h3>Features</h3>{cards}</section>
  <svg data-lucide="sparkles"></svg><svg data-lucide="arrow-right"></svg>
  <svg data-lucide="zap"></svg><svg data-lucide="check-circle"></svg>
  <style>.a{{color:#4F46E5}}.b{{background:#8B5CF6}}.c{{border-color:#6366F1}}</style>
  <img src="/a.jpg"><img src="/b.jpg"><img src="/c.jpg"><img src="/d.jpg">
  <footer><a href="/">Home</a><a href="/about">About</a><a href="/services">Services</a>
    <a href="/pricing">Pricing</a><a href="/contact">Contact</a><a href="/legal">Legal</a></footer>
</body></html>"""


def _order_page(host: str, name: str, path: str) -> str:
    """Competent page, wrong order: the price sits above the reason for it."""
    return f"""{_head(name, host=host)}
<body>
  <section id="hero"><h1>{name}</h1>
    <p>Same-day appointments on Bell Street, open since 1998.</p>
    <a class="btn" href="/book">Book</a></section>
  <section id="pricing"><h2>Pricing</h2>
    <p>Check-up $65. Hygiene $90 per visit. Emergency $140.</p>
    <p>Payment plans available over 6 or 12 months.</p></section>
  <section id="services"><h2>What we do</h2>
    <ul><li>Check-ups</li><li>Hygiene</li><li>Whitening</li><li>Emergency care</li>
        <li>Orthodontics</li><li>Implants</li></ul>
    <p>Eleven staff, two surgeries, 3,400 patients on the books as of March.</p></section>
  <section id="faq"><h2>Frequently asked questions</h2>
    <p>Do you take walk-ins? Yes, before 10am on weekdays.</p></section>
  <footer><a href="/">Home</a><a href="/about">About</a><a href="/services">Services</a>
    <a href="/pricing">Pricing</a><a href="/contact">Contact</a><a href="/legal">Legal</a></footer>
</body></html>"""


def _thin_page(host: str, name: str, path: str) -> str:
    """Almost nothing on it — the local-services page nobody finished."""
    return f"""{_head(name, meta=False, schema=False, host=host)}
<body>
  <section><h1>{name}</h1><p>Call us on 555-0142.</p></section>
  <footer><a href="/">Home</a></footer>
</body></html>"""


def _good_page(host: str, name: str, path: str) -> str:
    """What a finished page looks like: real hierarchy, specifics, structured
    data, an FAQ, and an order that makes its case before it asks."""
    return f"""{_head(name, host=host)}
<body>
  <header><h1>{name}</h1>
    <p>Sourdough and pastry, baked overnight on Wharf Road since 2016.</p></header>
  <section><h2>What we bake</h2>
    <p>Nine loaves and four pastries daily, out of the oven at 06:40.
       Everything is sold by 14:00 or given to the shelter on Palmer Street.</p>
    <ul><li>Country white, 900g</li><li>Rye, 750g</li><li>Seeded spelt, 800g</li>
        <li>Butter croissant</li><li>Almond twist</li><li>Cardamom bun</li></ul></section>
  <section><h2>How ordering works</h2>
    <p>Standing orders close Thursday at 18:00 for the following week.
       Collection is between 07:00 and 12:00.</p>
    <h3>Wholesale</h3><p>Twelve cafes across the city take a daily drop before 06:00.</p></section>
  <section><h2>Frequently asked questions</h2>
    <h3>Do you deliver?</h3><p>Not to homes. Wholesale drops only, inside the ring road.</p>
    <h3>Can I freeze the loaves?</h3><p>Yes, on the day. They keep about six weeks.</p></section>
  <section><h2>Visit</h2><p>41 Wharf Road. Tuesday to Saturday, 07:00 to 14:00.</p>
    <a class="btn" href="/orders">Start a standing order</a></section>
  <footer><a href="/">Home</a><a href="/about">About</a><a href="/orders">Orders</a>
    <a href="/wholesale">Wholesale</a><a href="/contact">Contact</a><a href="/legal">Legal</a></footer>
</body></html>"""


SHAPES = {"slop": _slop_page, "order": _order_page, "thin": _thin_page, "good": _good_page}


# --- build --------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def reset(session) -> None:
    for model in (ContentPost, Finding, Page, Scan, Job, ApiKey, Site):
        session.execute(delete(model))
    session.execute(delete(Account).where(Account.slug == DEMO_ACCOUNT_SLUG))
    session.commit()


def build(reset_first: bool = False) -> str:
    init_db()
    rng = random.Random(20260906)

    with session_scope() as session:
        if reset_first:
            reset(session)

        account = session.scalars(
            select(Account).where(Account.slug == DEMO_ACCOUNT_SLUG)).first()
        if account is None:
            account = Account(
                name="Northgate Digital", slug=DEMO_ACCOUNT_SLUG, kind="agency",
                contact_email="hello@northgate.example",
                white_label=True, brand_name="Northgate Digital",
                site_floor=20,
                trial_ends_at=_now() + timedelta(days=Account.TRIAL_DAYS),
            )
            session.add(account)
            session.flush()

        if not session.scalars(
                select(ApiKey).where(ApiKey.account_id == account.id)).first():
            mint_key(session, account, label="seed")

        existing = {s.hostname for s in account.sites}
        made = 0

        for i, (host, client, shape) in enumerate(CLIENTS):
            if host in existing:
                continue
            site = Site(account_id=account.id, hostname=host, client_name=client,
                        label=client, monitor=(i % 4 == 0), is_active=True)
            session.add(site)
            session.flush()

            # A little history, so the estate does not look like it was all
            # read in the same second.
            age_days = rng.randint(0, 9)
            finished = _now() - timedelta(days=age_days, minutes=rng.randint(0, 900))

            paths = PATHS[:rng.randint(3, 5)]
            signals = []
            for path in paths:
                html = SHAPES[shape](host, client, path)
                signals.append(parse_html(f"https://{host}{path}", html))

            flags = []
            scan = Scan(site_id=site.id, status="done", trigger="schedule" if site.monitor else "manual",
                        pages_crawled=len(signals), pages_requested=len(signals),
                        created_at=finished - timedelta(seconds=rng.randint(8, 40)),
                        started_at=finished - timedelta(seconds=rng.randint(8, 40)),
                        finished_at=finished)
            session.add(scan)
            session.flush()

            for sig in signals:
                sig.status_code = 200
                session.add(Page(
                    scan_id=scan.id, url=sig.url,
                    path=sig.url.split(host, 1)[1] or "/",
                    title=sig.title, status_code=200, word_count=sig.word_count,
                    section_roles=roles_for(sig), fetched_at=finished,
                ))
                flags.extend(run_all_checks(sig))

            for f in flags:
                session.add(Finding(
                    scan_id=scan.id, page_url=f.page_url or None, check=f.check,
                    layer=f.layer, severity=f.severity, weight=f.weight,
                    summary=f.summary, why=f.why or None, fix=f.fix or None,
                    evidence=list(f.evidence) if f.evidence else None,
                    count=f.count, created_at=finished,
                ))

            result = summarise(flags, pages=len(signals))
            scan.score = result["overall"]
            scan.score_craft = result["layers"]["craft"]
            scan.score_structure = result["layers"]["structure"]
            scan.score_search = result["layers"]["search"]
            scan.score_answers = result["layers"]["answers"]
            site.last_scanned_at = finished
            made += 1

        session.flush()
        session.refresh(account)
        briefs = seed_content(session, account)
        session.commit()
        session.refresh(account)          # the relationship was loaded empty
        return (f"{account.name}: {account.billable_sites()} sites "
                f"({made} added this run), "
                f"estate ${account.monthly_cents() / 100:.2f}/mo, "
                f"{briefs} content briefs")


# --- the content queue --------------------------------------------------


def _draft(topic: str, host: str, name: str, quality: str) -> str:
    """A draft good enough to score honestly.

    `quality` decides which of the nine checks pass, so the rings on the page
    spread out for a real reason rather than because a number was typed in.
    """
    # The opening sentence doubles as the meta description, so it is written
    # to land inside the 110-158 characters a search result will show.
    lead = (f"{topic}? Between $1,200 and $4,500 for most jobs, in 3 to 5 days, "
            f"and here is exactly what moves that number. "
            f"What follows is what {name} tells people who ring up and ask, in "
            f"the same order we say it on the phone. None of it is a range "
            f"invented to look reassuring.")
    if quality == "high":
        return "\n\n".join([
            f"# {topic}",
            lead,
            "## The short answer",
            f"Most jobs run 3 to 5 days and land between $1,200 and $4,500 "
            f"depending on access and materials. {name} has done 340 of these "
            f"since 2019, so those are measured figures rather than a range "
            f"pulled from the air.",
            "## What actually drives the number",
            "Three things move the price, in this order: how hard the site is to "
            "reach, how much of the old work has to come out first, and whether "
            "the job needs a permit. Access is the one people underestimate — a "
            "second-floor job with no side entry adds about 8 hours of labour.",
            "## How long does it take?",
            "Four days is typical. One day for strip-out, two for the work "
            "itself, one for making good. Weather adds a day in winter roughly "
            "one job in five.",
            "## What you should ask before booking anyone",
            "Ask for the last three addresses they worked at and ring one. Ask "
            "whether the quote includes disposal — about 30% of the complaints "
            "we hear about start there. Ask who is actually on site, because it "
            "is often not the person quoting, and ask what happens to the price "
            "if the job runs a day long. A firm answer to all four is a better "
            "signal than any review page.",
            "## Why the cheapest quote usually is not",
            "We get called out to finish somebody else's work about twice a "
            "month. The pattern is the same nearly every time: the quote left "
            "out disposal, or it assumed the substrate underneath was sound "
            "without anybody lifting a board to check. Both come back as a "
            "variation once the work has started and you have nobody else "
            "lined up. A quote that names the things it has excluded is worth "
            "more than one that is 15% lower and silent about them.",
            "## What the work looks like day by day",
            "Day one is strip-out and protection. Everything that is coming "
            "out comes out, the route in gets boarded, and anything staying "
            "gets sheeted. Day two and three are the work itself, and this is "
            "the part that varies — if the substrate needs making good first, "
            "that lands here and it is where a day gets added. Day four is "
            "making good, cleaning, and walking the job with you before "
            "anybody leaves. You get photographs of anything that was covered "
            "up, which matters in two years when somebody asks what is behind "
            "the wall.",
            "## Does it need a permit?",
            "For most jobs, no. Structural changes, anything touching a shared "
            "wall, and anything in a conservation area do, and that adds two to "
            "six weeks before a start date. We check this before quoting rather "
            "than after, because a job that cannot start for a month is a "
            "different decision than one that can start next week.",
            "## When is the right time of year",
            "Between March and October if the work involves anything exterior. "
            f"{name} still books winter work and about 60% of what we do is "
            "unaffected by weather, but a job with two days of outside work in "
            "January should have a day of slack in it and a quote that says so.",
            "## What we will not do",
            "We will not quote without seeing photographs at minimum, and for "
            "anything over $2,500 we will not quote without visiting. A number "
            "given over the phone with no information is a number that changes, "
            "and the change always goes one way. If somebody has given you a "
            "firm price sight unseen, that is worth asking about.",
            f"See our [pricing](/pricing) for the current schedule and the "
            f"[process page](/process) for what each day looks like. If you want "
            f"a figure for your own place, {name} will look at photos first and "
            f"tell you whether a visit is even needed. Most people who ring us "
            f"have already had one quote and want to know whether it was fair. "
            f"That is a reasonable thing to ask and we will tell you when it "
            f"was, which is more often than you would think.",
        ])
    if quality == "mid":
        return "\n\n".join([
            f"# {topic}",
            lead,
            "## The short answer",
            "It depends on the property, but most jobs are finished inside a "
            "week and the cost is in line with what you would expect locally. "
            "We will give you a firm number before anything starts.",
            "## What to expect",
            "We turn up when we say we will, we clear up after ourselves, and "
            "we tell you if we find something that changes the price rather than "
            "adding it to the invoice at the end.",
            "## Getting a number",
            f"Have a look at our [services](/services) or get in touch and "
            f"somebody at {name} will talk it through.",
        ])
    return "\n\n".join([
        f"# {topic}",
        f"Elevate your experience with {name}. Our seamless, innovative approach "
        f"unlocks the full potential of your property while delivering "
        f"best-in-class outcomes at every touchpoint.",
        "Get in touch today to learn more about how we can transform your space.",
    ])


CONTENT_PLAN = [
    # (state, quality, priority, days from now)
    ("published", "high", "high", -22),
    ("published", "high", "medium", -11),
    ("published", "mid", "low", -4),
    ("scheduled", "high", "high", 3),
    ("scheduled", "mid", "medium", 6),
    ("scheduled", "mid", "low", 9),
    ("review", "mid", "high", None),
    ("review", "low", "low", None),
    ("review", "mid", "medium", None),
    ("in_progress", "low", "medium", None),
    ("in_progress", "mid", "high", None),
    ("in_progress", "low", "low", None),
]


def seed_content(session, account: Account) -> int:
    """Build briefs from the audits, then take some of them forward.

    Briefs come from `content.propose`, which reads the real findings. The
    drafts are fixtures; the scores on them are not — every ring on the page is
    `content.score_post` run over the text that is actually stored.
    """
    if session.scalars(select(ContentPost).limit(1)).first() is not None:
        return 0

    sites = [s for s in account.sites if s.is_active]
    made = 0
    for site in sites:
        made += len(content.propose(session, site, limit=3))
    session.flush()

    posts = session.scalars(
        select(ContentPost).where(
            ContentPost.site_id.in_([s.id for s in sites]))).all()
    rng = random.Random(7)
    rng.shuffle(posts)
    by_id = {s.id: s for s in sites}

    for post, (state, quality, priority, days) in zip(posts, CONTENT_PLAN):
        site = by_id[post.site_id]
        topic = (post.target_keyword or post.title).strip().capitalize()
        post.body = _draft(topic, site.hostname,
                           site.client_name or site.hostname, quality)
        post.priority = priority
        post.state = state
        if days is not None:
            when = _now() + timedelta(days=days)
            post.scheduled_for = when
            if state == "published":
                post.published_at = when
        content.rescore(post)

    session.flush()
    return made


def purge() -> str:
    """Delete the demo estate entirely.

    The seeded agency is scaffolding for looking at the UI with data in it. Once
    there are real sites in here it is just noise, and a dashboard showing
    twenty-three invented clients does not look like a product anyone is using.
    """
    with session_scope() as session:
        account = session.scalars(
            select(Account).where(Account.slug == DEMO_ACCOUNT_SLUG)).first()
        if account is None:
            return "no demo estate to remove"
        n = len(account.sites)
        users = session.scalars(
            select(User).where(User.account_id == account.id)).all()
        for u in users:                       # detach before the account goes
            u.account_id = None
        session.flush()
        session.delete(account)               # cascades to sites, scans, findings
        return (f"removed the demo estate: {n} sites"
                + (f", {len(users)} user(s) left without a workspace" if users else ""))


if __name__ == "__main__":
    if "--purge" in sys.argv:
        print(purge())
    else:
        print(build(reset_first="--reset" in sys.argv))
