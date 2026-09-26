"""Build frontend/lib/sample-report.json: the /report/sample page's data.

Not hand-written. It runs the seed's fixture pages for an invented site
through the real rules engine and scoring, so every check name, "why",
"fix" and evidence snippet is exactly what a real scan would produce, in
the same shape GET /scan/{id} returns. Re-run after changing the rules:

    python scripts/make_sample_report.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("FIG_DATABASE_URL", "sqlite://")

from app.rules.checks import CHECKLIST, check_llms_txt, run_all_checks  # noqa: E402
from app.rules.scoring import LAYER_LABEL, layer_scores, overall, verdict  # noqa: E402
from app.scraper import parse_html  # noqa: E402
from app.seed import _good_page, _order_page, _slop_page, _thin_page  # noqa: E402

HOST = "northwind-coffee.example"  # .example is reserved: can never be a real site
NAME = "Northwind Coffee"
PAGES = [("/", _slop_page), ("/pricing", _order_page), ("/about", _thin_page), ("/journal/brewing-guide", _good_page)]

flags = []
for path, build in PAGES:
    url = f"https://{HOST}{path}"
    for f in run_all_checks(parse_html(url, build(HOST, NAME, path))):
        f.page_url = url
        flags.append(f)
site_flag = check_llms_txt(False)
if site_flag:
    flags.append(site_flag)

TITLE = {cid: e["title"] for e in CHECKLIST for cid in e["ids"]}
layers = layer_scores(flags, pages=len(PAGES))
score = overall(layers)
report = {
    "scan_id": "sample",
    "hostname": HOST,
    "status": "done",
    "pages": len(PAGES),
    "score": score,
    "verdict": verdict(score),
    "finished_at": "2026-09-26T15:00:00+00:00",
    "layers": layers,
    "findings": [
        {"check": f.check, "title": TITLE.get(f.check), "layer": f.layer, "layer_label": LAYER_LABEL.get(f.layer, f.layer),
         "severity": f.severity, "summary": f.summary, "why": f.why, "fix": f.fix,
         "evidence": f.evidence or [], "page": f.page_url or None}
        for f in flags
    ],
}
out = Path(__file__).resolve().parent.parent / "frontend" / "lib" / "sample-report.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"{out.name}: score {score} ({report['verdict']}), {len(flags)} findings, layers {layers}")
