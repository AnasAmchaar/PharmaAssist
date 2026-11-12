# PharmaAssist — Full Context, Architecture & Implementation Plan

> **How to use this file:** In any new session, tell the agent: *"Read `AGENTS.md` and resume from the current step in the 8-step plan."* Antigravity and other coding agents also load `AGENTS.md` automatically as workspace rules.

---

## 1. Operating Rules (Strict)

1. **Step-by-step execution:** Work one step at a time from the 8-Step Plan below. At the end of each step:
   - Run linter (`uv run ruff check backend tests`) and tests (`uv run pytest -q`).
   - Run the `/ponytail-review` checklist on the step's diff (`.agents/skills/ponytail-review/SKILL.md`).
   - Fix any **Must fix** items immediately.
   - Commit the step locally (`git commit`).
   - Report what was built, verified, and reviewed, then **stop and wait for user "go"** before starting the next step.
2. **Ponytail mode (`full`):** Installed in `.agents/rules/ponytail.md` and `.agents/skills/ponytail*` (upstream commit `96608e0`, MIT).
   - Solve the whole problem with the least new code.
   - Prefer standard library / platform / already-installed dependencies before writing helpers or adding packages.
   - No speculative abstractions, wrappers, or config nobody sets.
   - Leave one small test for non-trivial logic.
   - Mark known limits with `shortcut: <limit>, <when to upgrade>`.
   - End every reply with 1–2 lines: what was skipped/not checked, and any risk the user must know.
   - **Never cut:** validation at trust boundaries, error handling, security, accessibility, or anything the user explicitly asked for.
3. **Domain skills (ECC, MIT, `affaan-m/ECC@d2ef268`, reviewed before install):** load the matching skill from `.agents/skills/` when working on that area.
   - `healthcare-cdss-patterns` → Step 3 `validate_prescription` (severity tiers, fail closed on missing patient data, bidirectional interaction checks).
   - `python-testing` → all pytest work. `fastapi-patterns` → Step 5. `frontend-patterns` + `nextjs-turbopack` → Step 6. `docker-patterns` → Step 7 (ignore its ECC "installer harness" section).
   - **Ponytail wins on conflict:** no coverage targets, no router/service/repository layers, no extra deps (e.g. `asgi-lifespan`) unless a test truly needs them.
4. **Assignment check:** before closing each step, re-check it against `assignment-pharma.pdf` (Section 2 below) and say which requirements the step touched.

---

## 2. Assignment Specification (from `assignment-pharma.pdf`)

- **Objective:** Build an agentic pharmacology research assistant in Python over a local `corpus/` of 21 markdown files (10 drugs × DailyMed FDA labels + MedlinePlus consumer monographs + `GLOSSARY.md`).
- **5 Mandatory Agent Steps:**
  1. **Plan:** Decompose the user question into sub-questions or steps.
  2. **Retrieve:** Fetch relevant passages from `corpus/` using in-memory similarity.
  3. **Use tools:** At least two local tools; tool choice **must be driven by the agent** (LLM `bind_tools`), never hardcoded.
  4. **Review (Critic):** Verify grounding against retrieved passages and flag unsupported or clinically ambiguous claims before emitting the final answer.
  5. **Answer:** Produce a cited response referencing the source file(s) used, with an **explicit disclaimer** that the output is not medical advice.
- **User-Requested Tools (all 3 required):**
  1. `build_context`: Retrieve grounded passages from the corpus for the LLM.
  2. `validate_prescription`: Take a prescription + patient details and validate safety, contraindications, dosing, and interactions.
  3. `write_prescription`: Draft a prescription from a user description (corpus drugs only) and automatically validate it through `validate_prescription`.
- **Mandatory Technical & Interface Requirements:**
  - Python 3.11+ (using Python 3.12), dependencies pinned with `==` in `pyproject.toml` + `uv.lock`.
  - `Dockerfile` at repo root:
    ```bash
    docker build -t agent . && docker run -p 8000:8000 --env-file .env agent
    ```
    must start the self-contained container (graders inject their own `.env`).
  - `GET /health` → `200`
  - `POST /ask` with `{"question": "..."}` → `200`
  - Frontend calling `/ask` (built with **Next.js** per user request).
  - Push AI coding configuration to the repo (`.agents/` + `AGENTS.md`).
  - **Never commit `.env`** (contains a live LiteLLM key).

### Public Evaluation Questions & Expected Sources

| # | Question | Expected source file(s) |
|---|---|---|
| 1 | What are the main contraindications for warfarin? | `dailymed-warfarin.md` |
| 2 | Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug? | `dailymed-warfarin.md`, `dailymed-apixaban.md` |
| 3 | A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended? | `dailymed-warfarin.md`, `dailymed-sertraline.md` |
| 4 | A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold? | `dailymed-metformin.md` |

