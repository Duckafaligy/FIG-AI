# Test Runs

End-to-end runs of the FIG backend against real sites, newest at the bottom.
Each is produced by `python scripts/test_run.py <site>`: it starts the API
disconnected from the frontend, drives it over HTTP the way a client would,
and records the validation system, every pipeline stage, what the AI step
cost, and what was found.

---

## Test #1 — launchvault.ca

**PASS** · 53/53 checks passed · 2026-09-15 18:22 (UTC-0400) · 57.7 s total · `python scripts/test_run.py Launchvault.ca`

| | |
|---|---|
| Target | `Launchvault.ca` → `launchvault.ca` (172.64.80.1) |
| Scan | `done` · 40 pages read, 0 skipped · 48.0 s from queue to done |
| Score | **70 / 100 — check** · Craft 75 · Structure 50 · Search 81 · Answers 75 |
| Findings | 147 findings across 10 distinct problems · 10 of 10 explained by Claude |
| AI step | `claude-haiku-4-5` (served as `claude-haiku-4-5-20251001`) · 2 calls · 2,242 in / 919 out tokens · **$0.0068** |
| Backend | `http://127.0.0.1:52884` · Postgres (aws-1-us-east-2.pooler.supabase.com) · workspace API off · up in 3.2 s |

### 1. Environment

- **Database:** Postgres (aws-1-us-east-2.pooler.supabase.com) — `FIG_DB_STRICT=1`, so an unreachable database fails the run instead of falling back to SQLite. Schema check (`init_db`) took 578 ms.
- **AI:** key present, model `claude-haiku-4-5`, priced at $1.00 in / $5.00 out per million tokens.
- **Crawler:** user agent `FIGBot/0.2 (+https://fig.tools/bot; site self-check and structure scanner)`, 0.8 s between requests to a host, up to 40 pages, 5,120.0 KB per response, 5 redirects.
- **Server:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 52884 --log-level info` with `FIG_WORKSPACE_API=0`, Python 3.12.10.

### 2. Routes

| # | Step | Request | Expected | Got | Time | | Note |
|---|---|---|---|---|---|---|---|
| 1 | service | `GET /` | 200 | 200 | 15 ms | ✅ | — |
| 2 | service | `GET /health` | 200 | 200 | 63 ms | ✅ | — |
| 3 | frontend disconnected | `GET /api/me` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 4 | frontend disconnected | `GET /api/projects` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 5 | frontend disconnected | `OPTIONS /v1/sites` | 400/405 | 405 | 0 ms | ✅ | CORS preflight from the Next.js dev origin |
| 6 | auth | `GET /v1/account` | 401 | 401 | 0 ms | ✅ | no key |
| 7 | auth | `GET /v1/account` | 401 | 401 | 78 ms | ✅ | wrong key |
| 8 | auth | `GET /v1/account` | 200 | 200 | 391 ms | ✅ | key minted for this run |
| 9 | validation | `POST /v1/sites` | 422 | 422 | 171 ms | ✅ | loopback address |
| 10 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | cloud metadata endpoint |
| 11 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | private address on a non-standard port |
| 12 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | 127.0.0.1 written as a number |
| 13 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | reserved name |
| 14 | validation | `POST /v1/sites` | 422 | 422 | 171 ms | ✅ | internal-only suffix |
| 15 | validation | `POST /v1/sites` | 422 | 422 | 313 ms | ✅ | real public DNS name that resolves to 127.0.0.1 |
| 16 | validation | `POST /v1/sites` | 422 | 422 | 234 ms | ✅ | domain that does not exist |
| 17 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | non-web scheme |
| 18 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | not a hostname at all |
| 19 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | empty input |
| 20 | validation | `POST /scan` | 422 | 422 | 16 ms | ✅ | the free public read goes through the same gate |
| 21 | provision | `POST /v1/sites` | 201 | 201 | 296 ms | ✅ | as typed |
| 22 | provision | `POST /v1/sites` | 201 | 201 | 204 ms | ✅ | same site given as a full URL |
| 23 | provision | `GET /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd` | 200 | 200 | 187 ms | ✅ | — |
| 24 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification` | 200 | 200 | 203 ms | ✅ | issue a DNS TXT token |
| 25 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification/confirm` | 200 | 200 | 203 ms | ✅ | look the record up |
| 26 | scan | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/scans` | 202 | 202 | 250 ms | ✅ | queued for a worker |
| 27 | scan | `GET /v1/scans/85f6adc4-40d9-4628-9421-60843111cf53?findings=false` | 200 | 200 | 214 ms | ✅ | polled 28x every 1.5s until done (ms is the average) |
| 28 | results | `GET /v1/scans/85f6adc4-40d9-4628-9421-60843111cf53` | 200 | 200 | 391 ms | ✅ | scores and findings |
| 29 | results | `GET /v1/scans/85f6adc4-40d9-4628-9421-60843111cf53/pages` | 200 | 200 | 219 ms | ✅ | pages read |
| 30 | results | `GET /v1/scans/85f6adc4-40d9-4628-9421-60843111cf53/trace` | 200 | 200 | 187 ms | ✅ | stage-by-stage trace |
| 31 | results | `GET /v1/report` | 200 | 200 | 250 ms | ✅ | partner estate roll-up |
| 32 | results | `GET /v1/scans/not-a-real-scan` | 404 | 404 | 188 ms | ✅ | unknown scan id |

### 3. Validation system

**Accepted:** `Launchvault.ca` → `launchvault.ca` (nothing to change). Resolved to 172.64.80.1 — every address public, so the crawl was allowed. The same site given as `https://Launchvault.ca/pricing?utm_source=fig-test` normalised to the same hostname and returned the existing site.

**Ownership:** DNS TXT verification was issued and checked — verified: `False`. Ownership is only required to schedule monitoring; a one-off scan of any public site is allowed without it.

**Rejected** (each is a `POST /v1/sites`, answered before anything is fetched):

| Input | What it is | HTTP | Code | Expected | | Message |
|---|---|---|---|---|---|---|
| `127.0.0.1` | loopback address | 422 | `ip_literal` | `ip_literal` | ✅ | 127.0.0.1 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `169.254.169.254` | cloud metadata endpoint | 422 | `ip_literal` | `ip_literal` | ✅ | 169.254.169.254 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `http://10.0.0.1:8080/admin` | private address on a non-standard port | 422 | `has_port` | `has_port` | ✅ | Port 8080 is not supported. Give the site's hostname; sites are read over the standard ports. |
| `2130706433` | 127.0.0.1 written as a number | 422 | `bad_hostname` | `bad_hostname` | ✅ | '2130706433' does not look like a public domain name. |
| `localhost` | reserved name | 422 | `reserved_name` | `reserved_name` | ✅ | localhost is under the reserved name 'localhost', which never points at a public website. |
| `printer.internal` | internal-only suffix | 422 | `reserved_name` | `reserved_name` | ✅ | printer.internal is under the reserved name 'internal', which never points at a public website. |
| `127.0.0.1.nip.io` | real public DNS name that resolves to 127.0.0.1 | 422 | `non_public_address` | `non_public_address` | ✅ | 127.0.0.1.nip.io resolves to 127.0.0.1, which is not on the public internet. FIG only reads public sites. |
| `fig-nx-742d286ed7.com` | domain that does not exist | 422 | `dns_failed` | `dns_failed` | ✅ | fig-nx-742d286ed7.com does not resolve ([Errno 11001] getaddrinfo failed). |
| `ftp://launchvault.ca` | non-web scheme | 422 | `bad_scheme` | `bad_scheme` | ✅ | Only http and https sites can be read, not ftp://. |
| `not a hostname` | not a hostname at all | 422 | `bad_hostname` | `bad_hostname` | ✅ | 'not a hostname' contains spaces, so it is not a hostname or URL. |
| `(empty)` | empty input | 422 | `empty` | `empty` | ✅ | No hostname or URL was given. |

### 4. Pipeline

Trace total: 47.6 s inside the worker.

| Stage | Status | Time | What happened |
|---|---|---|---|
| `validate` | ok | 0 ms | launchvault.ca → launchvault.ca → 172.64.80.1 (all public) |
| `resolve_base` | ok | 1.2 s | https://launchvault.ca — tried: https://launchvault.ca/ ok 200 |
| `robots` | ok | 250 ms | parsed (HTTP 200) · 10 rules apply to FIGBot · 1 sitemap(s) declared |
| `discover` | ok | 2.0 s | 1 sitemap file(s) read · 500 URLs listed · 500 on this site |
| `fetch` | ok | 32.2 s | 40 read · skipped: none · page limit reached |
| `rules` | ok | 62 ms | 147 flags from 10 distinct checks (craft 64, search 14, answers 38, structure 31) |
| `explain` | ok | 12.0 s | 10/10 distinct findings explained in 2 calls · 2,242 in / 919 out tokens · $0.0068 |
| `score` | ok | 0 ms | overall 70 (check) · {'craft': 75, 'structure': 50, 'search': 81, 'answers': 75} |
| `persist` | ok | 203 ms | 40 pages and 147 findings saved, 147 with Claude-written text |

#### robots.txt

`https://launchvault.ca/robots.txt` → HTTP 200, outcome **parsed**, read in 250 ms.

Rules that apply to FIGBot (enforced before every request, including redirect hops):

```text
Allow: /
Allow: /features
Allow: /pricing
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /cookies
Allow: /refund-policy
Allow: /acceptable-use
Allow: /dpa
```

- Declared sitemap: `https://launchvault.ca/sitemap.xml`

#### Discovery

| Sitemap | Outcome | HTTP | URLs | Child sitemaps | Time |
|---|---|---|---|---|---|
| `https://launchvault.ca/sitemap.xml` | ok | 200 | 1069 | 0 | 2.0 s |

#### Pages

40 read, 0 skipped; stopped because: page limit reached.

