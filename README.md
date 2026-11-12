# PharmaAssist

Agentic pharmacology research assistant over a local corpus of FDA DailyMed labels and MedlinePlus
monographs (10 drugs). A LangGraph agent plans, retrieves passages, chooses among three tools
(`build_context`, `validate_prescription`, `write_prescription`), has a critic check every claim against
the retrieved passages, and answers with citations and a "not medical advice" disclaimer.

## Run (Docker)

```bash
cp .env.example .env   # set OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
docker build -t agent . && docker run -p 8000:8000 --env-file .env agent
```

- UI: <http://localhost:8000>
- `GET /health` → `{"status": "ok", "index_ready": bool}` (the embedding index builds in ~15-25 s after start)
- `POST /ask` with `{"question": "What are the main contraindications for warfarin?"}`
- `POST /ask/stream`: same request, Server-Sent Events trace (`plan`, `tool_call`, `tool_result`, `review`, `final`)

## Develop

```bash
uv sync
uv run uvicorn pharma_assist.api:app --port 8000   # API (+ UI from frontend/out if built)
cd frontend && npm ci && npm run dev               # UI with hot reload on http://localhost:3000
uv run ruff check backend tests && uv run pytest -q  # unit tests (no network)
uv run pytest -m live                               # live tests against the configured LLM endpoint
```

See `AGENTS.md` for the architecture, design decisions and step-by-step build log.
