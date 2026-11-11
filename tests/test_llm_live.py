"""Live checks against the real OpenAI-compatible endpoint. Run with `uv run pytest -m live`."""

import pytest
from langchain_core.tools import tool
from pydantic import BaseModel

from pharma_assist.llm import get_chat_model, get_embeddings

pytestmark = pytest.mark.live


class Answer(BaseModel):
    drug: str
    is_anticoagulant: bool


@tool
def lookup_drug(name: str) -> str:
    """Look up a drug label by drug name."""
    return name


def test_chat():
    assert get_chat_model().invoke("Reply with exactly: pong").content.strip()


def test_embeddings():
    vectors = get_embeddings().embed_documents(["warfarin", "metformin"])
    assert len(vectors) == 2 and len(vectors[0]) > 0


def test_tool_call():
    msg = get_chat_model().bind_tools([lookup_drug]).invoke("Use the tool to look up warfarin.")
    assert msg.tool_calls and msg.tool_calls[0]["name"] == "lookup_drug"


def test_structured_output():
    # langchain-openai defaults to method="json_schema"; the proxy model supports it (probed in Step 1).
    out = get_chat_model().with_structured_output(Answer).invoke("Is warfarin an anticoagulant?")
    assert isinstance(out, Answer) and out.is_anticoagulant