| # | Path | Outcome | HTTP | Size | Time | Note |
|---|---|---|---|---|---|---|
| 1 | `/` | ✅ read | 200 | 149.8 KB | 1.2 s | “LaunchVault — Learn AI in Plain English. No Jargon, No Rush.” · 1682 words · sections: hero, content, features, content, features, content, pricing, content, content, faq, content, cta |
| 2 | `/learn-ai` | ✅ read | 200 | 40.8 KB | 719 ms | “Learn AI — Free AI Learning Platform to Master AI \| LaunchVault” · 808 words · sections: hero, content, content, content, faq, content |
| 3 | `/how-to-learn-ai` | ✅ read | 200 | 37.6 KB | 375 ms | “How to Learn AI in 2026 — Step-by-Step Guide \| LaunchVault” · 637 words · sections: hero, content, faq |
| 4 | `/features` | ✅ read | 200 | 57.2 KB | 844 ms | “AI Learning Platform Features — Prompts, Courses & AI Agents \| LaunchVault” · 827 words · sections: hero, content, content, content, content, content, content |
| 5 | `/how-it-works` | ✅ read | 200 | 48.9 KB | 750 ms | “How to Learn AI with LaunchVault — How It Works” · 604 words · sections: hero, how, features, content, pricing, content |
| 6 | `/pricing` | ✅ read | 200 | 101.4 KB | 828 ms | “Pricing — AI Learning Platform Plans to Learn AI \| LaunchVault” · 903 words · sections: hero, content, content, content, pricing, content, content, cta, content |
| 7 | `/library` | ✅ read | 200 | 134.9 KB | 1.4 s | “AI Prompt Library & Courses — Learn AI Free \| LaunchVault” · 1543 words · sections: hero, testimonials, pricing |
| 8 | `/glossary` | ✅ read | 200 | 258.4 KB | 703 ms | “AI Glossary — AI Terms & Concepts Explained Simply \| LaunchVault” · 2208 words · sections: hero, content, how |
| 9 | `/blog` | ✅ read | 200 | 161.6 KB | 516 ms | “Learn AI — Guides & Essays on Using AI \| LaunchVault Blog” · 1728 words · sections: hero, content, content, footer, content |
| 10 | `/about` | ✅ read | 200 | 49.8 KB | 641 ms | “About LaunchVault — How Our AI Learning Platform Works” · 793 words · sections: hero, content, content, content, content, content, content |
| 11 | `/contact` | ✅ read | 200 | 28.4 KB | 735 ms | “Contact — LaunchVault” · 250 words · sections: hero, content, content |
| 12 | `/signup` | ✅ read | 200 | 20.9 KB | 828 ms | “Sign up — LaunchVault” · 157 words · sections: hero, content |
| 13 | `/login` | ✅ read | 200 | 17.5 KB | 812 ms | “Log in — LaunchVault” · 102 words · sections: hero, social_proof |
| 14 | `/privacy` | ✅ read | 200 | 33.7 KB | 813 ms | “Privacy Policy — LaunchVault” · 1003 words · sections: hero, content, footer, content |
| 15 | `/terms` | ✅ read | 200 | 35.0 KB | 812 ms | “Terms of Service — LaunchVault” · 1089 words · sections: hero, content, footer, content |
| 16 | `/cookies` | ✅ read | 200 | 27.8 KB | 984 ms | “Cookie Policy — LaunchVault” · 441 words · sections: hero, content, footer, content |
| 17 | `/refund-policy` | ✅ read | 200 | 29.2 KB | 641 ms | “Cancellation Policy — LaunchVault” · 619 words · sections: hero, content, footer, content |
| 18 | `/acceptable-use` | ✅ read | 200 | 28.5 KB | 781 ms | “Acceptable Use Policy — LaunchVault” · 602 words · sections: hero, content, footer, content |
| 19 | `/dpa` | ✅ read | 200 | 30.1 KB | 812 ms | “Data Processing Addendum — LaunchVault” · 607 words · sections: hero, content, footer, content |
| 20 | `/domains/ai-prompting-mastery` | ✅ read | 200 | 86.7 KB | 922 ms | “AI Prompting Mastery — LaunchVault” · 1075 words · sections: hero, content, content, content |
| 21 | `/domains/prompt-engineering-fundamentals` | ✅ read | 200 | 76.4 KB | 1.0 s | “Prompt Engineering Fundamentals — LaunchVault” · 934 words · sections: hero, content, content, content |
| 22 | `/domains/advanced-prompt-engineering` | ✅ read | 200 | 84.5 KB | 547 ms | “Advanced Prompt Engineering — LaunchVault” · 1039 words · sections: hero, content, content, content |
| 23 | `/domains/ai-for-business` | ✅ read | 200 | 85.2 KB | 765 ms | “AI for Business — LaunchVault” · 1043 words · sections: hero, content, content, content |
| 24 | `/domains/ai-business-models` | ✅ read | 200 | 84.7 KB | 812 ms | “AI Business Models — LaunchVault” · 1039 words · sections: hero, pricing, content, content |
| 25 | `/domains/ai-monetization` | ✅ read | 200 | 88.6 KB | 953 ms | “AI Monetization — LaunchVault” · 1081 words · sections: hero, content, content, content |
| 26 | `/domains/ai-automation-workflows` | ✅ read | 200 | 75.8 KB | 688 ms | “AI Automation & Workflows — LaunchVault” · 916 words · sections: hero, how, content, content |
| 27 | `/domains/no-code-ai-automation` | ✅ read | 200 | 88.5 KB | 906 ms | “No-Code AI Automation — LaunchVault” · 1082 words · sections: hero, content, content, content |
| 28 | `/domains/ai-agents-blueprints` | ✅ read | 200 | 111.9 KB | 656 ms | “AI Agents & Blueprints — LaunchVault” · 1454 words · sections: hero, content, content, content |
| 29 | `/domains/multi-agent-systems` | ✅ read | 200 | 92.9 KB | 781 ms | “Multi-Agent Systems — LaunchVault” · 1073 words · sections: hero, content, content, content |
| 30 | `/domains/agent-memory-tool-use` | ✅ read | 200 | 77.8 KB | 781 ms | “Agent Memory & Tool Use — LaunchVault” · 946 words · sections: hero, content, content, content |
| 31 | `/domains/machine-learning-basics` | ✅ read | 200 | 108.1 KB | 1.1 s | “Machine Learning Basics — LaunchVault” · 1399 words · sections: hero, content, content, content |
| 32 | `/domains/deep-learning-basics` | ✅ read | 200 | 84.8 KB | 563 ms | “Deep Learning Basics — LaunchVault” · 1041 words · sections: hero, content, content, content |
| 33 | `/domains/data-literacy-for-ai` | ✅ read | 200 | 69.8 KB | 765 ms | “Data Literacy for AI — LaunchVault” · 865 words · sections: hero, content, content, content |
| 34 | `/domains/ai-coding-development` | ✅ read | 200 | 78.8 KB | 1.8 s | “AI Coding & Development — LaunchVault” · 981 words · sections: hero, testimonials, content, content |
| 35 | `/domains/ai-app-building` | ✅ read | 200 | 65.9 KB | 359 ms | “AI App Building — LaunchVault” · 797 words · sections: hero, content, content, content |
| 36 | `/domains/ai-saas-building` | ✅ read | 200 | 70.4 KB | 828 ms | “AI SaaS Building — LaunchVault” · 865 words · sections: hero, content, content, content |
| 37 | `/domains/ai-productivity` | ✅ read | 200 | 88.8 KB | 735 ms | “AI Productivity & Personal Use — LaunchVault” · 1122 words · sections: hero, content, content, content |
| 38 | `/domains/ai-content-creation` | ✅ read | 200 | 72.3 KB | 813 ms | “AI Content Creation — LaunchVault” · 871 words · sections: hero, content, content, content |
| 39 | `/domains/ai-copywriting` | ✅ read | 200 | 64.8 KB | 812 ms | “AI Copywriting — LaunchVault” · 770 words · sections: hero, content, content, content |
| 40 | `/domains/ai-marketing` | ✅ read | 200 | 87.0 KB | 953 ms | “AI Marketing — LaunchVault” · 1072 words · sections: hero, content, content, content |

#### Rules

147 flags over 40 pages. Deterministic — no model involved.

| Check | Layer | Times flagged |
|---|---|---|
| `overused_icons` | craft | 40 |
| `no_answerable_questions` | answers | 38 |
| `heading_skips` | structure | 23 |
| `generic_copy` | craft | 13 |
| `numbered_eyebrows` | craft | 11 |
| `meta_description_length` | search | 11 |
| `section_order` | structure | 7 |
| `missing_canonical` | search | 2 |
| `title_length` | search | 1 |
| `thin_page` | structure | 1 |

#### AI step (the only model call in the pipeline)

- Sent **10 items** (one per distinct finding) instead of 147 — a check that fires on many pages is explained once.
- Model `claude-haiku-4-5`, served as `claude-haiku-4-5-20251001`: 2 calls, 0 failed batches.
- Tokens: 2,242 input, 919 output → **$0.0068**.
- Explained 10, kept the rule's own text for 0.
- Request ids: `req_011Cf61QDRtjnaFgDzLB4Nq7`, `req_011Cf61QkKGE1Rm7xhFH4fUW`

#### Scores

| Layer | Score |
|---|---|
| Craft | 75 |
| Structure | 50 |
| Search | 81 |
| Answers | 75 |
| **Overall** | **70 — check** |

### 5. Findings

#### Craft (75/100)

- **`generic_copy`** · medium · 13× on 13 pages (/how-it-works, /, /about, /domains/prompt-engineering-fundamentals…) · _Claude-written_
  - **Found:** 1 instance(s) of generic marketing phrasing found in headings/copy
  - **Why:** Phrases like "Supercharge" and "The Future of Work" appear frequently across sites and may dilute your distinctive voice in search results and reader memory.
  - **Fix:** Replace "Supercharge Your Prompts with Context" with a specific benefit: "Add domain knowledge to prompts — get smarter AI outputs." Audit the 13 pages and rewrite using concrete outcomes.
- **`overused_icons`** · low · 40× on 40 pages (/cookies, /refund-policy, /domains/ai-productivity, /learn-ai…) · _Claude-written_
  - **Found:** 3 uses of icons commonly overused in generated UI (chevron-right, sparkles)
  - **Why:** Overused icon sets (arrow-right, sparkles, rocket) are common in template designs and may make your site feel less intentional, especially with 40 instances.
  - **Fix:** Reduce arrow-right from 16 to 3–4 uses (only for navigation). Replace sparkles (9 uses) with a single icon for premium features. Keep others minimal and purposeful.
- **`numbered_eyebrows`** · low · 11× on 11 pages (/cookies, /refund-policy, /acceptable-use, /dpa…) · _Claude-written_
  - **Found:** Found 6 short numbered labels (01, 02, 03, 04, 05) — a common auto-generated 'step/feature' eyebrow pattern
  - **Why:** Numbered labels without context read as placeholder text and suggest the page wasn't fully customized. Readers scan past generic structure markers.
  - **Fix:** Replace numbered labels with descriptive headings. Instead of "4", write "What You'll Build" or "Track Your Progress." Review all 11 pages and audit each number's purpose.

#### Structure (50/100)

- **`section_order`** · high · 7× on 7 pages (/acceptable-use, /terms, /privacy, /blog…) · _Claude-written_
  - **Found:** On /acceptable-use, 1 block(s) render below the footer
  - **Why:** Content below the footer is hard to discover and appears unintentional. Search crawlers may deprioritize or miss material in this position.
  - **Fix:** On /blog and /acceptable-use, move the body content block that appears after footer markup to its proper position before the footer element in the DOM.
- **`thin_page`** · medium · 1× on 1 page (/login) · _Claude-written_
  - **Found:** Only 102 words of body copy on this page
  - **Why:** 102 words of body copy is thin for meaningful indexing and ranking. Crawlers and users both need sufficient content to understand the page's purpose.
  - **Fix:** Expand /login with actual body content—purpose statement, benefits, or next steps—to at least 200–300 words alongside the login form.
- **`heading_skips`** · low · 23× on 23 pages (/domains/machine-learning-basics, /domains/deep-learning-basics, /domains/ai-prompting-mastery, /domains/ai-productivity…) · _Claude-written_
  - **Found:** 2 places where the heading level jumps more than one step
  - **Why:** Skipping heading levels breaks the logical hierarchy readers use to scan and navigate. Screen readers and crawlers rely on proper nesting to understand page structure.
  - **Fix:** On /domains/advanced-prompt-engineering and similar pages, change h3 headings that follow h1 to h2, and h4 after h2 to h3. Maintain one-level increments.

#### Search (81/100)

- **`meta_description_length`** · low · 11× on 11 pages (/learn-ai, /, /features, /how-it-works…) · _Claude-written_
  - **Found:** Meta description is 202 characters (long)
  - **Why:** At 194 characters, your meta description is cut off at ~160 in most search results, losing key differentiators and call-to-action.
  - **Fix:** Trim to 150 characters max. Example: "Learn AI practically with prompts, courses & agents across 50 topics. Start free, no jargon." Test on Google's SERP preview tool.
- **`missing_canonical`** · low · 2× on 2 pages (/signup, /login) · _Claude-written_
  - **Found:** No canonical link on this page
  - **Why:** Without a canonical tag, search engines may treat /login and /signup as duplicate or conflicting versions, splitting ranking signals between them.
  - **Fix:** Add `<link rel="canonical" href="https://yourdomain.com/login">` to the <head> of /login, and the same pattern with /signup URL on that page.
- **`title_length`** · low · 1× on 1 page (/features) · _Claude-written_
  - **Found:** Title is 74 characters and will be truncated
  - **Why:** At 74 characters, the /features title is cut off in browser tabs and search results, losing the keyword "Features" and site name visibility.
  - **Fix:** Shorten to 60 characters: "LaunchVault Features: Prompts, Courses & AI Agents." Keeps brand and top keyword visible.

#### Answers (75/100)

- **`no_answerable_questions`** · medium · 38× on 38 pages (/, /learn-ai, /how-to-learn-ai, /features…) · _Claude-written_
  - **Found:** No question-and-answer block on this page
  - **Why:** Pages without Q&A blocks give AI answer engines no structured claims to quote or cite, reducing your visibility in generative search results.
  - **Fix:** Add one FAQ block per page type. On /features, include: "What makes LaunchVault different?" with a 2-sentence answer. Use schema.org FAQPage markup.

### 6. Database cross-check

| | Database | API |
|---|---|---|
| Scan status | done | done |
| Findings | 147 | 147 |
| AI-written findings | 147 | 147 |
| Pages | 40 | 40 |
| Trace stored | True | True |
| Queue job | done, attempt 1 | — |

### 7. Checks

- ✅ **preflight** — database is Postgres, not a SQLite fallback
- ✅ **preflight** — Anthropic API key is set
- ✅ **preflight** — ai_explain is enabled
- ✅ **preflight** — scans.trace column exists
- ✅ **preflight** — API key minted on account `test-runs`
- ✅ **server** — backend answers /health
- ✅ **routes** — root lists the workspace API as not mounted
- ✅ **routes** — /health reports Postgres, ai_explain on, workspace API off
- ✅ **routes** — no browser origin is allowed (no CORS headers returned)
- ✅ **validation** — every unsafe target answered with the expected reason code
- ✅ **provision** — `Launchvault.ca` stored as `launchvault.ca`
- ✅ **provision** — the URL form resolves to the same site (no duplicate)
- ✅ **ownership** — unverified (no TXT record) -- and a one-off scan is still allowed
- ✅ **scan** — scan finished as `done`
- ✅ **results** — trace covers every pipeline stage
- ✅ **results** — report lists this site
- ✅ **database** — findings in the database match the API
- ✅ **database** — AI-written flags match the API
- ✅ **database** — pages in the database match the API
- ✅ **database** — trace stored on the scan row
- ✅ **database** — queue job finished on its first attempt
- Plus 32 route calls in section 2, 32 as expected.

### 8. Issues observed

- None.

### 9. Server log (application lines, redacted)

```text
2026-09-15 18:22:56,000 INFO fig.jobs: worker w1 up
2026-09-15 18:22:56,001 INFO fig.jobs: worker w2 up
2026-09-15 18:22:56,001 INFO fig: FIG API up - db postgres, ai_explain claude-haiku-4-5, workspace API off (disconnected from the frontend)
2026-09-15 18:23:49,512 INFO fig.pipeline: scan 85f6adc4-40d9-4628-9421-60843111cf53 done: 40 pages, score 70, 47625 ms
```

### 10. Review notes (added after the run, from reading the results)

Every check passed, but reading the output turned up three real problems. No check in this run could fail on any of them, which is why they are written down here rather than hidden behind the green result.

