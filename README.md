# PharmaAssist

An agentic pharmacology research assistant over a local corpus of FDA DailyMed labels and MedlinePlus
monographs for 10 drugs (acetaminophen, albuterol, amoxicillin, apixaban, aspirin, atorvastatin, ibuprofen,
metformin, sertraline, warfarin) plus a glossary.

A LangGraph agent **plans** the question, **retrieves** passages with in-memory hybrid search, **chooses
its own tools** (`build_context`, `validate_prescription`, `write_prescription`), has a **critic** check
every claim against the retrieved passages, and **answers** with numbered citations to the corpus files and
a "not medical advice" disclaimer. A Next.js UI shows the agent's work live.

> Research and education only. Not medical advice.

## Quick start (Docker)

```bash
cp .env.example .env   # OPENAI_API_KEY, OPENAI_BASE_URL (or OPENAI_BASE_UR), OPENAI_MODEL, OPENAI_EMBEDDING_MODEL
docker build -t agent . && docker run -p 8000:8000 --env-file .env agent
```

| Endpoint | |
|---|---|
| `GET /` | Web UI (Ask · Validate · Write) |
| `GET /health` | `200 {"status": "ok", "index_ready": bool}`: the embedding index builds in ~15-25 s after start; `/health` is 200 meanwhile |
| `POST /ask` | `{"question": "...", "patient": {...}?}` → `{answer, citations, plan, review, revisions, validation, draft}` |
| `POST /ask/stream` | Same request; Server-Sent Events: `plan`, `tool_call`, `tool_result`, `review`, `final` (or `error`) |

```bash
curl -s localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "What are the main contraindications for warfarin?"}'
```

`patient` is optional and structured (`age, sex, weight_kg, egfr, hepatic_impairment, pregnant, breastfeeding,
conditions, allergies, current_medications`). Fields left out are **unknown, not normal**: if a label rule
depends on one, validation asks for it instead of approving.

## How it works

```
START → planner → agent ⇄ tools → critic ─(revise, once)→ agent
                                    └─(approve / budget spent)→ finalizer → END
```

| Assignment step | Implementation |
|---|---|
| **Plan** | `planner` node: structured output (`Plan`) breaks the question into 1-4 steps. |
| **Retrieve** | `retrieval.py`: heading-aware markdown chunks (528, ≤300 words, `Drug › 4 CONTRAINDICATIONS` headings, canonical section tags). Hybrid in-memory search: numpy cosine on OpenAI embeddings + BM25, fused with Reciprocal Rank Fusion, filterable by drug and section. Embeddings are cached in `.cache/` per corpus+model hash. |
| **Use tools** | `agent` node: the LLM gets the three tools via `bind_tools` and decides which to call, with which filters, how often. Nothing routes on keywords. |
| **Review** | `critic` node: structured `Critique` checks each claim against the retrieved passages, lists unsupported claims and clinically ambiguous points. One rewrite is allowed; whatever remains unverified is shown to the user as reviewer notes. |
| **Answer** | `finalizer` node: citation ids are renumbered to `[1]`, `[2]`… (ids the model invented are dropped), a numbered source list (file + section) and the disclaimer are added **in code**. |

### Tools (`backend/pharma_assist/tools.py`)

- **`build_context(query, drugs?, sections?, k)`**: returns passages tagged with citation ids
  (`[dailymed-warfarin.md#13]`). Drugs and sections are enums, so the model cannot ask for what is not there.
- **`validate_prescription(prescription, patient)`**:
  1. Deterministic prechecks: drugs outside the corpus → `needs_more_info`, documented allergy → `critical`.
  2. Targeted retrieval per drug: contraindications, dosing, renal, hepatic, pregnancy/lactation (unless
     ruled out), age extremes, the patient's conditions/allergies, and **interactions in both directions**
     (drug A's label may mention B when B's label is silent about A).
  3. Structured LLM review that must cite passage ids; invented ids are removed.
  4. **The verdict is computed in code, failing closed**: any critical issue → `rejected`; missing patient
     data or an unvalidated drug → `needs_more_info`; otherwise `approved_with_warnings` / `approved`.
- **`write_prescription(description, patient?)`**: drafts from indication and dosing passages (corpus drugs
  only), then always runs `validate_prescription` on the draft.

