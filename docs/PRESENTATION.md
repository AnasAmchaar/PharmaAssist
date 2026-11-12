# PharmaAssist: 10-minute walkthrough

A script for presenting the project: what to show, in what order, and what to say. Times are targets.

## Before you start (5 min, off the clock)

```bash
docker build -t agent . && docker run -p 8000:8000 --env-file .env agent
```

- Wait until `curl localhost:8000/health` shows `"index_ready": true` (~15-25 s).
- Open <http://localhost:8000> and run one question once, so the first demo is not a cold start.
- Have `README.md`, `backend/pharma_assist/agent.py`, `tools.py` and `docs/eval_report.md` open in the editor.

## 1. The problem and the result (1 min)

- An agentic research assistant over 21 drug-label files (10 drugs, FDA DailyMed + MedlinePlus).
- It must plan, retrieve, choose its own tools, critique its draft against the sources, and answer with
  citations and a disclaimer.
- Result: one Docker command; `/health`, `/ask` and a Next.js UI; all 4 public questions plus 5 prescription
  scenarios pass the evaluation harness (`docs/eval_report.md`).

## 2. Live demo: a plain question (2 min)

- **Ask** tab → click the example *"Compare the contraindications of warfarin and apixaban…"*.
- Point at the **agent trace** as it streams:
  - the **plan** (decomposition),
  - the **tool calls**: the model chose `build_context` with drug and section filters, once per drug,
  - the **critic** pass.
- In the answer: click a citation `[1]` → the exact label passage opens, with a link to the original label.
- Point out the **Sources** list (file + section) and the **disclaimer** at the bottom.

## 3. Live demo: prescription safety (2 min)

- **Validate** tab → *Example: metformin at eGFR 25* → Validate.
- Result: **Rejected**, with a CRITICAL contraindication citing `dailymed-metformin.md` (eGFR below 30).
- Say why it is trustworthy:
  - the **verdict is computed in code**, not by the model: critical → rejected; missing patient data →
    needs more info;
  - **unknown is not normal**: leave hepatic status empty and the verdict becomes *Needs more information*;
  - interactions are searched **in both directions** (example: sertraline with warfarin → warning cites
    both labels).
- Optional (1 min): **Write** tab → *Example: type 2 diabetes* → metformin 500 mg twice daily, validated
  automatically.

## 4. Architecture (2.5 min)

Show the graph in `README.md` / `agent.py`:

```
planner → agent ⇄ tools → critic ─(revise once)→ agent
                              └→ finalizer (renumber citations, sources list, disclaimer)
```

Three points to make:

1. **The agent picks the tools.** The three tools are bound with `bind_tools`; their descriptions and enum
   arguments (10 drugs, 10 section tags) steer the choice. No keyword routing.
2. **Citations cannot be invented.** Tools return the retrieved passages as artifacts
   (`content_and_artifact`). Citation keys are chunk ids; the finalizer keeps only ids that were really
   retrieved and renumbers them `[1]`, `[2]`.
3. **Retrieval is hybrid and local.** Heading-aware chunks with section tags; cosine similarity on
   embeddings + BM25 keywords, fused with Reciprocal Rank Fusion; filters by drug and section; embeddings
   cached on disk.

## 5. Quality and engineering (1.5 min)

- **Tests**: 55 unit tests with a fake LLM and fake embeddings (no network) cover the graph flow, citation
  renumbering, verdict rules, the API and the SSE stream. 16 live tests hit the real model.
- **Evaluation**: `tests/eval/run_eval.py` runs everything through `POST /ask` (in-process or against the
  container) and checks cited files, disclaimer and verdicts.
- **Lessons from real runs**:
  - The proxy rate-limited one big embeddings request → batched by 64.
  - The provided `.env` has `OPENAI_BASE_UR` (typo) and quoted values → both handled in config.
  - The critic's second rewrite rarely helped → limited to one; leftover doubts are shown as reviewer
    notes. Prescription answers went from ~2 min to ~1 min.
- **Container**: multi-stage build, non-root user, healthcheck, no secrets or caches in the image.

## 6. Limits and next steps (1 min)

- Latency of 1-1.5 min for prescription checks (several LLM calls). Next: cache retrieval per question, run
  the critic on a smaller model.
- Generic drug names only (no brand-name mapping); only the 10 corpus drugs can be validated.
- No auth or rate limiting: built for a local demo, not public hosting.
- The AI coding setup is in the repo: `AGENTS.md` (rules, plan, build log) and `.agents/` (skills).

## Likely questions

- **Why LangGraph and not a single ReAct loop?** The assignment needs explicit plan and review steps; a graph
  makes them real nodes with their own structured outputs, and the critic can send the draft back.
- **What if the model cites something wrong?** Unknown ids are dropped; the critic checks claim vs passage;
  what it cannot verify is shown as "Not verified against the sources".
- **What if patient data is missing?** Missing fields are unknown, and validation returns
  *needs_more_info* naming the field instead of approving.
- **Why not a vector database?** 528 chunks fit in memory; numpy + BM25 is exact, fast and dependency-light.