1. **robots.txt was not honoured.** The scan read `/login` and `/signup`, which launchvault.ca disallows. The robots section above shows why: only the 10 `Allow` lines were picked up. Python's `urllib.robotparser` ends a group at a blank line; this file has one between its Allow and Disallow blocks, so all 6 `Disallow` lines were silently dropped, and even without the blank line it applies the first matching rule in file order, so `Allow: /` would still have won (checked: with no blank line, urllib still allows `/login`). Checked directly against the live file: urllib says `/login`, `/signup`, `/dashboard`, `/api/...` and `/checkout` are all allowed. RFC 9309 (and Google) ignore blank lines and use the longest match, under which all six are disallowed. **Fixed:** `app/robots.py`, an RFC 9309 parser, replaces urllib, and the harness now checks every page read against an independent reading of the file.
2. **`section_order` (high, 7 legal pages) was a false positive.** The block "below the footer" on `/acceptable-use`, `/privacy`, `/terms` and the rest is an empty `<section>` with zero words: a mount point, not content. It alone pulled Structure down to 50. **Fixed:** empty blocks are no longer counted as sections.
3. **`no_answerable_questions` fired on the homepage**, which has `<section id="faq">` titled "Questions, answered" with nine question headings. The check only recognised FAQPage markup or a heading starting with "FAQ". **Fixed:** a section named or labelled as an FAQ, or two or more question headings, now counts.

Checked and fine: Claude's explanations cite specifics like "arrow-right 16 uses", "sparkles 9" and "50 AI topics", and all of them are in the evidence it was sent, not invented. Where a number differs from the "Found" line (194 vs 202 characters), that line shows a different page's example than the one Claude received. One real nit: the canonical-tag fix used a placeholder domain because the model was never told the hostname. **Fixed:** the AI step now receives it.

---

## Test #2 — launchvault.ca

**PASS** · 54/54 checks passed · 2026-09-15 18:36 (UTC-0400) · 54.6 s total · `python scripts/test_run.py Launchvault.ca`

| | |
|---|---|
| Target | `Launchvault.ca` → `launchvault.ca` (172.64.80.1) |
| Scan | `done` · 40 pages read, 2 skipped · 44.8 s from queue to done |
| Score | **82 / 100 — clean** · Craft 74 · Structure 90 · Search 87 · Answers 76 |
| Findings | 138 findings across 7 distinct problems · 7 of 7 explained by Claude |
| AI step | `claude-haiku-4-5` (served as `claude-haiku-4-5-20251001`) · 2 calls · 2,132 in / 769 out tokens · **$0.0060** |
| Backend | `http://127.0.0.1:50481` · Postgres (aws-1-us-east-2.pooler.supabase.com) · workspace API off · up in 3.2 s |

### 1. Environment

- **Database:** Postgres (aws-1-us-east-2.pooler.supabase.com) — `FIG_DB_STRICT=1`, so an unreachable database fails the run instead of falling back to SQLite. Schema check (`init_db`) took 500 ms.
- **AI:** key present, model `claude-haiku-4-5`, priced at $1.00 in / $5.00 out per million tokens.
- **Crawler:** user agent `FIGBot/0.2 (+https://fig.tools/bot; site self-check and structure scanner)`, 0.8 s between requests to a host, up to 40 pages, 5,120.0 KB per response, 5 redirects.
- **Server:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 50481 --log-level info` with `FIG_WORKSPACE_API=0`, Python 3.12.10.

### 2. Routes

| # | Step | Request | Expected | Got | Time | | Note |
|---|---|---|---|---|---|---|---|
| 1 | service | `GET /` | 200 | 200 | 0 ms | ✅ | — |
| 2 | service | `GET /health` | 200 | 200 | 63 ms | ✅ | — |
| 3 | frontend disconnected | `GET /api/me` | 404 | 404 | 15 ms | ✅ | workspace API not mounted |
| 4 | frontend disconnected | `GET /api/projects` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 5 | frontend disconnected | `OPTIONS /v1/sites` | 400/405 | 405 | 0 ms | ✅ | CORS preflight from the Next.js dev origin |
| 6 | auth | `GET /v1/account` | 401 | 401 | 0 ms | ✅ | no key |
| 7 | auth | `GET /v1/account` | 401 | 401 | 78 ms | ✅ | wrong key |
| 8 | auth | `GET /v1/account` | 200 | 200 | 219 ms | ✅ | key minted for this run |
| 9 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | loopback address |
| 10 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | cloud metadata endpoint |
| 11 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | private address on a non-standard port |
| 12 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | 127.0.0.1 written as a number |
| 13 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | reserved name |
| 14 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | internal-only suffix |
| 15 | validation | `POST /v1/sites` | 422 | 422 | 203 ms | ✅ | real public DNS name that resolves to 127.0.0.1 |
| 16 | validation | `POST /v1/sites` | 422 | 422 | 219 ms | ✅ | domain that does not exist |
| 17 | validation | `POST /v1/sites` | 422 | 422 | 203 ms | ✅ | non-web scheme |
| 18 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | not a hostname at all |
| 19 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | empty input |
| 20 | validation | `POST /scan` | 422 | 422 | 0 ms | ✅ | the free public read goes through the same gate |
| 21 | provision | `POST /v1/sites` | 201 | 201 | 235 ms | ✅ | as typed |
| 22 | provision | `POST /v1/sites` | 201 | 201 | 203 ms | ✅ | same site given as a full URL |
| 23 | provision | `GET /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd` | 200 | 200 | 312 ms | ✅ | — |
| 24 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification` | 200 | 200 | 219 ms | ✅ | issue a DNS TXT token |
| 25 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification/confirm` | 200 | 200 | 219 ms | ✅ | look the record up |
| 26 | scan | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/scans` | 202 | 202 | 234 ms | ✅ | queued for a worker |
| 27 | scan | `GET /v1/scans/446c91bf-7eb2-447d-bd6c-a42c38c30e57?findings=false` | 200 | 200 | 223 ms | ✅ | polled 26x every 1.5s until done (ms is the average) |
| 28 | results | `GET /v1/scans/446c91bf-7eb2-447d-bd6c-a42c38c30e57` | 200 | 200 | 266 ms | ✅ | scores and findings |
| 29 | results | `GET /v1/scans/446c91bf-7eb2-447d-bd6c-a42c38c30e57/pages` | 200 | 200 | 234 ms | ✅ | pages read |
| 30 | results | `GET /v1/scans/446c91bf-7eb2-447d-bd6c-a42c38c30e57/trace` | 200 | 200 | 188 ms | ✅ | stage-by-stage trace |
| 31 | results | `GET /v1/report` | 200 | 200 | 265 ms | ✅ | partner estate roll-up |
| 32 | results | `GET /v1/scans/not-a-real-scan` | 404 | 404 | 188 ms | ✅ | unknown scan id |

### 3. Validation system

**Accepted:** `Launchvault.ca` → `launchvault.ca` (nothing to change). Resolved to 172.64.80.1 — every address public, so the crawl was allowed. The same site given as `https://Launchvault.ca/pricing?utm_source=fig-test` normalised to the same hostname and returned the existing site.

**Ownership:** DNS TXT verification was issued and checked — verified: `False`. Ownership is only required to schedule monitoring; a one-off scan of any public site is allowed without it.

**Rejected** (each is a `POST /v1/sites`, answered before anything is fetched):

| Input | What it is | HTTP | Code | Expected | | Message |
|---|---|---|---|---|---|---|
| `127.0.0.1` | loopback address | 422 | `ip_literal` | `ip_literal` | ✅ | 127.0.0.1 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `169.254.169.254` | cloud metadata endpoint | 422 | `ip_literal` | `ip_literal` | ✅ | 169.254.169.254 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `http://10.0.0.1:8080/admin` | private address on a non-standard port | 422 | `has_port` | `has_port` | ✅ | Port 8080 is not supported. Give the site's hostname; sites are read over the standard ports. |
| `2130706433` | 127.0.0.1 written as a number | 422 | `bad_hostname` | `bad_hostname` | ✅ | '2130706433' does not look like a public domain name. |
| `localhost` | reserved name | 422 | `reserved_name` | `reserved_name` | ✅ | localhost is under the reserved name 'localhost', which never points at a public website. |
| `printer.internal` | internal-only suffix | 422 | `reserved_name` | `reserved_name` | ✅ | printer.internal is under the reserved name 'internal', which never points at a public website. |
| `127.0.0.1.nip.io` | real public DNS name that resolves to 127.0.0.1 | 422 | `non_public_address` | `non_public_address` | ✅ | 127.0.0.1.nip.io resolves to 127.0.0.1, which is not on the public internet. FIG only reads public sites. |
| `fig-nx-027ee7a89d.com` | domain that does not exist | 422 | `dns_failed` | `dns_failed` | ✅ | fig-nx-027ee7a89d.com does not resolve ([Errno 11001] getaddrinfo failed). |
| `ftp://launchvault.ca` | non-web scheme | 422 | `bad_scheme` | `bad_scheme` | ✅ | Only http and https sites can be read, not ftp://. |
| `not a hostname` | not a hostname at all | 422 | `bad_hostname` | `bad_hostname` | ✅ | 'not a hostname' contains spaces, so it is not a hostname or URL. |
| `(empty)` | empty input | 422 | `empty` | `empty` | ✅ | No hostname or URL was given. |

### 4. Pipeline

Trace total: 43.9 s inside the worker.

| Stage | Status | Time | What happened |
|---|---|---|---|
| `validate` | ok | 0 ms | launchvault.ca → launchvault.ca → 172.64.80.1 (all public) |
| `resolve_base` | ok | 1.4 s | https://launchvault.ca — tried: https://launchvault.ca/ ok 200 |
| `robots` | ok | 282 ms | parsed (HTTP 200) · 16 rules apply to FIGBot · 1 sitemap(s) declared |
| `discover` | ok | 703 ms | 1 sitemap file(s) read · 500 URLs listed · 500 on this site |
| `fetch` | ok | 31.7 s | 40 read · skipped: robots 2 · page limit reached |
| `rules` | ok | 62 ms | 138 flags from 7 distinct checks (craft 66, search 11, answers 36, structure 25) |
| `explain` | ok | 9.9 s | 7/7 distinct findings explained in 2 calls · 2,132 in / 769 out tokens · $0.0060 |
| `score` | ok | 0 ms | overall 82 (clean) · {'craft': 74, 'structure': 90, 'search': 87, 'answers': 76} |
| `persist` | ok | 188 ms | 40 pages and 138 findings saved, 138 with Claude-written text |

#### robots.txt

`https://launchvault.ca/robots.txt` → HTTP 200, outcome **parsed**, read in 282 ms.

Rules that apply to FIGBot (enforced before every request, including redirect hops):

```text
Allow: /
Allow: /features
Allow: /pricing
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /cookies
Allow: /refund-policy
Allow: /acceptable-use
Allow: /dpa
Disallow: /dashboard
Disallow: /onboarding
Disallow: /login
Disallow: /signup
Disallow: /checkout
Disallow: /api/
```

- Declared sitemap: `https://launchvault.ca/sitemap.xml`

**Independent robots check:** of 40 pages read, 0 are disallowed by robots.txt.

#### Discovery

| Sitemap | Outcome | HTTP | URLs | Child sitemaps | Time |
|---|---|---|---|---|---|
| `https://launchvault.ca/sitemap.xml` | ok | 200 | 1069 | 0 | 703 ms |

#### Pages

40 read, 2 skipped; stopped because: page limit reached.