Every tool returns `(text for the LLM, artifact)`; the artifacts carry the retrieved passages, so citations
always point at real corpus chunks.

### Layout

```
backend/pharma_assist/  config.py · llm.py · retrieval.py · schemas.py · tools.py · agent.py · api.py
frontend/               Next.js 16 (App Router, TypeScript, Tailwind), static export served by FastAPI at /
tests/                  unit tests (fake LLM + fake embeddings, no network) and `-m live` tests
tests/eval/run_eval.py  end-to-end evaluation through POST /ask → docs/eval_report.md
corpus/                 the 21 provided markdown files (unchanged)
.agents/, AGENTS.md     AI coding configuration (rules, skills, build plan and log)
```

## Evaluation

`uv run python tests/eval/run_eval.py [--url http://localhost:8000]` runs the 4 public questions and 5
prescription scenarios through `POST /ask` and checks: HTTP 200, the expected source files are cited, the
disclaimer is present, and (for prescriptions) the verdict. Last run, against the Docker container
(full answers in [`docs/eval_report.md`](docs/eval_report.md)):

| Case | Result | Time | Verdict | Cited files |
|---|---|---|---|---|
| Q1 warfarin contraindications | PASS | 10 s | — | `dailymed-warfarin.md` |
| Q2 warfarin vs apixaban | PASS | 12 s | — | `dailymed-apixaban.md`, `dailymed-warfarin.md` |
| Q3 warfarin + sertraline bleeding | PASS | 75 s | needs_more_info¹ | `dailymed-sertraline.md`, `dailymed-warfarin.md` |
| Q4 metformin at eGFR 25 | PASS | 13 s | — | `dailymed-metformin.md` |
| Validate metformin, eGFR 25 | PASS | 14 s | rejected | `dailymed-metformin.md` |
| Validate sertraline on warfarin | PASS | 77 s | approved_with_warnings | sertraline, warfarin labels |
| Validate amoxicillin, amoxicillin allergy | PASS | 55 s | rejected | `dailymed-amoxicillin.md` |
| Validate amoxicillin, penicillin allergy | PASS | 67 s | rejected | amoxicillin label + monograph |
| Write first-line T2D | PASS | 56 s | approved | `dailymed-metformin.md` |

¹ In this run the agent chose to also call `validate_prescription` for Q3 (no dose or patient data was given,
so it correctly returned `needs_more_info`).

LLM output varies between runs; the checks are on sources, disclaimer and verdicts, not exact wording.

## Develop

```bash
uv sync
uv run uvicorn pharma_assist.api:app --port 8000      # API (+ UI from frontend/out if built)
cd frontend && npm ci && npm run dev                  # UI with hot reload on :3000 (calls the API on :8000)
uv run ruff check backend tests && uv run pytest -q   # 55 unit tests, no network
uv run pytest -m live                                 # 16 tests against the configured LLM endpoint
```

Python 3.12 with exact `==` pins in `pyproject.toml` + `uv.lock`; npm versions pinned exactly in
`frontend/package.json` + `package-lock.json`.

## Design notes and limits

- **Config quirks handled**: `OPENAI_BASE_UR` (the provided `.env`'s typo) is accepted as well as
  `OPENAI_BASE_URL`, and quotes are stripped because `docker run --env-file` keeps them literally.
- **Embeddings are batched** (64 inputs per request): a single 528-input request put the LiteLLM proxy into
  a rate-limit cooldown.
- **Latency**: plain questions take ~10-30 s; prescription checks and interaction questions 1-1.5 min (tool
  call + LLM review + critic). `/ask/stream` shows progress and sends keep-alive pings meanwhile.
- **Generic names only**: brand names are not mapped (the UI suggests the 10 corpus drugs).
- **No auth or rate limiting** on the API: it is built for a local demo or grading run, not public hosting.
- **One worker per container**: the index lives in process memory.

## AI coding configuration

`AGENTS.md` holds the operating rules, architecture decisions and a step-by-step build log. `.agents/`
holds the always-on Ponytail rule (smallest complete change) and the skills used while building it,
including reviewed domain skills (CDSS patterns, FastAPI, Next.js, Docker, pytest) from `affaan-m/ECC`.