---

## 3. Environment & Corpus Context

- **Corpus (`corpus/`):** 10 drugs (`acetaminophen`, `albuterol`, `amoxicillin`, `apixaban`, `aspirin`, `atorvastatin`, `ibuprofen`, `metformin`, `sertraline`, `warfarin`), each with `dailymed-<drug>.md` and `medlineplus-<drug>.md`, plus `GLOSSARY.md`.
  - DailyMed files use numbered FDA sections (`## 1 INDICATIONS AND USAGE`, `## 2 DOSAGE AND ADMINISTRATION`, `## 4 CONTRAINDICATIONS`, `## 5 WARNINGS AND PRECAUTIONS`, `## 7 DRUG INTERACTIONS`, `## 8 USE IN SPECIFIC POPULATIONS`, etc.), except OTC labels (`acetaminophen`, `aspirin`) which use `## Uses`, `## Directions`, `## Warnings`.
  - MedlinePlus files use Q&A headings (`## Why is this medication prescribed?`, `## How should this medicine be used?`, `## What special precautions should I follow?`, `## What side effects can this medication cause?`, etc.).
- **`.env` Quirks discovered in Step 1:**
  - Ships with a typo: `OPENAI_BASE_UR='https://llm.ai.syntax-rnd.com'` (missing `L`). `backend/pharma_assist/config.py` accepts both `OPENAI_BASE_URL` and `OPENAI_BASE_UR` via `AliasChoices`.
  - Configured models: `OPENAI_MODEL='gpt-5.6-terra'`, `OPENAI_EMBEDDING_MODEL='text-embedding-3-small'`.
  - Values are quoted. `docker run --env-file` keeps quotes literally, so `config.py` strips one pair of matching quotes from every setting.
- **Proxy capabilities (probed in Step 1):** chat, embeddings (1536-dim), `bind_tools` tool calls, structured output with both `json_schema` (langchain default, used) and `function_calling`, and `temperature=0` (set in `llm.py`) all work.
- **Proxy limits (found in Step 2):** one embeddings request with all 528 chunks (~70k tokens) put the LiteLLM deployment into a 429 "cooldown" and the client hung on retry-after. `llm.py` now batches 64 inputs per request and sets timeouts; a cold index build takes ~25 s, a cached one ~0.3 s.
- **Local Python/Tooling Quirks on Windows:**
  - `C:\msys64\ucrt64\bin\python.exe` is first on `PATH` and lacks `pip`. Always run Python tools via `uv run ...` (which uses CPython 3.12 in `.venv`).

---

## 4. Agreed Architecture & Design Decisions

1. **LangGraph Custom `StateGraph` (`Planner → ReAct Agent ⇄ Tools → Critic → Revise or Finalize`):**
   ```
   START -> planner -> agent --(tool_calls)--> tools -> agent
                         |
                   (no tool_calls)
                         v
                       critic --(revise & revisions < MAX_REVISIONS)--> agent
                         |
              (approve or max reached)
                         v
                     finalizer -> END
   ```
2. **Deterministic Citations (`content_and_artifact`):**
   - Tools return `(text_for_llm, artifact)` using LangChain's `response_format="content_and_artifact"`. `build_context`'s artifact is `list[Source]`; `validate_prescription` → `ValidationResult`, `write_prescription` → `DraftResult` (both have `.sources`).
   - Citation keys are **chunk ids** (`[dailymed-warfarin.md#13]`), unique across tool calls, so no per-call `[S#]` numbering has to be merged. `collect_sources` merges ToolMessage artifacts by id; the finalizer renumbers cited ids to `[1]`, `[2]` and drops ids that were never retrieved.
   - The medical disclaimer is appended in code inside `finalizer`.
3. **In-Memory Hybrid Retrieval (`retrieval.py`):**
   - Heading-aware markdown chunker preserving heading hierarchy (`Warfarin › 4 CONTRAINDICATIONS`) + canonical section tag (`indications | dosage | contraindications | warnings | interactions | adverse_reactions | specific_populations | pharmacology | overdose | other`).
   - Hybrid scoring: numpy cosine similarity on OpenAI embeddings + BM25 (`rank-bm25`), combined with Reciprocal Rank Fusion (RRF), with optional `drugs` and `sections` filters.
   - Disk cache at `.cache/emb-<sha256(corpus+model)>.npy` so embeddings are computed once per corpus/model hash.