| # | Path | Outcome | HTTP | Size | Time | Note |
|---|---|---|---|---|---|---|
| 1 | `/` | ✅ read | 200 | 149.8 KB | 1.4 s | “LaunchVault — Learn AI in Plain English. No Jargon, No Rush.” · 1682 words · sections: hero, content, features, content, features, content, pricing, content, content, faq, content, cta |
| 2 | `/learn-ai` | ✅ read | 200 | 40.8 KB | 562 ms | “Learn AI — Free AI Learning Platform to Master AI \| LaunchVault” · 808 words · sections: hero, content, content, content, faq, content |
| 3 | `/how-to-learn-ai` | ✅ read | 200 | 37.6 KB | 828 ms | “How to Learn AI in 2026 — Step-by-Step Guide \| LaunchVault” · 637 words · sections: hero, content, faq |
| 4 | `/features` | ✅ read | 200 | 57.2 KB | 781 ms | “AI Learning Platform Features — Prompts, Courses & AI Agents \| LaunchVault” · 827 words · sections: hero, content, content, content, content, content, content |
| 5 | `/how-it-works` | ✅ read | 200 | 48.9 KB | 828 ms | “How to Learn AI with LaunchVault — How It Works” · 604 words · sections: hero, how, features, content, pricing, content |
| 6 | `/pricing` | ✅ read | 200 | 101.4 KB | 828 ms | “Pricing — AI Learning Platform Plans to Learn AI \| LaunchVault” · 903 words · sections: hero, content, content, content, pricing, content, content, cta, content |
| 7 | `/library` | ✅ read | 200 | 134.9 KB | 937 ms | “AI Prompt Library & Courses — Learn AI Free \| LaunchVault” · 1543 words · sections: hero, testimonials, pricing |
| 8 | `/glossary` | ✅ read | 200 | 258.4 KB | 828 ms | “AI Glossary — AI Terms & Concepts Explained Simply \| LaunchVault” · 2208 words · sections: hero, content, how |
| 9 | `/blog` | ✅ read | 200 | 161.6 KB | 703 ms | “Learn AI — Guides & Essays on Using AI \| LaunchVault Blog” · 1728 words · sections: hero, content, content, footer |
| 10 | `/about` | ✅ read | 200 | 49.8 KB | 672 ms | “About LaunchVault — How Our AI Learning Platform Works” · 793 words · sections: hero, content, content, content, content, content, content |
| 11 | `/contact` | ✅ read | 200 | 28.4 KB | 688 ms | “Contact — LaunchVault” · 250 words · sections: hero, content, content |
| 12 | `/signup` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/signup |
| 13 | `/login` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/login |
| 14 | `/privacy` | ✅ read | 200 | 33.7 KB | 828 ms | “Privacy Policy — LaunchVault” · 1003 words · sections: hero, content, footer |
| 15 | `/terms` | ✅ read | 200 | 35.0 KB | 797 ms | “Terms of Service — LaunchVault” · 1089 words · sections: hero, content, footer |
| 16 | `/cookies` | ✅ read | 200 | 27.8 KB | 797 ms | “Cookie Policy — LaunchVault” · 441 words · sections: hero, content, footer |
| 17 | `/refund-policy` | ✅ read | 200 | 29.2 KB | 797 ms | “Cancellation Policy — LaunchVault” · 619 words · sections: hero, content, footer |
| 18 | `/acceptable-use` | ✅ read | 200 | 28.5 KB | 859 ms | “Acceptable Use Policy — LaunchVault” · 602 words · sections: hero, content, footer |
| 19 | `/dpa` | ✅ read | 200 | 30.1 KB | 797 ms | “Data Processing Addendum — LaunchVault” · 607 words · sections: hero, content, footer |
| 20 | `/domains/ai-prompting-mastery` | ✅ read | 200 | 86.7 KB | 969 ms | “AI Prompting Mastery — LaunchVault” · 1075 words · sections: hero, content, content, content |
| 21 | `/domains/prompt-engineering-fundamentals` | ✅ read | 200 | 76.4 KB | 703 ms | “Prompt Engineering Fundamentals — LaunchVault” · 934 words · sections: hero, content, content, content |
| 22 | `/domains/advanced-prompt-engineering` | ✅ read | 200 | 84.5 KB | 765 ms | “Advanced Prompt Engineering — LaunchVault” · 1039 words · sections: hero, content, content, content |
| 23 | `/domains/ai-for-business` | ✅ read | 200 | 85.2 KB | 890 ms | “AI for Business — LaunchVault” · 1043 words · sections: hero, content, content, content |
| 24 | `/domains/ai-business-models` | ✅ read | 200 | 84.7 KB | 734 ms | “AI Business Models — LaunchVault” · 1039 words · sections: hero, pricing, content, content |
| 25 | `/domains/ai-monetization` | ✅ read | 200 | 88.6 KB | 813 ms | “AI Monetization — LaunchVault” · 1081 words · sections: hero, content, content, content |
| 26 | `/domains/ai-automation-workflows` | ✅ read | 200 | 75.8 KB | 781 ms | “AI Automation & Workflows — LaunchVault” · 916 words · sections: hero, how, content, content |
| 27 | `/domains/no-code-ai-automation` | ✅ read | 200 | 88.5 KB | 797 ms | “No-Code AI Automation — LaunchVault” · 1082 words · sections: hero, content, content, content |
| 28 | `/domains/ai-agents-blueprints` | ✅ read | 200 | 111.9 KB | 781 ms | “AI Agents & Blueprints — LaunchVault” · 1454 words · sections: hero, content, content, content |
| 29 | `/domains/multi-agent-systems` | ✅ read | 200 | 92.9 KB | 813 ms | “Multi-Agent Systems — LaunchVault” · 1073 words · sections: hero, content, content, content |
| 30 | `/domains/agent-memory-tool-use` | ✅ read | 200 | 77.8 KB | 781 ms | “Agent Memory & Tool Use — LaunchVault” · 946 words · sections: hero, content, content, content |
| 31 | `/domains/machine-learning-basics` | ✅ read | 200 | 108.1 KB | 813 ms | “Machine Learning Basics — LaunchVault” · 1399 words · sections: hero, content, content, content |
| 32 | `/domains/deep-learning-basics` | ✅ read | 200 | 84.8 KB | 796 ms | “Deep Learning Basics — LaunchVault” · 1041 words · sections: hero, content, content, content |
| 33 | `/domains/data-literacy-for-ai` | ✅ read | 200 | 69.8 KB | 781 ms | “Data Literacy for AI — LaunchVault” · 865 words · sections: hero, content, content, content |
| 34 | `/domains/ai-coding-development` | ✅ read | 200 | 78.8 KB | 750 ms | “AI Coding & Development — LaunchVault” · 981 words · sections: hero, testimonials, content, content |
| 35 | `/domains/ai-app-building` | ✅ read | 200 | 65.9 KB | 859 ms | “AI App Building — LaunchVault” · 797 words · sections: hero, content, content, content |
| 36 | `/domains/ai-saas-building` | ✅ read | 200 | 70.4 KB | 781 ms | “AI SaaS Building — LaunchVault” · 865 words · sections: hero, content, content, content |
| 37 | `/domains/ai-productivity` | ✅ read | 200 | 88.8 KB | 750 ms | “AI Productivity & Personal Use — LaunchVault” · 1122 words · sections: hero, content, content, content |
| 38 | `/domains/ai-content-creation` | ✅ read | 200 | 72.3 KB | 828 ms | “AI Content Creation — LaunchVault” · 871 words · sections: hero, content, content, content |
| 39 | `/domains/ai-copywriting` | ✅ read | 200 | 64.8 KB | 766 ms | “AI Copywriting — LaunchVault” · 770 words · sections: hero, content, content, content |
| 40 | `/domains/ai-marketing` | ✅ read | 200 | 87.0 KB | 844 ms | “AI Marketing — LaunchVault” · 1072 words · sections: hero, content, content, content |
| 41 | `/domains/ai-sales` | ✅ read | 200 | 66.2 KB | 782 ms | “AI Sales — LaunchVault” · 793 words · sections: hero, content, content, content |
| 42 | `/domains/ai-customer-support` | ✅ read | 200 | 92.0 KB | 828 ms | “AI Customer Support — LaunchVault” · 1141 words · sections: hero, pricing, content, content |

#### Rules

138 flags over 40 pages. Deterministic — no model involved.

| Check | Layer | Times flagged |
|---|---|---|
| `overused_icons` | craft | 40 |
| `no_answerable_questions` | answers | 36 |
| `heading_skips` | structure | 25 |
| `generic_copy` | craft | 15 |
| `numbered_eyebrows` | craft | 11 |
| `meta_description_length` | search | 10 |
| `title_length` | search | 1 |

#### AI step (the only model call in the pipeline)

- Sent **7 items** (one per distinct finding) instead of 138 — a check that fires on many pages is explained once.
- Model `claude-haiku-4-5`, served as `claude-haiku-4-5-20251001`: 2 calls, 0 failed batches.
- Tokens: 2,132 input, 769 output → **$0.0060**.
- Explained 7, kept the rule's own text for 0.
- Request ids: `req_011Cf62Qqnnadein1oAR2KDh`, `req_011Cf62RQp9YmAjTNqNTE8zq`

#### Scores

| Layer | Score |
|---|---|
| Craft | 74 |
| Structure | 90 |
| Search | 87 |
| Answers | 76 |
| **Overall** | **82 — clean** |

### 5. Findings

#### Craft (74/100)

- **`generic_copy`** · medium · 15× on 15 pages (/, /how-it-works, /about, /domains/prompt-engineering-fundamentals…) · _Claude-written_
  - **Found (one example):** 1 instance(s) of generic marketing phrasing found in headings/copy
  - **Why:** Generic phrases like "Supercharge", "The Future of", and "unlock your personalized feed" are commonly associated with template or auto-generated marketing copy. They weaken specificity.
  - **Fix:** Replace "Supercharge Your Prompts with Context" with a benefit specific to LaunchVault, e.g., "Build Prompts That Remember Your Goals". Replace "unlock your personalized feed" with what actually personalizes (e.g., "track progress across 50 AI domains").
- **`overused_icons`** · low · 40× on 40 pages (/domains/data-literacy-for-ai, /acceptable-use, /dpa, /domains/ai-customer-support…) · _Claude-written_
  - **Found (one example):** 3 uses of icons commonly overused in generated UI (sparkles, arrow-right)
  - **Why:** Arrow-right, sparkles, and rocket icons appear frequently in generated UI kits and template designs. Overreliance suggests a default pattern rather than intentional visual hierarchy.
  - **Fix:** Audit icon usage: remove decorative sparkles and rockets where they don't add clarity. Keep arrow-right only for navigation; replace trend-focused icons (trending-up, zap) with domain-specific symbols relevant to AI learning.
- **`numbered_eyebrows`** · low · 11× on 11 pages (/acceptable-use, /dpa, /, /how-to-learn-ai…) · _Claude-written_
  - **Found (one example):** Found 6 short numbered labels (01, 02, 03, 04, 05) — a common auto-generated 'step/feature' eyebrow pattern
  - **Why:** Numbered eyebrows (1, 2, 3...) commonly signal template-generated layouts rather than thoughtfully designed content hierarchy. This pattern reads as auto-made rather than intentional.
  - **Fix:** Replace numbered labels with descriptive headers that reflect actual content, e.g., "Getting Started" instead of "1", "Core Concepts" instead of "2". Use these across /about, /, and /acceptable-use.

#### Structure (90/100)

- **`heading_skips`** · low · 25× on 25 pages (/domains/data-literacy-for-ai, /domains/ai-prompting-mastery, /domains/prompt-engineering-fundamentals, /domains/ai-coding-development…) · _Claude-written_
  - **Found (one example):** 2 places where the heading level jumps more than one step
  - **Why:** Heading jumps break the logical outline readers and assistive technology expect, making it harder to scan page structure and navigate sections.
  - **Fix:** On /domains/advanced-prompt-engineering and similar pages, add missing h2 tags between h1 and h3, and h3 tags between h2 and h4, to create a continuous hierarchy.

#### Search (87/100)

- **`meta_description_length`** · low · 10× on 10 pages (/, /learn-ai, /how-to-learn-ai, /features…) · _Claude-written_
  - **Found (one example):** Meta description is 194 characters (long)
  - **Why:** Meta descriptions over 160 characters truncate in search results, losing message impact. Longer descriptions suggest padding rather than concise value summary.
  - **Fix:** Trim each meta description to 155 characters max. For / use: "Learn AI without jargon. Clear lessons, copy-ready prompts, and step-by-step guides across 50 domains. Start free." Keep the rest consistent across affected pages.
- **`title_length`** · low · 1× on 1 page (/features) · _Claude-written_
  - **Found (one example):** Title is 74 characters and will be truncated
  - **Why:** Search engines truncate titles over 60 characters on desktop. At 74 characters, the /features title loses its closing tag in search results, reducing visibility.
  - **Fix:** Shorten /features title to: "AI Learning Platform Features | LaunchVault" (52 chars). Prioritize "Features" over descriptive modifiers; move "Prompts, Courses & AI Agents" to meta description.

#### Answers (76/100)

- **`no_answerable_questions`** · medium · 36× on 36 pages (/domains/data-literacy-for-ai, /library, /how-it-works, /glossary…) · _Claude-written_
  - **Found (one example):** No question-and-answer block on this page
  - **Why:** AI answer engines quote and cite pages with structured questions and answers. Without them, these 36 pages can't be sourced in AI-generated responses, reducing referral traffic.
  - **Fix:** Add FAQ or QA schema to /about ("What is LaunchVault?", "How does personalization work?"), /contact ("How do I get support?"), and /blog post pages. Use JSON-LD structured data.

### 6. Database cross-check

| | Database | API |
|---|---|---|
| Scan status | done | done |
| Findings | 138 | 138 |
| AI-written findings | 138 | 138 |
| Pages | 40 | 40 |
| Trace stored | True | True |
| Queue job | done, attempt 1 | — |

### 7. Checks

- ✅ **preflight** — database is Postgres, not a SQLite fallback
- ✅ **preflight** — Anthropic API key is set
- ✅ **preflight** — ai_explain is enabled
- ✅ **preflight** — scans.trace column exists
- ✅ **preflight** — API key minted on account `test-runs`
- ✅ **server** — backend answers /health
- ✅ **routes** — root lists the workspace API as not mounted
- ✅ **routes** — /health reports Postgres, ai_explain on, workspace API off
- ✅ **routes** — no browser origin is allowed (no CORS headers returned)
- ✅ **validation** — every unsafe target answered with the expected reason code
- ✅ **provision** — `Launchvault.ca` stored as `launchvault.ca`
- ✅ **provision** — the URL form resolves to the same site (no duplicate)
- ✅ **ownership** — unverified (no TXT record) -- and a one-off scan is still allowed
- ✅ **scan** — scan finished as `done`
- ✅ **results** — trace covers every pipeline stage
- ✅ **results** — report lists this site
- ✅ **results** — no page the scan read is disallowed by robots.txt (independent check)
- ✅ **database** — findings in the database match the API
- ✅ **database** — AI-written flags match the API
- ✅ **database** — pages in the database match the API
- ✅ **database** — trace stored on the scan row
- ✅ **database** — queue job finished on its first attempt
- Plus 32 route calls in section 2, 32 as expected.

### 8. Issues observed

- ℹ️ 2 page(s) skipped because the site's robots.txt disallows them — expected, and correct: /signup, /login

### 9. Server log (application lines, redacted)

```text
2026-09-15 18:36:12,892 INFO fig.jobs: worker w1 up
2026-09-15 18:36:12,892 INFO fig.jobs: worker w2 up
2026-09-15 18:36:12,892 INFO fig: FIG API up - db postgres, ai_explain claude-haiku-4-5, workspace API off (disconnected from the frontend)
2026-09-15 18:37:02,715 INFO fig.pipeline: scan 446c91bf-7eb2-447d-bd6c-a42c38c30e57 done: 40 pages, score 82, 43938 ms
```

