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
│   ├── schemas.py            # CorpusDrug/Section enums, PatientProfile, PrescriptionItem, Issue, ValidationReport, Draft*, Source, Plan, Critique (+ Ask* in Step 5)
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
- [x] `schemas.py`: models used by the tools only (`Ask*` arrive in Step 5). `CorpusDrug` / `Section` enums are tested against the corpus.
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

### Step 5 — FastAPI Service (`api.py`) *(NEXT)*
- [ ] Implement `GET /health` (`200 {"status": "ok", "index_ready": bool}`), `POST /ask` (`AskRequest` → `AskResponse`), and `POST /ask/stream` (`fastapi.sse` events: `plan`, `tool_call`, `tool_result`, `review`, `final`, `error`).
- [ ] Lifespan index warm-up, dev CORS, static Next.js mount at `/`.
- [ ] Add `tests/test_api.py` (`TestClient` tests for `/health` and `/ask`).
- [ ] Lint, test, `/ponytail-review`, commit, wait for user approval.

### Step 6 — Next.js Frontend (`frontend/`)
- [ ] Scaffold Next.js App Router + TypeScript + Tailwind with `output: "export"`.
- [ ] Single page with tabs `Ask · Validate · Write`, structured `PatientProfile` form, example question chips, live SSE agent trace, severity-colored validation badges, and clickable citations.
- [ ] Verify `npm run build` and `npm run lint`.
- [ ] `/ponytail-review`, commit, wait for user approval.

### Step 7 — Single-Container Docker Build (`Dockerfile`)
- [ ] Write multi-stage `Dockerfile` (`node:22-alpine` → `python:3.12-slim` with `uv`).
- [ ] Verify exact grader command: `docker build -t agent . && docker run -p 8000:8000 --env-file .env agent`, test `GET /health`, `POST /ask`, and UI on `http://localhost:8000`.
- [ ] `/ponytail-review`, commit, wait for user approval.

### Step 8 — Evaluation Harness, Whole-Repo Audit, Docs & Presentation
- [ ] Add `tests/eval/run_eval.py` (runs the 4 public questions + prescription scenarios, verifies expected source files and disclaimer, writes `eval_report.md`).
- [ ] Run `/ponytail-audit` across the repository and fix any **Must fix** items.
- [ ] Finalize `README.md`, `docs/PRESENTATION.md` (10-minute walkthrough guide), and the `walkthrough.md` artifact.