4. **Single-Container Deployment:**
   - Multi-stage `Dockerfile`: Stage 1 builds Next.js static export (`output: "export"` → `/web/out`); Stage 2 runs FastAPI on `:8000` serving `/health`, `/ask`, `/ask/stream` (via built-in `fastapi.sse`), and mounts the static Next.js export at `/`.
5. **Single-Page Next.js UI (`Ask · Validate · Write`):**
   - One page with three tabs, a structured `PatientProfile` form (`age, sex, weight_kg, egfr, hepatic_impairment, pregnant, breastfeeding, conditions, allergies, current_medications`), clickable example questions, live SSE agent trace (plan → tool calls → critic review), and cited answers.

### Target Repository Layout

```
PharmaAssist/
├── .agents/                  # Ponytail skills & always-on rule (committed as AI config)
├── AGENTS.md                 # This file: full context, rules & implementation plan
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── README.md
├── pyproject.toml
├── uv.lock
├── corpus/                   # 21 pharmacology markdown files (unchanged)
├── backend/pharma_assist/
│   ├── __init__.py
│   ├── config.py             # Settings (handles OPENAI_BASE_URL + OPENAI_BASE_UR)
│   ├── llm.py                # ChatOpenAI + OpenAIEmbeddings factories
│   ├── schemas.py            # CorpusDrug/Section enums, PatientProfile, PrescriptionItem, Issue, ValidationReport, Draft*, Source, Plan, Critique, AskRequest/AskResponse
│   ├── retrieval.py          # Markdown section chunker + HybridIndex (cosine + BM25 + RRF) + .cache
│   ├── tools.py              # build_context, validate_prescription, write_prescription
│   ├── agent.py              # LangGraph StateGraph (planner, agent, tools, critic, finalizer)
│   └── api.py                # FastAPI (/health, /ask, /ask/stream SSE, static mount)
├── frontend/                 # Next.js (App Router, TypeScript, Tailwind, output: "export")
└── tests/
    ├── test_config.py
    ├── test_retrieval.py
    ├── test_tools.py
    ├── test_agent.py
    ├── test_api.py
    └── eval/run_eval.py
```

---

## 5. 8-Step Implementation Plan & Status Tracker

### Step 1 — Scaffolding, Config & LLM Connectivity *(DONE)*
- [x] `git init -b main`, `.gitignore`, `.dockerignore`, `.env.example`, `README.md`.
- [x] `pyproject.toml` with exact `==` pins (`fastapi==0.162.4`, `langgraph==1.2.20`, `langchain-core==1.8.0`, `langchain-openai==1.7.4`, `numpy==2.4.6`, `pydantic==2.14.3`, `pydantic-settings==2.16.2`, `rank-bm25==0.2.2`, `uvicorn[standard]==0.54.0`) + dev deps (`pytest`, `pytest-asyncio`, `httpx`, `ruff`) + `uv.lock`.
- [x] Ponytail installed in `.agents/rules/ponytail.md` and `.agents/skills/ponytail*`.
- [x] `backend/pharma_assist/config.py` and `backend/pharma_assist/llm.py`.
- [x] Live LLM smoke test against the proxy → kept as `tests/test_llm_live.py` (`uv run pytest -m live`).
- [x] `tests/test_config.py` (`OPENAI_BASE_UR` fallback, quote stripping, missing key fails).
- [x] ECC domain skills installed (see Section 1.3).
- [x] Lint, tests, `/ponytail-review`, commit.

### Step 2 — Hybrid In-Memory Retrieval (`retrieval.py`) *(DONE)*
- [x] Heading-aware chunker: 528 chunks (≤300 words, split on lines then sentences, since many label sections are one long line), canonical section from the `##` heading, `url` from the `Source:` line.
- [x] `HybridIndex` (numpy cosine + `BM25Okapi` + RRF, BM25 zero-scores ignored, `drugs`/`sections` filters, `.cache/emb-<sha256(model + chunk texts)>.npy`, atomic write). `get_index()` singleton.
- [x] `tests/test_retrieval.py`: unit (section mapping, chunking, filters, fusion index mapping, cache reuse) + live (warfarin contraindications top-1; all 4 eval questions retrieve their expected files in top-8).
- [x] Lint, test, `/ponytail-review`, commit.