### 10. Review notes (added after the run, from reading the results)

This run re-tests the three fixes from Test #1's review. Same site, same settings, same model.

**The fixes held:**

1. **robots.txt.** All 16 rules picked up (Test #1: 10). `/login` and `/signup` were skipped as `robots` before any request was made to them, and the harness's independent reading of the file found 0 of 40 pages read are disallowed. Test #1 had no such check.
2. **`section_order`.** 0 findings (Test #1: 7, all false). Structure went from 50 to 90. The legal pages still show a `footer` role, but the empty block after it no longer counts as a section.
3. **The homepage FAQ.** `no_answerable_questions` no longer fires on `/`, `/learn-ai`, `/how-to-learn-ai` or `/pricing` (checked in the database). The first three have a section classified as `faq`. `/pricing` has none, so the question headings rule is what cleared it.

**Why there are 7 problems instead of 10.** The other three disappeared for the right reasons. `section_order` was fixed. `missing_canonical` (2×) and `thin_page` (1×) had only ever fired on `/login` and `/signup`, which robots.txt says not to read. The two pages that replaced them in the 40-page budget (`/domains/ai-sales` and `/domains/ai-customer-support`) account for the small changes in the other counts: `generic_copy` 13→15, `heading_skips` 23→25, `meta_description_length` 11→10. Craft moved 75→74 for the same reason. The overall score went from 70 (check) to 82 (clean).

**The AI step: correct, with three nits.** 7 of 7 findings explained, $0.0060, and every fix names real LaunchVault pages. There is no placeholder domain this time, but this run had no canonical finding, so that fix is untested live. What I noticed reading the output:

- **Tone.** `numbered_eyebrows` says the pattern "reads as auto-made rather than intentional". That is firmer than the probabilistic language `CLAUDE.md` requires ("commonly associated with…"). The rule's own text is fine. The model drifted from the system prompt.
- **Overclaim.** `no_answerable_questions` says the 36 pages "can't be sourced in AI-generated responses". A page with no Q&A block is less quotable, not unquotable.
- **Arithmetic.** The suggested `/features` title is described as "52 chars". It is 43. The suggestion is still under the limit, so the advice holds, but a number the model computed should not be shown as fact. The suggested meta description is 114 characters, within the 155 it asked for.

None of these would fail a check, and none needs a pipeline change. If they recur, the cheaper fix is in the rule text the model receives, or a deterministic length check on suggested titles, rather than a larger model.

---

## Test #3 — launchvault.ca

**PASS** · 54/54 checks passed · 2026-09-16 23:06 (UTC-0400) · 54.7 s total · `python scripts/test_run.py launchvault.ca`

| | |
|---|---|
| Target | `launchvault.ca` → `launchvault.ca` (172.64.80.1) |
| Scan | `done` · 40 pages read, 2 skipped · 44.8 s from queue to done |
| Score | **82 / 100 — clean** · Craft 74 · Structure 90 · Search 87 · Answers 76 |
| Findings | 138 findings across 7 distinct problems · 7 of 7 explained by Claude |
| AI step | `claude-haiku-4-5` (served as `claude-haiku-4-5-20251001`) · 2 calls · 2,132 in / 726 out tokens · **$0.0058** |
| Backend | `http://127.0.0.1:54273` · Postgres (aws-1-us-east-2.pooler.supabase.com) · workspace API off · up in 3.0 s |

### 1. Environment

- **Database:** Postgres (aws-1-us-east-2.pooler.supabase.com) — `FIG_DB_STRICT=1`, so an unreachable database fails the run instead of falling back to SQLite. Schema check (`init_db`) took 594 ms.
- **AI:** key present, model `claude-haiku-4-5`, priced at $1.00 in / $5.00 out per million tokens.
- **Crawler:** user agent `FIGBot/0.2 (+https://fig.tools/bot; site self-check and structure scanner)`, 0.8 s between requests to a host, up to 40 pages, 5,120.0 KB per response, 5 redirects.
- **Server:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 54273 --log-level info` with `FIG_WORKSPACE_API=0`, Python 3.12.10.

### 2. Routes

| # | Step | Request | Expected | Got | Time | | Note |
|---|---|---|---|---|---|---|---|
| 1 | service | `GET /` | 200 | 200 | 15 ms | ✅ | — |
| 2 | service | `GET /health` | 200 | 200 | 188 ms | ✅ | — |
| 3 | frontend disconnected | `GET /api/me` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 4 | frontend disconnected | `GET /api/projects` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 5 | frontend disconnected | `OPTIONS /v1/sites` | 400/405 | 405 | 0 ms | ✅ | CORS preflight from the Next.js dev origin |
| 6 | auth | `GET /v1/account` | 401 | 401 | 15 ms | ✅ | no key |
| 7 | auth | `GET /v1/account` | 401 | 401 | 78 ms | ✅ | wrong key |
| 8 | auth | `GET /v1/account` | 200 | 200 | 219 ms | ✅ | key minted for this run |
| 9 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | loopback address |
| 10 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | cloud metadata endpoint |
| 11 | validation | `POST /v1/sites` | 422 | 422 | 171 ms | ✅ | private address on a non-standard port |
| 12 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | 127.0.0.1 written as a number |
| 13 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | reserved name |
| 14 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | internal-only suffix |
| 15 | validation | `POST /v1/sites` | 422 | 422 | 250 ms | ✅ | real public DNS name that resolves to 127.0.0.1 |
| 16 | validation | `POST /v1/sites` | 422 | 422 | 265 ms | ✅ | domain that does not exist |
| 17 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | non-web scheme |
| 18 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | not a hostname at all |
| 19 | validation | `POST /v1/sites` | 422 | 422 | 172 ms | ✅ | empty input |
| 20 | validation | `POST /scan` | 422 | 422 | 15 ms | ✅ | the free public read goes through the same gate |
| 21 | provision | `POST /v1/sites` | 201 | 201 | 281 ms | ✅ | as typed |
| 22 | provision | `POST /v1/sites` | 201 | 201 | 188 ms | ✅ | same site given as a full URL |
| 23 | provision | `GET /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd` | 200 | 200 | 344 ms | ✅ | — |
| 24 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification` | 200 | 200 | 218 ms | ✅ | issue a DNS TXT token |
| 25 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification/confirm` | 200 | 200 | 204 ms | ✅ | look the record up |
| 26 | scan | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/scans` | 202 | 202 | 234 ms | ✅ | queued for a worker |
| 27 | scan | `GET /v1/scans/5b5d2508-1839-4b80-8f2a-7196ad5ede4f?findings=false` | 200 | 200 | 220 ms | ✅ | polled 26x every 1.5s until done (ms is the average) |
| 28 | results | `GET /v1/scans/5b5d2508-1839-4b80-8f2a-7196ad5ede4f` | 200 | 200 | 281 ms | ✅ | scores and findings |
| 29 | results | `GET /v1/scans/5b5d2508-1839-4b80-8f2a-7196ad5ede4f/pages` | 200 | 200 | 219 ms | ✅ | pages read |
| 30 | results | `GET /v1/scans/5b5d2508-1839-4b80-8f2a-7196ad5ede4f/trace` | 200 | 200 | 203 ms | ✅ | stage-by-stage trace |
| 31 | results | `GET /v1/report` | 200 | 200 | 266 ms | ✅ | partner estate roll-up |
| 32 | results | `GET /v1/scans/not-a-real-scan` | 404 | 404 | 203 ms | ✅ | unknown scan id |

### 3. Validation system

**Accepted:** `launchvault.ca` → `launchvault.ca` (nothing to change). Resolved to 172.64.80.1 — every address public, so the crawl was allowed. The same site given as `https://launchvault.ca/pricing?utm_source=fig-test` normalised to the same hostname and returned the existing site.

**Ownership:** DNS TXT verification was issued and checked — verified: `False`. Ownership is only required to schedule monitoring; a one-off scan of any public site is allowed without it.

**Rejected** (each is a `POST /v1/sites`, answered before anything is fetched):

| Input | What it is | HTTP | Code | Expected | | Message |
|---|---|---|---|---|---|---|
| `127.0.0.1` | loopback address | 422 | `ip_literal` | `ip_literal` | ✅ | 127.0.0.1 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `169.254.169.254` | cloud metadata endpoint | 422 | `ip_literal` | `ip_literal` | ✅ | 169.254.169.254 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `http://10.0.0.1:8080/admin` | private address on a non-standard port | 422 | `has_port` | `has_port` | ✅ | Port 8080 is not supported. Give the site's hostname; sites are read over the standard ports. |
| `2130706433` | 127.0.0.1 written as a number | 422 | `bad_hostname` | `bad_hostname` | ✅ | '2130706433' does not look like a public domain name. |
| `localhost` | reserved name | 422 | `reserved_name` | `reserved_name` | ✅ | localhost is under the reserved name 'localhost', which never points at a public website. |
| `printer.internal` | internal-only suffix | 422 | `reserved_name` | `reserved_name` | ✅ | printer.internal is under the reserved name 'internal', which never points at a public website. |
| `127.0.0.1.nip.io` | real public DNS name that resolves to 127.0.0.1 | 422 | `non_public_address` | `non_public_address` | ✅ | 127.0.0.1.nip.io resolves to 127.0.0.1, which is not on the public internet. FIG only reads public sites. |
| `fig-nx-01033d333c.com` | domain that does not exist | 422 | `dns_failed` | `dns_failed` | ✅ | fig-nx-01033d333c.com does not resolve ([Errno 11001] getaddrinfo failed). |
| `ftp://launchvault.ca` | non-web scheme | 422 | `bad_scheme` | `bad_scheme` | ✅ | Only http and https sites can be read, not ftp://. |
| `not a hostname` | not a hostname at all | 422 | `bad_hostname` | `bad_hostname` | ✅ | 'not a hostname' contains spaces, so it is not a hostname or URL. |
| `(empty)` | empty input | 422 | `empty` | `empty` | ✅ | No hostname or URL was given. |

### 4. Pipeline

Trace total: 43.6 s inside the worker.

| Stage | Status | Time | What happened |
|---|---|---|---|
| `validate` | ok | 0 ms | launchvault.ca → launchvault.ca → 172.64.80.1 (all public) |
| `resolve_base` | ok | 1.2 s | https://launchvault.ca — tried: https://launchvault.ca/ ok 200 |
| `robots` | ok | 531 ms | parsed (HTTP 200) · 16 rules apply to FIGBot · 1 sitemap(s) declared |
| `discover` | ok | 1.6 s | 1 sitemap file(s) read · 500 URLs listed · 500 on this site |
| `fetch` | ok | 31.3 s | 40 read · skipped: robots 2 · page limit reached |
| `rules` | ok | 62 ms | 138 flags from 7 distinct checks (craft 66, search 11, answers 36, structure 25) |
| `explain` | ok | 9.2 s | 7/7 distinct findings explained in 2 calls · 2,132 in / 726 out tokens · $0.0058 |
| `score` | ok | 0 ms | overall 82 (clean) · {'craft': 74, 'structure': 90, 'search': 87, 'answers': 76} |
| `persist` | ok | 187 ms | 40 pages and 138 findings saved, 138 with Claude-written text |

#### robots.txt

`https://launchvault.ca/robots.txt` → HTTP 200, outcome **parsed**, read in 531 ms.

Rules that apply to FIGBot (enforced before every request, including redirect hops):

```text
Allow: /
Allow: /features
Allow: /pricing
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /cookies
Allow: /refund-policy
Allow: /acceptable-use
Allow: /dpa
Disallow: /dashboard
Disallow: /onboarding
Disallow: /login
Disallow: /signup
Disallow: /checkout
Disallow: /api/
```

- Declared sitemap: `https://launchvault.ca/sitemap.xml`

**Independent robots check:** of 40 pages read, 0 are disallowed by robots.txt.

#### Discovery

| Sitemap | Outcome | HTTP | URLs | Child sitemaps | Time |
|---|---|---|---|---|---|
| `https://launchvault.ca/sitemap.xml` | ok | 200 | 1069 | 0 | 1.6 s |

#### Pages

40 read, 2 skipped; stopped because: page limit reached.

| # | Path | Outcome | HTTP | Size | Time | Note |
|---|---|---|---|---|---|---|
| 1 | `/` | ✅ read | 200 | 149.8 KB | 1.2 s | “LaunchVault — Learn AI in Plain English. No Jargon, No Rush.” · 1682 words · sections: hero, content, features, content, features, content, pricing, content, content, faq, content, cta |
| 2 | `/learn-ai` | ✅ read | 200 | 40.8 KB | 641 ms | “Learn AI — Free AI Learning Platform to Master AI \| LaunchVault” · 808 words · sections: hero, content, content, content, faq, content |
| 3 | `/how-to-learn-ai` | ✅ read | 200 | 37.6 KB | 546 ms | “How to Learn AI in 2026 — Step-by-Step Guide \| LaunchVault” · 637 words · sections: hero, content, faq |
| 4 | `/features` | ✅ read | 200 | 57.2 KB | 719 ms | “AI Learning Platform Features — Prompts, Courses & AI Agents \| LaunchVault” · 827 words · sections: hero, content, content, content, content, content, content |
| 5 | `/how-it-works` | ✅ read | 200 | 48.9 KB | 781 ms | “How to Learn AI with LaunchVault — How It Works” · 604 words · sections: hero, how, features, content, pricing, content |
| 6 | `/pricing` | ✅ read | 200 | 101.4 KB | 812 ms | “Pricing — AI Learning Platform Plans to Learn AI \| LaunchVault” · 903 words · sections: hero, content, content, content, pricing, content, content, cta, content |
| 7 | `/library` | ✅ read | 200 | 134.9 KB | 1.2 s | “AI Prompt Library & Courses — Learn AI Free \| LaunchVault” · 1543 words · sections: hero, testimonials, pricing |
| 8 | `/glossary` | ✅ read | 200 | 258.4 KB | 750 ms | “AI Glossary — AI Terms & Concepts Explained Simply \| LaunchVault” · 2208 words · sections: hero, content, how |
| 9 | `/blog` | ✅ read | 200 | 161.6 KB | 531 ms | “Learn AI — Guides & Essays on Using AI \| LaunchVault Blog” · 1728 words · sections: hero, content, content, footer |
| 10 | `/about` | ✅ read | 200 | 49.8 KB | 578 ms | “About LaunchVault — How Our AI Learning Platform Works” · 793 words · sections: hero, content, content, content, content, content, content |
| 11 | `/contact` | ✅ read | 200 | 28.4 KB | 828 ms | “Contact — LaunchVault” · 250 words · sections: hero, content, content |
| 12 | `/signup` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/signup |
| 13 | `/login` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/login |
| 14 | `/privacy` | ✅ read | 200 | 33.7 KB | 781 ms | “Privacy Policy — LaunchVault” · 1003 words · sections: hero, content, footer |
| 15 | `/terms` | ✅ read | 200 | 35.0 KB | 828 ms | “Terms of Service — LaunchVault” · 1089 words · sections: hero, content, footer |
| 16 | `/cookies` | ✅ read | 200 | 27.8 KB | 781 ms | “Cookie Policy — LaunchVault” · 441 words · sections: hero, content, footer |
| 17 | `/refund-policy` | ✅ read | 200 | 29.2 KB | 812 ms | “Cancellation Policy — LaunchVault” · 619 words · sections: hero, content, footer |
| 18 | `/acceptable-use` | ✅ read | 200 | 28.5 KB | 797 ms | “Acceptable Use Policy — LaunchVault” · 602 words · sections: hero, content, footer |
| 19 | `/dpa` | ✅ read | 200 | 30.1 KB | 812 ms | “Data Processing Addendum — LaunchVault” · 607 words · sections: hero, content, footer |
| 20 | `/domains/ai-prompting-mastery` | ✅ read | 200 | 86.7 KB | 1.1 s | “AI Prompting Mastery — LaunchVault” · 1075 words · sections: hero, content, content, content |
| 21 | `/domains/prompt-engineering-fundamentals` | ✅ read | 200 | 76.4 KB | 719 ms | “Prompt Engineering Fundamentals — LaunchVault” · 934 words · sections: hero, content, content, content |
| 22 | `/domains/advanced-prompt-engineering` | ✅ read | 200 | 84.5 KB | 813 ms | “Advanced Prompt Engineering — LaunchVault” · 1039 words · sections: hero, content, content, content |
| 23 | `/domains/ai-for-business` | ✅ read | 200 | 85.2 KB | 797 ms | “AI for Business — LaunchVault” · 1043 words · sections: hero, content, content, content |
| 24 | `/domains/ai-business-models` | ✅ read | 200 | 84.7 KB | 687 ms | “AI Business Models — LaunchVault” · 1039 words · sections: hero, pricing, content, content |
| 25 | `/domains/ai-monetization` | ✅ read | 200 | 88.6 KB | 766 ms | “AI Monetization — LaunchVault” · 1081 words · sections: hero, content, content, content |
| 26 | `/domains/ai-automation-workflows` | ✅ read | 200 | 75.8 KB | 797 ms | “AI Automation & Workflows — LaunchVault” · 916 words · sections: hero, how, content, content |
| 27 | `/domains/no-code-ai-automation` | ✅ read | 200 | 88.5 KB | 797 ms | “No-Code AI Automation — LaunchVault” · 1082 words · sections: hero, content, content, content |
| 28 | `/domains/ai-agents-blueprints` | ✅ read | 200 | 111.9 KB | 953 ms | “AI Agents & Blueprints — LaunchVault” · 1454 words · sections: hero, content, content, content |
| 29 | `/domains/multi-agent-systems` | ✅ read | 200 | 92.9 KB | 641 ms | “Multi-Agent Systems — LaunchVault” · 1073 words · sections: hero, content, content, content |
| 30 | `/domains/agent-memory-tool-use` | ✅ read | 200 | 77.8 KB | 797 ms | “Agent Memory & Tool Use — LaunchVault” · 946 words · sections: hero, content, content, content |
| 31 | `/domains/machine-learning-basics` | ✅ read | 200 | 108.1 KB | 782 ms | “Machine Learning Basics — LaunchVault” · 1399 words · sections: hero, content, content, content |
| 32 | `/domains/deep-learning-basics` | ✅ read | 200 | 84.8 KB | 781 ms | “Deep Learning Basics — LaunchVault” · 1041 words · sections: hero, content, content, content |
| 33 | `/domains/data-literacy-for-ai` | ✅ read | 200 | 69.8 KB | 828 ms | “Data Literacy for AI — LaunchVault” · 865 words · sections: hero, content, content, content |
| 34 | `/domains/ai-coding-development` | ✅ read | 200 | 78.8 KB | 797 ms | “AI Coding & Development — LaunchVault” · 981 words · sections: hero, testimonials, content, content |
| 35 | `/domains/ai-app-building` | ✅ read | 200 | 65.9 KB | 797 ms | “AI App Building — LaunchVault” · 797 words · sections: hero, content, content, content |
| 36 | `/domains/ai-saas-building` | ✅ read | 200 | 70.4 KB | 797 ms | “AI SaaS Building — LaunchVault” · 865 words · sections: hero, content, content, content |
| 37 | `/domains/ai-productivity` | ✅ read | 200 | 88.8 KB | 828 ms | “AI Productivity & Personal Use — LaunchVault” · 1122 words · sections: hero, content, content, content |
| 38 | `/domains/ai-content-creation` | ✅ read | 200 | 72.3 KB | 781 ms | “AI Content Creation — LaunchVault” · 871 words · sections: hero, content, content, content |
| 39 | `/domains/ai-copywriting` | ✅ read | 200 | 64.8 KB | 796 ms | “AI Copywriting — LaunchVault” · 770 words · sections: hero, content, content, content |
| 40 | `/domains/ai-marketing` | ✅ read | 200 | 87.0 KB | 750 ms | “AI Marketing — LaunchVault” · 1072 words · sections: hero, content, content, content |
| 41 | `/domains/ai-sales` | ✅ read | 200 | 66.2 KB | 782 ms | “AI Sales — LaunchVault” · 793 words · sections: hero, content, content, content |
| 42 | `/domains/ai-customer-support` | ✅ read | 200 | 92.0 KB | 828 ms | “AI Customer Support — LaunchVault” · 1141 words · sections: hero, pricing, content, content |

#### Rules

138 flags over 40 pages. Deterministic — no model involved.

| Check | Layer | Times flagged |
|---|---|---|
| `overused_icons` | craft | 40 |
| `no_answerable_questions` | answers | 36 |
| `heading_skips` | structure | 25 |
| `generic_copy` | craft | 15 |
| `numbered_eyebrows` | craft | 11 |
| `meta_description_length` | search | 10 |
| `title_length` | search | 1 |

#### AI step (the only model call in the pipeline)

- Sent **7 items** (one per distinct finding) instead of 138 — a check that fires on many pages is explained once.
- Model `claude-haiku-4-5`, served as `claude-haiku-4-5-20251001`: 2 calls, 0 failed batches.
- Tokens: 2,132 input, 726 output → **$0.0058**.
- Explained 7, kept the rule's own text for 0.
- Request ids: `req_011Cf8GoBBbrTqVgUREF7zk2`, `req_011Cf8GogetsRXcRv8Fv77xk`

#### Scores

| Layer | Score |
|---|---|
| Craft | 74 |
| Structure | 90 |
| Search | 87 |
| Answers | 76 |
| **Overall** | **82 — clean** |

### 5. Findings

#### Craft (74/100)

- **`generic_copy`** · medium · 15× on 15 pages (/, /how-it-works, /about, /domains/prompt-engineering-fundamentals…) · _Claude-written_
  - **Found (one example):** 1 instance(s) of generic marketing phrasing found in headings/copy
  - **Why:** Generic phrases like "Supercharge" and "True Value" don't differentiate LaunchVault or show specific benefits. They blend into standard marketing language across education sites.
  - **Fix:** On / and /about, replace "Supercharge Your Prompts with Context" with concrete detail: e.g., "Add real data to prompts—get more accurate AI responses." Show what LaunchVault uniquely teaches.
- **`overused_icons`** · low · 40× on 40 pages (/acceptable-use, /domains/data-literacy-for-ai, /dpa, /domains/ai-prompting-mastery…) · _Claude-written_
  - **Found (one example):** 3 uses of icons commonly overused in generated UI (chevron-right, sparkles)
  - **Why:** Arrow-right, sparkles, and rocket icons appear across 40 pages as visual clichés in generated design. They distract rather than clarify meaning for users scanning content.
  - **Fix:** On / and high-traffic pages, swap decorative icons for functional ones. Keep arrow-right for navigation; replace sparkles (9 uses) with icons that match actual features—e.g., a document icon for "prompts."
- **`numbered_eyebrows`** · low · 11× on 11 pages (/acceptable-use, /dpa, /, /how-to-learn-ai…) · _Claude-written_
  - **Found (one example):** Found 6 short numbered labels (01, 02, 03, 04, 05) — a common auto-generated 'step/feature' eyebrow pattern
  - **Why:** Numbered eyebrow labels read as template placeholders rather than meaningful section identifiers. Visitors scanning the page won't understand what each section covers.
  - **Fix:** Replace numbered labels (4, 2, 3, etc.) with descriptive names. For example, on / use "Learn", "Practice", "Build" instead of numbers to clarify what each section offers.

#### Structure (90/100)

- **`heading_skips`** · low · 25× on 25 pages (/domains/data-literacy-for-ai, /domains/ai-prompting-mastery, /domains/prompt-engineering-fundamentals, /domains/ai-coding-development…) · _Claude-written_
  - **Found (one example):** 2 places where the heading level jumps more than one step
  - **Why:** Heading jumps confuse screen readers and break the logical outline scanners use to navigate. Readers expect consistent hierarchy (h1→h2→h3), so skipping levels signals disorganized content structure.
  - **Fix:** On /domains/advanced-prompt-engineering and similar pages, insert missing h2 or h3 tags between jumps. For example, change 'h1 → h3' to 'h1 → h2 → h3' to restore proper nesting.

#### Search (87/100)

- **`meta_description_length`** · low · 10× on 10 pages (/, /learn-ai, /how-to-learn-ai, /features…) · _Claude-written_
  - **Found (one example):** Meta description is 194 characters (long)
  - **Why:** Meta descriptions over 160 characters truncate in search results, cutting off key messaging. Visitors see incomplete information before clicking.
  - **Fix:** Trim homepage meta description to 155 characters: "Learn AI without jargon. Copy-ready prompts, courses, and guides for 50 everyday topics. Start free." Keep the strongest value prop visible.
- **`title_length`** · low · 1× on 1 page (/features) · _Claude-written_
  - **Found (one example):** Title is 74 characters and will be truncated
  - **Why:** Title at 74 characters will truncate in search results and browser tabs. Searchers won't see the full page promise, affecting click-through rate.
  - **Fix:** Shorten /features title to 60 characters: "AI Learning Platform: Prompts, Courses & Agents | LaunchVault" to fit on desktop and mobile search results.

#### Answers (76/100)

- **`no_answerable_questions`** · medium · 36× on 36 pages (/domains/data-literacy-for-ai, /features, /how-it-works, /glossary…) · _Claude-written_
  - **Found (one example):** No question-and-answer block on this page
  - **Why:** No Q&A blocks mean answer engines can't extract specific claims to quote or cite. The page stays invisible to AI-powered search and answer tools.
  - **Fix:** Add a FAQ section to /about with 3–5 questions users ask: "What's the difference between a prompt and an AI agent?" Answer in complete sentences to make content quotable.

### 6. Database cross-check

| | Database | API |
|---|---|---|
| Scan status | done | done |
| Findings | 138 | 138 |
| AI-written findings | 138 | 138 |
| Pages | 40 | 40 |
| Trace stored | True | True |
| Queue job | done, attempt 1 | — |

### 7. Checks

- ✅ **preflight** — database is Postgres, not a SQLite fallback
- ✅ **preflight** — Anthropic API key is set
- ✅ **preflight** — ai_explain is enabled
- ✅ **preflight** — scans.trace column exists
- ✅ **preflight** — API key minted on account `test-runs`
- ✅ **server** — backend answers /health
- ✅ **routes** — root lists the workspace API as not mounted
- ✅ **routes** — /health reports Postgres, ai_explain on, workspace API off
- ✅ **routes** — no browser origin is allowed (no CORS headers returned)
- ✅ **validation** — every unsafe target answered with the expected reason code
- ✅ **provision** — `launchvault.ca` stored as `launchvault.ca`
- ✅ **provision** — the URL form resolves to the same site (no duplicate)
- ✅ **ownership** — unverified (no TXT record) -- and a one-off scan is still allowed
- ✅ **scan** — scan finished as `done`
- ✅ **results** — trace covers every pipeline stage
- ✅ **results** — report lists this site
- ✅ **results** — no page the scan read is disallowed by robots.txt (independent check)
- ✅ **database** — findings in the database match the API
- ✅ **database** — AI-written flags match the API
- ✅ **database** — pages in the database match the API
- ✅ **database** — trace stored on the scan row
- ✅ **database** — queue job finished on its first attempt
- Plus 32 route calls in section 2, 32 as expected.

### 8. Issues observed

- ℹ️ 2 page(s) skipped because the site's robots.txt disallows them — expected, and correct: /signup, /login

### 9. Server log (application lines, redacted)

```text
2026-09-16 23:06:03,641 INFO fig.jobs: worker w1 up
2026-09-16 23:06:03,641 INFO fig.jobs: worker w2 up
2026-09-16 23:06:03,641 INFO fig: FIG API up - db postgres, ai_explain claude-haiku-4-5, workspace API off (disconnected from the frontend)
2026-09-16 23:06:53,120 INFO fig.pipeline: scan 5b5d2508-1839-4b80-8f2a-7196ad5ede4f done: 40 pages, score 82, 43640 ms
```

---

## Test #4 — launchvault.ca

**PASS** · 54/54 checks passed · 2026-09-16 23:11 (UTC-0400) · 53.1 s total · `python scripts/test_run.py launchvault.ca`

| | |
|---|---|
| Target | `launchvault.ca` → `launchvault.ca` (172.64.80.1) |
| Scan | `done` · 40 pages read, 2 skipped · 43.1 s from queue to done |
| Score | **82 / 100 — clean** · Craft 74 · Structure 90 · Search 87 · Answers 76 |
| Findings | 138 findings across 7 distinct problems · 7 of 7 explained by Claude |
| AI step | `claude-haiku-4-5` (served as `claude-haiku-4-5-20251001`) · 2 calls · 2,137 in / 699 out tokens · **$0.0056** |
| Backend | `http://127.0.0.1:63393` · Postgres (aws-1-us-east-2.pooler.supabase.com) · workspace API off · up in 3.2 s |

### 1. Environment

- **Database:** Postgres (aws-1-us-east-2.pooler.supabase.com) — `FIG_DB_STRICT=1`, so an unreachable database fails the run instead of falling back to SQLite. Schema check (`init_db`) took 609 ms.
- **AI:** key present, model `claude-haiku-4-5`, priced at $1.00 in / $5.00 out per million tokens.
- **Crawler:** user agent `FIGBot/0.2 (+https://fig.tools/bot; site self-check and structure scanner)`, 0.8 s between requests to a host, up to 40 pages, 5,120.0 KB per response, 5 redirects.
- **Server:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 63393 --log-level info` with `FIG_WORKSPACE_API=0`, Python 3.12.10.

### 2. Routes

| # | Step | Request | Expected | Got | Time | | Note |
|---|---|---|---|---|---|---|---|
| 1 | service | `GET /` | 200 | 200 | 32 ms | ✅ | — |
| 2 | service | `GET /health` | 200 | 200 | 62 ms | ✅ | — |
| 3 | frontend disconnected | `GET /api/me` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 4 | frontend disconnected | `GET /api/projects` | 404 | 404 | 0 ms | ✅ | workspace API not mounted |
| 5 | frontend disconnected | `OPTIONS /v1/sites` | 400/405 | 405 | 0 ms | ✅ | CORS preflight from the Next.js dev origin |
| 6 | auth | `GET /v1/account` | 401 | 401 | 0 ms | ✅ | no key |
| 7 | auth | `GET /v1/account` | 401 | 401 | 94 ms | ✅ | wrong key |
| 8 | auth | `GET /v1/account` | 200 | 200 | 203 ms | ✅ | key minted for this run |
| 9 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | loopback address |
| 10 | validation | `POST /v1/sites` | 422 | 422 | 203 ms | ✅ | cloud metadata endpoint |
| 11 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | private address on a non-standard port |
| 12 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | 127.0.0.1 written as a number |
| 13 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | reserved name |
| 14 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | internal-only suffix |
| 15 | validation | `POST /v1/sites` | 422 | 422 | 203 ms | ✅ | real public DNS name that resolves to 127.0.0.1 |
| 16 | validation | `POST /v1/sites` | 422 | 422 | 250 ms | ✅ | domain that does not exist |
| 17 | validation | `POST /v1/sites` | 422 | 422 | 187 ms | ✅ | non-web scheme |
| 18 | validation | `POST /v1/sites` | 422 | 422 | 188 ms | ✅ | not a hostname at all |
| 19 | validation | `POST /v1/sites` | 422 | 422 | 203 ms | ✅ | empty input |
| 20 | validation | `POST /scan` | 422 | 422 | 0 ms | ✅ | the free public read goes through the same gate |
| 21 | provision | `POST /v1/sites` | 201 | 201 | 250 ms | ✅ | as typed |
| 22 | provision | `POST /v1/sites` | 201 | 201 | 219 ms | ✅ | same site given as a full URL |
| 23 | provision | `GET /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd` | 200 | 200 | 312 ms | ✅ | — |
| 24 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification` | 200 | 200 | 219 ms | ✅ | issue a DNS TXT token |
| 25 | ownership | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/verification/confirm` | 200 | 200 | 219 ms | ✅ | look the record up |
| 26 | scan | `POST /v1/sites/cd9c6b21-07b0-4345-b04e-ae4ba4379ecd/scans` | 202 | 202 | 234 ms | ✅ | queued for a worker |
| 27 | scan | `GET /v1/scans/a092e2a7-b669-45a0-ac81-eb79d554bc22?findings=false` | 200 | 200 | 225 ms | ✅ | polled 25x every 1.5s until done (ms is the average) |
| 28 | results | `GET /v1/scans/a092e2a7-b669-45a0-ac81-eb79d554bc22` | 200 | 200 | 265 ms | ✅ | scores and findings |
| 29 | results | `GET /v1/scans/a092e2a7-b669-45a0-ac81-eb79d554bc22/pages` | 200 | 200 | 235 ms | ✅ | pages read |
| 30 | results | `GET /v1/scans/a092e2a7-b669-45a0-ac81-eb79d554bc22/trace` | 200 | 200 | 218 ms | ✅ | stage-by-stage trace |
| 31 | results | `GET /v1/report` | 200 | 200 | 266 ms | ✅ | partner estate roll-up |
| 32 | results | `GET /v1/scans/not-a-real-scan` | 404 | 404 | 203 ms | ✅ | unknown scan id |

### 3. Validation system

**Accepted:** `launchvault.ca` → `launchvault.ca` (nothing to change). Resolved to 172.64.80.1 — every address public, so the crawl was allowed. The same site given as `https://launchvault.ca/pricing?utm_source=fig-test` normalised to the same hostname and returned the existing site.

**Ownership:** DNS TXT verification was issued and checked — verified: `False`. Ownership is only required to schedule monitoring; a one-off scan of any public site is allowed without it.

**Rejected** (each is a `POST /v1/sites`, answered before anything is fetched):

| Input | What it is | HTTP | Code | Expected | | Message |
|---|---|---|---|---|---|---|
| `127.0.0.1` | loopback address | 422 | `ip_literal` | `ip_literal` | ✅ | 127.0.0.1 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `169.254.169.254` | cloud metadata endpoint | 422 | `ip_literal` | `ip_literal` | ✅ | 169.254.169.254 is an IP address. FIG reads sites by domain name; give the site's hostname instead. |
| `http://10.0.0.1:8080/admin` | private address on a non-standard port | 422 | `has_port` | `has_port` | ✅ | Port 8080 is not supported. Give the site's hostname; sites are read over the standard ports. |
| `2130706433` | 127.0.0.1 written as a number | 422 | `bad_hostname` | `bad_hostname` | ✅ | '2130706433' does not look like a public domain name. |
| `localhost` | reserved name | 422 | `reserved_name` | `reserved_name` | ✅ | localhost is under the reserved name 'localhost', which never points at a public website. |
| `printer.internal` | internal-only suffix | 422 | `reserved_name` | `reserved_name` | ✅ | printer.internal is under the reserved name 'internal', which never points at a public website. |
| `127.0.0.1.nip.io` | real public DNS name that resolves to 127.0.0.1 | 422 | `non_public_address` | `non_public_address` | ✅ | 127.0.0.1.nip.io resolves to 127.0.0.1, which is not on the public internet. FIG only reads public sites. |
| `fig-nx-ca7ce00140.com` | domain that does not exist | 422 | `dns_failed` | `dns_failed` | ✅ | fig-nx-ca7ce00140.com does not resolve ([Errno 11001] getaddrinfo failed). |
| `ftp://launchvault.ca` | non-web scheme | 422 | `bad_scheme` | `bad_scheme` | ✅ | Only http and https sites can be read, not ftp://. |
| `not a hostname` | not a hostname at all | 422 | `bad_hostname` | `bad_hostname` | ✅ | 'not a hostname' contains spaces, so it is not a hostname or URL. |
| `(empty)` | empty input | 422 | `empty` | `empty` | ✅ | No hostname or URL was given. |

### 4. Pipeline

Trace total: 42.5 s inside the worker.

| Stage | Status | Time | What happened |
|---|---|---|---|
| `validate` | ok | 0 ms | launchvault.ca → launchvault.ca → 172.64.80.1 (all public) |
| `resolve_base` | ok | 1.1 s | https://launchvault.ca — tried: https://launchvault.ca/ ok 200 |
| `robots` | ok | 234 ms | parsed (HTTP 200) · 16 rules apply to FIGBot · 1 sitemap(s) declared |
| `discover` | ok | 968 ms | 1 sitemap file(s) read · 500 URLs listed · 500 on this site |
| `fetch` | ok | 31.6 s | 40 read · skipped: robots 2 · page limit reached |
| `rules` | ok | 78 ms | 138 flags from 7 distinct checks (craft 66, search 11, answers 36, structure 25) |
| `explain` | ok | 8.5 s | 7/7 distinct findings explained in 2 calls · 2,137 in / 699 out tokens · $0.0056 |
| `score` | ok | 0 ms | overall 82 (clean) · {'craft': 74, 'structure': 90, 'search': 87, 'answers': 76} |
| `persist` | ok | 172 ms | 40 pages and 138 findings saved, 138 with Claude-written text |

#### robots.txt

`https://launchvault.ca/robots.txt` → HTTP 200, outcome **parsed**, read in 234 ms.

Rules that apply to FIGBot (enforced before every request, including redirect hops):

```text
Allow: /
Allow: /features
Allow: /pricing
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /cookies
Allow: /refund-policy
Allow: /acceptable-use
Allow: /dpa
Disallow: /dashboard
Disallow: /onboarding
Disallow: /login
Disallow: /signup
Disallow: /checkout
Disallow: /api/
```

- Declared sitemap: `https://launchvault.ca/sitemap.xml`

**Independent robots check:** of 40 pages read, 0 are disallowed by robots.txt.

#### Discovery

| Sitemap | Outcome | HTTP | URLs | Child sitemaps | Time |
|---|---|---|---|---|---|
| `https://launchvault.ca/sitemap.xml` | ok | 200 | 1069 | 0 | 968 ms |

#### Pages

40 read, 2 skipped; stopped because: page limit reached.

| # | Path | Outcome | HTTP | Size | Time | Note |
|---|---|---|---|---|---|---|
| 1 | `/` | ✅ read | 200 | 149.8 KB | 1.1 s | “LaunchVault — Learn AI in Plain English. No Jargon, No Rush.” · 1682 words · sections: hero, content, features, content, features, content, pricing, content, content, faq, content, cta |
| 2 | `/learn-ai` | ✅ read | 200 | 40.8 KB | 578 ms | “Learn AI — Free AI Learning Platform to Master AI \| LaunchVault” · 808 words · sections: hero, content, content, content, faq, content |
| 3 | `/how-to-learn-ai` | ✅ read | 200 | 37.6 KB | 797 ms | “How to Learn AI in 2026 — Step-by-Step Guide \| LaunchVault” · 637 words · sections: hero, content, content |
| 4 | `/features` | ✅ read | 200 | 57.2 KB | 844 ms | “AI Learning Platform Features — Prompts, Courses & AI Agents \| LaunchVault” · 827 words · sections: hero, content, content, content, content, content, content |
| 5 | `/how-it-works` | ✅ read | 200 | 48.9 KB | 797 ms | “How to Learn AI with LaunchVault — How It Works” · 604 words · sections: hero, how, features, content, pricing, content |
| 6 | `/pricing` | ✅ read | 200 | 101.4 KB | 813 ms | “Pricing — AI Learning Platform Plans to Learn AI \| LaunchVault” · 903 words · sections: hero, content, content, content, pricing, content, content, cta, content |
| 7 | `/library` | ✅ read | 200 | 134.9 KB | 875 ms | “AI Prompt Library & Courses — Learn AI Free \| LaunchVault” · 1543 words · sections: hero, testimonials, content |
| 8 | `/glossary` | ✅ read | 200 | 258.4 KB | 891 ms | “AI Glossary — AI Terms & Concepts Explained Simply \| LaunchVault” · 2208 words · sections: hero, content, how |
| 9 | `/blog` | ✅ read | 200 | 161.6 KB | 687 ms | “Learn AI — Guides & Essays on Using AI \| LaunchVault Blog” · 1728 words · sections: hero, content, content, footer |
| 10 | `/about` | ✅ read | 200 | 49.8 KB | 625 ms | “About LaunchVault — How Our AI Learning Platform Works” · 793 words · sections: hero, content, content, content, content, content, content |
| 11 | `/contact` | ✅ read | 200 | 28.4 KB | 829 ms | “Contact — LaunchVault” · 250 words · sections: hero, content, content |
| 12 | `/signup` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/signup |
| 13 | `/login` | ⏭ robots | — | — | — | robots.txt disallows https://launchvault.ca/login |
| 14 | `/privacy` | ✅ read | 200 | 33.7 KB | 781 ms | “Privacy Policy — LaunchVault” · 1003 words · sections: hero, content, footer |
| 15 | `/terms` | ✅ read | 200 | 35.0 KB | 797 ms | “Terms of Service — LaunchVault” · 1089 words · sections: hero, content, footer |
| 16 | `/cookies` | ✅ read | 200 | 27.8 KB | 813 ms | “Cookie Policy — LaunchVault” · 441 words · sections: hero, content, footer |
| 17 | `/refund-policy` | ✅ read | 200 | 29.2 KB | 813 ms | “Cancellation Policy — LaunchVault” · 619 words · sections: hero, content, footer |
| 18 | `/acceptable-use` | ✅ read | 200 | 28.5 KB | 812 ms | “Acceptable Use Policy — LaunchVault” · 602 words · sections: hero, content, footer |
| 19 | `/dpa` | ✅ read | 200 | 30.1 KB | 797 ms | “Data Processing Addendum — LaunchVault” · 607 words · sections: hero, content, footer |
| 20 | `/domains/ai-prompting-mastery` | ✅ read | 200 | 86.7 KB | 921 ms | “AI Prompting Mastery — LaunchVault” · 1075 words · sections: hero, content, content, content |
| 21 | `/domains/prompt-engineering-fundamentals` | ✅ read | 200 | 76.4 KB | 844 ms | “Prompt Engineering Fundamentals — LaunchVault” · 934 words · sections: hero, content, content, content |
| 22 | `/domains/advanced-prompt-engineering` | ✅ read | 200 | 84.5 KB | 688 ms | “Advanced Prompt Engineering — LaunchVault” · 1039 words · sections: hero, content, content, content |
| 23 | `/domains/ai-for-business` | ✅ read | 200 | 85.2 KB | 812 ms | “AI for Business — LaunchVault” · 1043 words · sections: hero, content, content, content |
| 24 | `/domains/ai-business-models` | ✅ read | 200 | 84.7 KB | 797 ms | “AI Business Models — LaunchVault” · 1039 words · sections: hero, content, content, content |
| 25 | `/domains/ai-monetization` | ✅ read | 200 | 88.6 KB | 844 ms | “AI Monetization — LaunchVault” · 1081 words · sections: hero, content, content, content |
| 26 | `/domains/ai-automation-workflows` | ✅ read | 200 | 75.8 KB | 735 ms | “AI Automation & Workflows — LaunchVault” · 916 words · sections: hero, how, content, content |
| 27 | `/domains/no-code-ai-automation` | ✅ read | 200 | 88.5 KB | 797 ms | “No-Code AI Automation — LaunchVault” · 1082 words · sections: hero, content, content, content |
| 28 | `/domains/ai-agents-blueprints` | ✅ read | 200 | 111.9 KB | 843 ms | “AI Agents & Blueprints — LaunchVault” · 1454 words · sections: hero, content, content, content |
| 29 | `/domains/multi-agent-systems` | ✅ read | 200 | 92.9 KB | 750 ms | “Multi-Agent Systems — LaunchVault” · 1073 words · sections: hero, content, content, content |
| 30 | `/domains/agent-memory-tool-use` | ✅ read | 200 | 77.8 KB | 843 ms | “Agent Memory & Tool Use — LaunchVault” · 946 words · sections: hero, content, content, content |
| 31 | `/domains/machine-learning-basics` | ✅ read | 200 | 108.1 KB | 766 ms | “Machine Learning Basics — LaunchVault” · 1399 words · sections: hero, content, content, content |
| 32 | `/domains/deep-learning-basics` | ✅ read | 200 | 84.8 KB | 813 ms | “Deep Learning Basics — LaunchVault” · 1041 words · sections: hero, content, content, content |
| 33 | `/domains/data-literacy-for-ai` | ✅ read | 200 | 69.8 KB | 766 ms | “Data Literacy for AI — LaunchVault” · 865 words · sections: hero, content, content, content |
| 34 | `/domains/ai-coding-development` | ✅ read | 200 | 78.8 KB | 797 ms | “AI Coding & Development — LaunchVault” · 981 words · sections: hero, testimonials, content, content |
| 35 | `/domains/ai-app-building` | ✅ read | 200 | 65.9 KB | 860 ms | “AI App Building — LaunchVault” · 797 words · sections: hero, content, content, content |
| 36 | `/domains/ai-saas-building` | ✅ read | 200 | 70.4 KB | 766 ms | “AI SaaS Building — LaunchVault” · 865 words · sections: hero, content, content, content |
| 37 | `/domains/ai-productivity` | ✅ read | 200 | 88.8 KB | 750 ms | “AI Productivity & Personal Use — LaunchVault” · 1122 words · sections: hero, content, content, content |
| 38 | `/domains/ai-content-creation` | ✅ read | 200 | 72.3 KB | 891 ms | “AI Content Creation — LaunchVault” · 871 words · sections: hero, content, content, content |
| 39 | `/domains/ai-copywriting` | ✅ read | 200 | 64.8 KB | 718 ms | “AI Copywriting — LaunchVault” · 770 words · sections: hero, content, content, content |
| 40 | `/domains/ai-marketing` | ✅ read | 200 | 87.0 KB | 813 ms | “AI Marketing — LaunchVault” · 1072 words · sections: hero, content, content, content |
| 41 | `/domains/ai-sales` | ✅ read | 200 | 66.2 KB | 797 ms | “AI Sales — LaunchVault” · 793 words · sections: hero, content, content, content |
| 42 | `/domains/ai-customer-support` | ✅ read | 200 | 92.0 KB | 828 ms | “AI Customer Support — LaunchVault” · 1141 words · sections: hero, content, content, content |

#### Rules

138 flags over 40 pages. Deterministic — no model involved.

| Check | Layer | Times flagged |
|---|---|---|
| `overused_icons` | craft | 40 |
| `no_answerable_questions` | answers | 36 |
| `heading_skips` | structure | 25 |
| `generic_copy` | craft | 15 |
| `numbered_eyebrows` | craft | 11 |
| `meta_description_length` | search | 10 |
| `title_length` | search | 1 |

#### AI step (the only model call in the pipeline)

- Sent **7 items** (one per distinct finding) instead of 138 — a check that fires on many pages is explained once.
- Model `claude-haiku-4-5`, served as `claude-haiku-4-5-20251001`: 2 calls, 0 failed batches.
- Tokens: 2,137 input, 699 output → **$0.0056**.
- Explained 7, kept the rule's own text for 0.
- Request ids: `req_011Cf8HCqxdDxNAQVYmeeF7r`, `req_011Cf8HDL5K8uYfWrVXNCU3u`

#### Scores

| Layer | Score |
|---|---|
| Craft | 74 |
| Structure | 90 |
| Search | 87 |
| Answers | 76 |
| **Overall** | **82 — clean** |

### 5. Findings

#### Craft (74/100)

- **`generic_copy`** · medium · 15× on 15 pages (/, /how-it-works, /about, /domains/prompt-engineering-fundamentals…) · _Claude-written_
  - **Found (one example):** 1 instance(s) of generic marketing phrasing found in headings/copy
  - **Why:** Overused phrases like "Supercharge," "True Value," and "The Future of Work" appear across multiple pages, making the site read as template-driven rather than substantive.
  - **Fix:** Rewrite headings to be specific to LaunchVault's offering. For example, change "AI's True Value: It's Not Just About Automation" to something concrete like "Why Agent Memory Fails (And How LaunchVault Fixes It)."
- **`overused_icons`** · low · 40× on 40 pages (/domains/data-literacy-for-ai, /acceptable-use, /dpa, /domains/ai-customer-support…) · _Claude-written_
  - **Found (one example):** 3 uses of icons commonly overused in generated UI (sparkles, arrow-right)
  - **Why:** Heavy reliance on generic icons (arrow-right, sparkles, zap, rocket) is commonly associated with auto-generated layouts and reduces visual distinctiveness.
  - **Fix:** Replace 40% of generic icons with custom or fewer icons. Use arrow-right sparingly; remove sparkles and rocket icons entirely and rely on typography and color for visual hierarchy instead.
- **`numbered_eyebrows`** · low · 11× on 11 pages (/acceptable-use, /dpa, /, /how-to-learn-ai…) · _Claude-written_
  - **Found (one example):** Found 6 short numbered labels (01, 02, 03, 04, 05) — a common auto-generated 'step/feature' eyebrow pattern
  - **Why:** Numbered labels without context read as auto-generated step sequences rather than meaningful section markers, weakening the sense of deliberate content organization.
  - **Fix:** Replace numbered eyebrows with descriptive labels that reflect each section's actual purpose—e.g., "Getting Started," "Core Features," "Our Approach" instead of "1," "2," "3."

#### Structure (90/100)

- **`heading_skips`** · low · 25× on 25 pages (/domains/data-literacy-for-ai, /domains/ai-prompting-mastery, /domains/ai-coding-development, /domains/prompt-engineering-fundamentals…) · _Claude-written_
  - **Found (one example):** 2 places where the heading level jumps more than one step
  - **Why:** Heading jumps confuse screen readers and make the outline structure unclear, making it harder for readers to scan and understand page organization.
  - **Fix:** On /domains/advanced-prompt-engineering and similar pages, insert missing h2 tags between h1 and h3, and h3 tags between h2 and h4, to create a proper hierarchy without gaps.

#### Search (87/100)

- **`meta_description_length`** · low · 10× on 10 pages (/, /learn-ai, /how-to-learn-ai, /features…) · _Claude-written_
  - **Found (one example):** Meta description is 194 characters (long)
  - **Why:** At 194 characters, meta descriptions truncate in search results around 155–160 characters, cutting off key information and reducing click incentive.
  - **Fix:** Trim meta descriptions to 155 characters max. On the homepage, try: "Learn AI without jargon. Copy-ready prompts, courses, and agent blueprints across 50 everyday topics. Free to start."
- **`title_length`** · low · 1× on 1 page (/features) · _Claude-written_
  - **Found (one example):** Title is 74 characters and will be truncated
  - **Why:** At 74 characters, the /features page title exceeds the typical 60-character display limit in search results, cutting off "LaunchVault" on desktop.
  - **Fix:** Shorten to "AI Learning Features — Prompts, Courses & Agents | LaunchVault" (71 chars), or drop "Platform" to prioritize the value proposition.

#### Answers (76/100)

- **`no_answerable_questions`** · medium · 36× on 36 pages (/domains/data-literacy-for-ai, /contact, /domains/prompt-engineering-fundamentals, /features…) · _Claude-written_
  - **Found (one example):** No question-and-answer block on this page
  - **Why:** Pages without structured Q&A reduce chances of being cited by AI answer engines, which prioritize directly answerable questions and clear factual responses.
  - **Fix:** Add a FAQ section to /about and /contact pages. Example: "What makes LaunchVault different?" followed by 2–3 sentence factual answer, formatted as structured data schema.

### 6. Database cross-check

| | Database | API |
|---|---|---|
| Scan status | done | done |
| Findings | 138 | 138 |
| AI-written findings | 138 | 138 |
| Pages | 40 | 40 |
| Trace stored | True | True |
| Queue job | done, attempt 1 | — |

### 7. Checks

- ✅ **preflight** — database is Postgres, not a SQLite fallback
- ✅ **preflight** — Anthropic API key is set
- ✅ **preflight** — ai_explain is enabled
- ✅ **preflight** — scans.trace column exists
- ✅ **preflight** — API key minted on account `test-runs`
- ✅ **server** — backend answers /health
- ✅ **routes** — root lists the workspace API as not mounted
- ✅ **routes** — /health reports Postgres, ai_explain on, workspace API off
- ✅ **routes** — no browser origin is allowed (no CORS headers returned)
- ✅ **validation** — every unsafe target answered with the expected reason code
- ✅ **provision** — `launchvault.ca` stored as `launchvault.ca`
- ✅ **provision** — the URL form resolves to the same site (no duplicate)
- ✅ **ownership** — unverified (no TXT record) -- and a one-off scan is still allowed
- ✅ **scan** — scan finished as `done`
- ✅ **results** — trace covers every pipeline stage
- ✅ **results** — report lists this site
- ✅ **results** — no page the scan read is disallowed by robots.txt (independent check)
- ✅ **database** — findings in the database match the API
- ✅ **database** — AI-written flags match the API
- ✅ **database** — pages in the database match the API
- ✅ **database** — trace stored on the scan row
- ✅ **database** — queue job finished on its first attempt
- Plus 32 route calls in section 2, 32 as expected.

### 8. Issues observed

- ℹ️ 2 page(s) skipped because the site's robots.txt disallows them — expected, and correct: /signup, /login

### 9. Server log (application lines, redacted)

```text
2026-09-16 23:11:25,190 INFO fig.jobs: worker w1 up
2026-09-16 23:11:25,190 INFO fig.jobs: worker w2 up
2026-09-16 23:11:25,190 INFO fig: FIG API up - db postgres, ai_explain claude-haiku-4-5, workspace API off (disconnected from the frontend)
2026-09-16 23:12:13,612 INFO fig.pipeline: scan a092e2a7-b669-45a0-ac81-eb79d554bc22 done: 40 pages, score 82, 42516 ms
```
