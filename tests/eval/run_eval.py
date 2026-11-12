"""End-to-end evaluation: the 4 public questions + prescription scenarios through POST /ask.

    uv run python tests/eval/run_eval.py                         # in-process (FastAPI TestClient)
    uv run python tests/eval/run_eval.py --url http://localhost:8000   # a running server / the container

Checks per case: HTTP 200, expected source files cited, at least one citation, the disclaimer, and for
prescription cases the verdict. Writes a markdown report (default `docs/eval_report.md`); exit code 1 if
any check fails. Uses the real LLM endpoint from `.env` (a full run takes a few minutes).
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = "not medical advice"

CASES = [
    # --- the 4 public evaluation questions (expected files from the assignment) ---
    {
        "name": "Q1 warfarin contraindications",
        "request": {"question": "What are the main contraindications for warfarin?"},
        "files": {"dailymed-warfarin.md"},
    },
    {
        "name": "Q2 warfarin vs apixaban",
        "request": {
            "question": "Compare the contraindications of warfarin and apixaban. What conditions are shared "
            "and which are unique to each drug?"
        },
        "files": {"dailymed-warfarin.md", "dailymed-apixaban.md"},
    },
    {
        "name": "Q3 warfarin + sertraline bleeding",
        "request": {
            "question": "A patient currently on warfarin is prescribed sertraline. What is the risk of "
            "bleeding and what monitoring is recommended?"
        },
        "files": {"dailymed-warfarin.md", "dailymed-sertraline.md"},
    },
    {
        "name": "Q4 metformin at eGFR 25",
        "request": {
            "question": "A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin "
            "contraindicated at this level of renal function, and what is the threshold?"
        },
        "files": {"dailymed-metformin.md"},
    },
    # --- prescription scenarios (validate_prescription / write_prescription) ---
    {
        "name": "Validate metformin, eGFR 25",
        "request": {
            "question": "Validate this prescription for the patient: metformin 500 mg twice daily.",
            "patient": {"age": 67, "sex": "male", "egfr": 25, "hepatic_impairment": "none"},
        },
        "files": {"dailymed-metformin.md"},
        "verdicts": {"rejected"},
    },
    {
        "name": "Validate sertraline on warfarin",
        "request": {
            "question": "Validate this prescription for the patient: sertraline 50 mg once daily.",
            "patient": {
                "age": 58,
                "sex": "male",
                "egfr": 80,
                "hepatic_impairment": "none",
                "current_medications": ["warfarin"],
            },
        },
        "files": {"dailymed-sertraline.md"},
        "verdicts": {"approved_with_warnings", "needs_more_info"},  # interaction: never a clean approval
    },
    {
        "name": "Validate amoxicillin, amoxicillin allergy",
        "request": {
            "question": "Validate this prescription for the patient: amoxicillin 500 mg every 8 hours.",
            "patient": {"age": 30, "sex": "male", "allergies": ["amoxicillin (hives)"]},
        },
        "files": set(),
        "verdicts": {"rejected"},  # deterministic allergy precheck
    },
    {
        "name": "Validate amoxicillin, penicillin allergy",
        "request": {
            "question": "Validate this prescription for the patient: amoxicillin 500 mg every 8 hours.",
            "patient": {"age": 30, "sex": "male", "egfr": 90, "allergies": ["penicillin (anaphylaxis)"]},
        },
        "files": {"dailymed-amoxicillin.md"},
        "verdicts": {"rejected"},  # class allergy: caught by the LLM review from the label, not the precheck
    },
    {
        "name": "Write first-line T2D",
        "request": {
            "question": "Write a prescription for this request and validate it for the patient: first-line "
            "oral therapy for newly diagnosed type 2 diabetes.",
            "patient": {
                "age": 60,
                "sex": "female",
                "egfr": 75,
                "hepatic_impairment": "none",
                "pregnant": False,
                "breastfeeding": False,
            },
        },
        "files": {"dailymed-metformin.md"},
        "verdicts": {"approved", "approved_with_warnings", "needs_more_info"},
        "draft_drug": "metformin",
    },
]


def run_case(client: httpx.Client, case: dict) -> dict:
    start = time.monotonic()
    try:
        r = client.post("/ask", json=case["request"])
    except httpx.HTTPError as e:
        return {"case": case, "secs": time.monotonic() - start, "failures": [f"request failed: {e!r}"]}
    secs = time.monotonic() - start
    if r.status_code != 200:
        return {"case": case, "secs": secs, "failures": [f"HTTP {r.status_code}: {r.text[:200]}"]}

    body = r.json()
    cited = {c["file"] for c in body["citations"]}
    validation = body.get("validation") or {}
    draft_drugs = [i["drug"].lower() for i in (body.get("draft") or {}).get("items", [])]
    failures = []
    if missing := case["files"] - cited:
        failures.append(f"expected source not cited: {sorted(missing)}")
    if case["files"] and not body["citations"]:
        failures.append("no citations")
    if DISCLAIMER not in body["answer"]:
        failures.append("disclaimer missing")
    if "verdicts" in case and validation.get("verdict") not in case["verdicts"]:
        failures.append(f"verdict {validation.get('verdict')!r} not in {sorted(case['verdicts'])}")
    if "draft_drug" in case and case["draft_drug"] not in draft_drugs:
        failures.append(f"draft {draft_drugs} lacks {case['draft_drug']}")
    return {"case": case, "secs": secs, "failures": failures, "body": body, "cited": cited}


def report(results: list[dict], target: str) -> str:
    passed = sum(not r["failures"] for r in results)
    lines = [
        "# PharmaAssist evaluation report",
        "",
        f"- Run: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC against `{target}`",
        f"- Result: **{passed}/{len(results)} cases passed**",
        "",
        "| Case | Result | Time | Critic | Revisions | Verdict | Cited files |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        body = r.get("body") or {}
        verdict = (body.get("validation") or {}).get("verdict", "—")
        critic = (body.get("review") or {}).get("verdict", "—")
        cited = ", ".join(f"`{f}`" for f in sorted(r.get("cited", ()))) or "—"
        status = "PASS" if not r["failures"] else "FAIL: " + "; ".join(r["failures"])
        lines.append(
            f"| {r['case']['name']} | {status} | {r['secs']:.0f} s | {critic} | {body.get('revisions', '—')} "
            f"| {verdict} | {cited} |"
        )
    for r in results:
        if body := r.get("body"):
            lines += ["", f"## {r['case']['name']}", "", f"> {r['case']['request']['question']}", ""]
            if body.get("plan"):
                lines += ["Plan: " + " → ".join(body["plan"]), ""]
            lines += [body["answer"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", help="Base URL of a running server (default: in-process TestClient)")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "eval_report.md")
    parser.add_argument("--workers", type=int, default=2, help="Cases run in parallel (proxy rate limits)")
    args = parser.parse_args()

    if args.url:
        client = httpx.Client(base_url=args.url, timeout=600)
    else:
        from fastapi.testclient import TestClient

        from pharma_assist.api import app

        client = TestClient(app)  # same request path as the server, without the network hop
    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(lambda c: run_case(client, c), CASES))

    for r in results:
        status = "PASS" if not r["failures"] else "FAIL"
        print(f"{status}  {r['secs']:5.0f}s  {r['case']['name']}  {r['failures']}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report(results, args.url or "in-process"), encoding="utf-8")
    print(f"Report: {args.out}")
    return 0 if all(not r["failures"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
