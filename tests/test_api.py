import base64
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from pharma_assist import tools
from pharma_assist.api import app
from pharma_assist.schemas import Critique, Plan

# Smallest valid PNG (1x1), as the UI would send it.
PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9a"
    "wAAAABJRU5ErkJggg=="
)
client = TestClient(app)  # no `with`: the lifespan (real index warm-up) does not run in unit tests


def sse_events(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if not line.startswith(":"))
        if "event" in fields:
            events.append((fields["event"], json.loads(fields["data"])))
    return events


def validate_flow():
    """Plan -> validate_prescription (its own LLM review) -> answer -> critic approves."""
    call = {
        "name": "validate_prescription",
        "args": {
            "prescription": [{"drug": "metformin", "dose": "500 mg", "frequency": "twice daily"}],
            "patient": {"age": 60, "egfr": 25},
        },
        "id": "c1",
    }
    return (
        Plan(steps=["Validate metformin for this patient"]),
        AIMessage("", tool_calls=[call]),
        tools._Review(issues=[], summary="ok"),
        AIMessage("Checked against the label."),
        Critique(verdict="approve"),
    )


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and isinstance(r.json()["index_ready"], bool)


def test_ask_returns_cited_answer_and_passes_patient(fake_llm, chunks):
    cid = next(c.id for c in chunks if c.drug == "warfarin" and c.section == "contraindications")
    args = {"query": "contraindications", "drugs": ["warfarin"]}
    llm = fake_llm(
        Plan(steps=["Find warfarin contraindications"]),
        AIMessage("", tool_calls=[{"name": "build_context", "args": args, "id": "c1"}]),
        AIMessage(f"Contraindicated in pregnancy [{cid}]."),
        Critique(verdict="approve"),
    )
    payload = {"question": "  Warfarin contraindications?  ", "patient": {"pregnant": True}}
    r = client.post("/ask", json=payload)

    assert r.status_code == 200
    body = r.json()
    assert body["answer"].startswith("Contraindicated in pregnancy [1].")
    assert "not medical advice" in body["answer"]
    assert [c["id"] for c in body["citations"]] == [cid]
    assert body["plan"] == ["Find warfarin contraindications"] and body["review"]["verdict"] == "approve"
    assert body["validation"] is None and body["draft"] is None
    question = llm.calls[0][1].text  # what the planner saw: stripped question + patient JSON
    assert question.startswith("Warfarin contraindications?\n\nPatient profile")
    assert '"pregnant":true' in question


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": "   "},
        {"question": "x" * 4001},
        {"question": "x", "patient": {"egfr": -1}},
        {"question": "x", "patient": {"current_medications": ["warfarin"] * 21}},  # bounds retrieval fan-out
        {"question": "x", "images": ["data:image/svg+xml;base64,PHN2Zz4="]},  # not a vision format
        {"question": "x", "images": ["data:image/png;base64,not base64!"]},
        {"question": "x", "images": [PNG] * 4},  # at most 3
    ],
)
def test_ask_rejects_invalid_input(payload):
    assert client.post("/ask", json=payload).status_code == 422


def test_ask_agent_failure_is_502_without_details(fake_llm):
    fake_llm()  # no queued outputs: the planner's LLM call fails
    r = client.post("/ask", json={"question": "Warfarin?"})
    assert r.status_code == 502 and "IndexError" not in r.text


def test_images_reach_planner_agent_and_critic(fake_llm):
    args = {"query": "metformin dose", "drugs": ["metformin"]}
    llm = fake_llm(
        Plan(steps=["Read the prescription in the image"]),
        AIMessage("", tool_calls=[{"name": "build_context", "args": args, "id": "c1"}]),
        AIMessage("The image shows metformin 500 mg."),
        Critique(verdict="approve"),
    )
    r = client.post("/ask", json={"question": "Is this prescription OK?", "images": [PNG]})
    assert r.status_code == 200

    def image_urls(messages):
        return [
            block["image_url"]["url"]
            for m in messages
            if isinstance(m.content, list)
            for block in m.content
            if block.get("type") == "image_url"
        ]

    planner, agent_turn, critic = llm.calls[0], llm.calls[1], llm.calls[-1]
    assert image_urls(planner) == image_urls(agent_turn) == image_urls(critic) == [PNG]


def test_stream_emits_trace_then_final(fake_llm):
    fake_llm(*validate_flow())
    r = client.post("/ask/stream", json={"question": "Can this patient take metformin 500 mg bid?"})

    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    events = sse_events(r.text)
    assert [e for e, _ in events] == ["plan", "tool_call", "tool_result", "review", "final"]
    _, tool_result = events[2]
    assert tool_result["name"] == "validate_prescription" and tool_result["status"] == "success"
    assert tool_result["verdict"] == "approved" and tool_result["source_ids"]
    final = events[-1][1]
    assert final["validation"]["verdict"] == "approved" and "not medical advice" in final["answer"]


def test_stream_reports_errors_as_event(fake_llm):
    fake_llm()
    events = sse_events(client.post("/ask/stream", json={"question": "Warfarin?"}).text)
    assert [e for e, _ in events] == ["error"]


# --- live: real model reads an image (`uv run pytest -m live`) ---


@pytest.mark.live
def test_live_prescription_photo_is_read_and_validated():
    photo = (Path(__file__).parent / "fixtures" / "rx-metformin.png").read_bytes()  # metformin 500 mg bid
    r = client.post(
        "/ask",
        json={
            "question": "Is this prescription safe for my patient?",
            "patient": {"age": 67, "egfr": 25, "hepatic_impairment": "none"},
            "images": ["data:image/png;base64," + base64.b64encode(photo).decode()],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["validation"]["verdict"] == "rejected"  # metformin read from the image, eGFR 25 < 30
    assert "dailymed-metformin.md" in {c["file"] for c in body["citations"]}
