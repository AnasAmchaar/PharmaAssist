"""HTTP API: GET /health, POST /ask, POST /ask/stream (SSE agent trace), and the static Next.js UI at /.

Run: `uv run uvicorn pharma_assist.api:app --port 8000`.
"""

import logging
import threading
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import ToolMessage

from pharma_assist import agent
from pharma_assist.config import PROJECT_ROOT
from pharma_assist.retrieval import get_index, index_ready
from pharma_assist.schemas import AskRequest, AskResponse, DraftResult, ValidationResult

log = logging.getLogger(__name__)
STATIC_DIR = PROJECT_ROOT / "frontend" / "out"  # Next.js static export (Step 6)


def _warm_index() -> None:
    try:
        get_index()
    except Exception:  # the first /ask retries the build and reports the error to the caller
        log.exception("Index warm-up failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background thread so /health answers at once; requests during warm-up wait on the index lock.
    threading.Thread(target=_warm_index, name="index-warmup", daemon=True).start()
    yield


app = FastAPI(title="PharmaAssist", version="0.1.0", lifespan=lifespan)
# Dev only: the Next.js dev server (`npm run dev`) calls the API cross-origin. In the container the UI is
# served from this same origin, so CORS is not involved.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _agent_input(req: AskRequest) -> dict:
    question = req.question
    if req.patient is not None:
        question += f"\n\nPatient profile (null = unknown): {req.patient.model_dump_json()}"
    return {"question": question, "images": req.images}


def to_response(state: agent.AgentState) -> AskResponse:
    validation = draft = None
    for m in state["messages"]:  # latest structured tool result wins
        art = m.artifact if isinstance(m, ToolMessage) else None
        if isinstance(art, ValidationResult):
            validation = art.report
        elif isinstance(art, DraftResult):
            draft, validation = art.draft, art.validation
    return AskResponse(
        answer=state["answer"],
        citations=state["citations"],
        plan=state["plan"],
        review=state.get("critique"),
        revisions=state.get("revisions", 0),
        validation=validation,
        draft=draft,
    )


def _tool_result(m: ToolMessage) -> dict:
    art = m.artifact  # list[Source] | ValidationResult | DraftResult | None (tool error)
    sources = art if isinstance(art, list) else getattr(art, "sources", [])
    report = art.report if isinstance(art, ValidationResult) else getattr(art, "validation", None)
    return {
        "name": m.name,
        "status": m.status,
        "source_ids": [s.id for s in sources],
        "verdict": report.verdict if report else None,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "index_ready": index_ready()}


@app.post("/ask")
def ask(req: AskRequest) -> AskResponse:
    try:
        state = agent.graph.invoke(_agent_input(req))
    except Exception as e:
        log.exception("Agent run failed")
        raise HTTPException(502, "The agent could not complete this request. Please try again.") from e
    return to_response(state)


@app.post("/ask/stream", response_class=EventSourceResponse)
def ask_stream(req: AskRequest) -> Iterator[ServerSentEvent]:
    """Agent trace as it happens: plan, tool_call, tool_result, review (per revision), then final or error."""
    state = None
    try:
        for mode, chunk in agent.graph.stream(_agent_input(req), stream_mode=["updates", "values"]):
            if mode == "values":
                state = chunk
                continue
            for node, update in chunk.items():
                if node == "planner":
                    yield ServerSentEvent(event="plan", data={"steps": update["plan"]})
                elif node == "agent" and (calls := update["messages"][-1].tool_calls):
                    calls = [{"name": c["name"], "args": c["args"]} for c in calls]
                    yield ServerSentEvent(event="tool_call", data={"calls": calls})
                elif node == "tools":
                    for m in update["messages"]:
                        yield ServerSentEvent(event="tool_result", data=_tool_result(m))
                elif node == "critic":
                    review = update["critique"].model_dump()
                    yield ServerSentEvent(event="review", data={**review, "revising": "messages" in update})
        yield ServerSentEvent(event="final", data=to_response(state).model_dump())
    except Exception:
        log.exception("Agent stream failed")
        yield ServerSentEvent(event="error", data={"message": "The agent could not complete this request."})


if STATIC_DIR.is_dir():  # mounted last so API routes take precedence
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
