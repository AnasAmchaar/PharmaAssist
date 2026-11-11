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
                       critic --(revise & revisions < max_revisions)--> agent
                         |
              (approve or max reached)
                         v
                     finalizer -> END
   ```
2. **Deterministic Citations (`content_and_artifact`):**
   - Tools return `(text_for_llm, list[Source])` using LangChain's `response_format="content_and_artifact"`.
   - `AgentState.sources` merges artifacts by chunk ID so citations in the final answer are mapped from actually retrieved corpus chunks (`[S1]`, `[S2]` → renumbered `[1]`, `[2]`), never hallucinated.
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
│   ├── schemas.py            # PatientProfile, PrescriptionItem, ValidationReport, Plan, Critique, Source, Ask*
│   ├── retrieval.py          # Markdown section chunker + HybridIndex (cosine + BM25 + RRF) + .cache
│   ├── tools.py              # build_context, validate_prescription, write_prescription
│   ├── agent.py              # LangGraph StateGraph (planner, agent, tools, critic, finalizer)
│   └── api.py                # FastAPI (/health, /ask, /ask/stream SSE, static mount)
├── frontend/                 # Next.js (App Router, TypeScript, Tailwind, output: "export")
└── tests/
    ├── test_config.py
    ├── test_retrieval.py
    ├── test_tools.py
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

### Step 2 — Hybrid In-Memory Retrieval (`retrieval.py`) *(NEXT)*
- [ ] Implement markdown heading-aware chunker with canonical section mapping across DailyMed (Rx + OTC) and MedlinePlus formats.
- [ ] Implement `HybridIndex` (numpy cosine + `BM25Okapi` + RRF + `drugs`/`sections` pre-filtering + `.cache/` numpy persistence).
- [ ] Add `tests/test_retrieval.py` (unit tests with fake embeddings + live sanity check that `"warfarin contraindications"` ranks `dailymed-warfarin.md › 4 CONTRAINDICATIONS` first).
- [ ] Lint, test, `/ponytail-review`, commit, wait for user approval.

### Step 3 — Schemas & Agent Tools (`schemas.py`, `tools.py`)
- [ ] Define Pydantic models in `schemas.py` (`PatientProfile`, `PrescriptionItem`, `Issue`, `ValidationReport`, `DraftPrescription`, `Source`, `Plan`, `Critique`, `AskRequest`, `AskResponse`).
- [ ] Implement `build_context(query, drugs=None, sections=None, k=6)` with `response_format="content_and_artifact"`.
- [ ] Implement `validate_prescription(prescription, patient)`: out-of-corpus check at trust boundary + targeted multi-query retrieval (contraindications, dosage, warnings, interactions, renal/pregnancy/age, cross-drug interactions with `current_medications`) + grounded structured LLM evaluation.
- [ ] Implement `write_prescription(description, patient=None)`: retrieve indications/dosage → structured draft (corpus drugs only) → auto-call `validate_prescription` → return draft + validation report.
- [ ] Add `tests/test_tools.py` (unit tests with fake LLM + live check on metformin eGFR 25 and warfarin + sertraline).
- [ ] Lint, test, `/ponytail-review`, commit, wait for user approval.

### Step 4 — LangGraph Agent (`agent.py`)
- [ ] Build `StateGraph(AgentState)` with nodes: `planner`, `agent` (ReAct with `bind_tools`), `tools` (`ToolNode`), `critic`, `finalizer`.
- [ ] Enforce loop guards (`max_revisions`, `recursion_limit`), deterministic `[S#]` → `[1..n]` citation renumbering, critic caveats preservation, and mandatory medical disclaimer.
- [ ] Verify against all 4 public evaluation questions.
- [ ] Lint, test, `/ponytail-review`, commit, wait for user approval.

### Step 5 — FastAPI Service (`api.py`)
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