### Step 3 — Schemas & Agent Tools (`schemas.py`, `tools.py`) *(DONE)*
- [x] `schemas.py`: models used by the tools. `CorpusDrug` / `Section` enums are tested against the corpus.
- [x] `build_context(query, drugs, sections, k)` → passages rendered as `[chunk-id] heading\ntext` + `list[Source]`.
- [x] `validate_prescription` / `run_validation`: deterministic prechecks (out-of-corpus, documented allergy) → per-drug targeted retrieval (contraindications, dosing, renal, hepatic, pregnancy if not ruled out, age extremes, conditions/allergies, interactions **both directions** with current meds and co-prescribed drugs) → structured LLM review → invented citation ids dropped → **verdict computed in code** (critical → rejected; missing_info/out_of_corpus → needs_more_info; else approved[_with_warnings]). Unknown patient fields are "unknown, not normal" (fail closed, per `healthcare-cdss-patterns`).
- [x] `write_prescription` / `run_draft`: indication + dosing retrieval → structured draft (corpus drugs only) → always validated.
- [x] `tests/test_tools.py`: fake-LLM unit tests (verdict rules, allergy precheck, out-of-corpus skips LLM, citation filtering, bidirectional interaction retrieval, draft auto-validation) + live (metformin eGFR 25 rejected citing the metformin label; sertraline + warfarin interaction flagged; T2D draft → metformin).
- [x] Lint, test, `/ponytail-review` (fixed: empty prescription was approved; blank drug name matched every allergy), commit.
- Note: hepatic status left unknown usually yields `needs_more_info` (labels of metformin/sertraline depend on it). Intended; the UI should make it easy to set.

### Step 4 — LangGraph Agent (`agent.py`) *(DONE)*
- [x] `StateGraph(AgentState)`: `planner` (structured `Plan`) → `agent` (`bind_tools(TOOLS)`, LLM picks tools) ⇄ `tools` (`ToolNode`, `handle_tool_errors=True`) → `critic` (structured `Critique`: unsupported claims, ambiguities, feedback) → `agent` (feedback as a HumanMessage) or `finalizer`. `ask(question)` returns the final state (`plan`, `messages`, `critique`, `revisions`, `answer`, `citations`).
- [x] Loop guards are module constants: `MAX_TOOL_ROUNDS=8` (then `tool_choice="none"`), `MAX_REVISIONS=2`, `RECURSION_LIMIT=50` backstop. `GraphRecursionError` / LLM errors propagate: Step 5 must turn them into an error response/event.
- [x] Sources are collected from ToolMessage artifacts (no reducer). `renumber_citations`: `[a.md#1, b.md#2]` → `[1][2]` in order of first use, unknown ids dropped, non-citation brackets kept. Finalizer appends reviewer notes (ambiguities; unverified claims if the revision budget ran out), a numbered **Sources** list (file + heading), and `DISCLAIMER` in code.
- [x] Live: all 4 public questions cite their expected files (Q1 15s/0 revisions, Q2 32s/1, Q3 78s/2, Q4 13s/0).
- [x] `tests/test_agent.py` (fake LLM: citation renumbering, tool → revise → finalize flow, revision budget flags claims, tool budget forces an answer; live: 4 eval questions). `FakeLLM`, `fake_llm` and `EVAL_QUESTIONS` live in `tests/conftest.py`.
- [x] Lint, test, `/ponytail-review` (fixed: `max_revisions` setting nobody set could push runs past the recursion limit → constant), commit.

### Step 5 — FastAPI Service (`api.py`) *(DONE)*
- [x] `GET /health` → `200 {"status": "ok", "index_ready": bool}` (always 200, even during warm-up).
- [x] `POST /ask`: `AskRequest {question (1-4000 chars, stripped), patient?: PatientProfile}` → `AskResponse {answer, citations, plan, review, revisions, validation?, draft?}`. The patient is appended to the question as JSON (`null = unknown`); `validation`/`draft` come from the latest `validate_prescription`/`write_prescription` artifact (for UI badges). Agent failure → `502` with a generic message (details only in the server log); bad input → `422`.
- [x] `POST /ask/stream` (`fastapi.sse.EventSourceResponse`, sync generator run in a threadpool, 15 s `: ping` keep-alives): `plan {steps}` → `tool_call {calls:[{name,args}]}` → `tool_result {name,status,source_ids,verdict}` → `review {verdict,unsupported_claims,ambiguities,feedback,revising}` (per critic pass) → `final` (AskResponse) or `error {message}`. Uses `graph.stream(stream_mode=["updates","values"])`.
- [x] Lifespan starts index warm-up in a background thread; `retrieval.get_index()` is now a locked singleton (`index_ready()`), so requests during warm-up wait for the one build. Dev CORS for `http://localhost:3000`. Static mount of `frontend/out` at `/` only if the directory exists (verify in Steps 6/7).
- [x] `PatientProfile` lists bounded (≤20 items, ≤200 chars, no blanks): each current medication adds 2 retrievals per prescribed drug. The UI must drop empty entries.
- [x] `tests/test_api.py` (real graph + tools on the fake LLM/index: health, cited answer + patient passthrough, 422 cases, 502 without details, SSE event order + validation verdict, SSE error event). Live server check: `/ask` eval Q4 with patient → 22 s; stream eval Q3 → 54 s; validate sertraline + warfarin → 85 s, `approved_with_warnings`.
- [x] Lint, test, `/ponytail-review` (fixed: unbounded patient lists at the trust boundary), commit.
- Run locally: `uv run uvicorn pharma_assist.api:app --port 8000`.

### Step 6 — Next.js Frontend (`frontend/`) *(DONE)*
- [x] `create-next-app@16.4.6` (App Router, TypeScript, Tailwind 4, ESLint, `--empty`); all npm deps pinned exactly + `package-lock.json`; `output: "export"` → `frontend/out/` (mounted by FastAPI at `/`).
- [x] One client page, tabs `Ask · Validate · Write` (ARIA tablist, arrow keys). Every tab goes through the agent via `POST /ask/stream` (`lib/api.ts`: SSE parsed from `fetch`, 422 details shown per field, abort/cancel). Validate/Write build a question from the prescription rows / description; the shared `PatientForm` (empty = unknown, blank list entries dropped) is sent as `patient`, and the Ask tab says when it is included.
- [x] Live trace (plan, tool calls with args, tool results with verdict badges, critic passes), severity-colored validation card, draft table, answer rendered by `components/Markdown.tsx` (headings, lists, tables, bold/italic; `[n]` → button that opens + scrolls to the cited passage; no HTML injection), cited passages with "Open original label".
- [x] Verified: `npm run lint`, `tsc`, `npm run build`, `npm audit --omit=dev` (0). Headless Chrome (puppeteer-core in the scratchpad only) against `uvicorn` serving `out/`: Ask eval Q4 (trace streams, citation [1] opens its passage, disclaimer shown), Validate metformin eGFR 25 → Rejected/CRITICAL, Write T2D → metformin draft + Needs more information (136 s), 390 px width without horizontal scroll, no console errors.
- [x] `/ponytail-review` (fixed: patient details from another tab were sent silently with Ask questions; favicon 404), commit.
- Note: no JS unit-test runner (would be a new dependency); the markdown renderer is covered by the browser run only. Latency: Validate/Write take 1-2+ min (agent adds its own searches and critic revisions) — tune in Step 8 if needed.

### Step 7 — Single-Container Docker Build (`Dockerfile`) *(DONE)*
- [x] Multi-stage `Dockerfile`: `node:22.23.5-alpine3.24` (`npm ci` + `next build` → `/web/out`) → `python:3.12.16-slim-trixie` + `ghcr.io/astral-sh/uv:0.11.29` (`uv sync --frozen --no-dev --no-install-project`, `PYTHONPATH=/app/backend`). The repo layout is kept under `/app`, so `config.PROJECT_ROOT` still finds `corpus/`, `.cache/` and `frontend/out` (no path settings needed).
- [x] Non-root user `app` (uid 1001) that can write only `/app/.cache`; `HEALTHCHECK` on `/health`; one uvicorn worker (in-memory index). No `.env`, `.agents/`, `tests/` or embedding cache in the image (`.dockerignore`). The cache is built at container start in the background (~15-25 s; `/health` is 200 meanwhile), so no API key is needed at build time.
- [x] Verified with the exact grader command on Docker 28.5.1 and the real (quoted, `OPENAI_BASE_UR`-typo) `.env`: build ~67 s, image 748 MB; `/health` 200 after ~3 s, index ready ~14 s later; `POST /ask {"question": ...}` (eval Q1) → 200 in 10 s citing `dailymed-warfarin.md`; UI at `/`; the headless-Chrome run (Ask Q4 + Validate) passes with no console errors; container `healthy`; `docker stop` exits in ~1 s.
- [x] `.env.example` updated (dropped the removed `MAX_REVISIONS`; default model `gpt-5.6-terra`, matching the user's change to `config.py`). README: run/develop commands.
- [x] Lint, test, `/ponytail-review` (no Must fix; removed a `useradd --system` uid warning), commit.

### Step 8 — Evaluation Harness, Whole-Repo Audit, Docs & Presentation *(NEXT)*
- [ ] Add `tests/eval/run_eval.py` (runs the 4 public questions + prescription scenarios, verifies expected source files and disclaimer, writes `eval_report.md`).
- [ ] Run `/ponytail-audit` across the repository and fix any **Must fix** items.
- [ ] Finalize `README.md`, `docs/PRESENTATION.md` (10-minute walkthrough guide), and the `walkthrough.md` artifact.

