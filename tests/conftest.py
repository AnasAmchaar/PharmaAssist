import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from pharma_assist import agent, tools
from pharma_assist.config import PROJECT_ROOT
from pharma_assist.retrieval import HybridIndex, load_corpus

# The 4 public evaluation questions and the corpus files each answer must draw on.
EVAL_QUESTIONS = [
    ("What are the main contraindications for warfarin?", {"dailymed-warfarin.md"}),
    (
        "Compare the contraindications of warfarin and apixaban. "
        "What conditions are shared and which are unique to each drug?",
        {"dailymed-warfarin.md", "dailymed-apixaban.md"},
    ),
    (
        "A patient currently on warfarin is prescribed sertraline. "
        "What is the risk of bleeding and what monitoring is recommended?",
        {"dailymed-warfarin.md", "dailymed-sertraline.md"},
    ),
    (
        "A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin "
        "contraindicated at this level of renal function, and what is the threshold?",
        {"dailymed-metformin.md"},
    ),
]


@pytest.fixture(scope="session")
def chunks():
    return load_corpus(PROJECT_ROOT / "corpus")


@pytest.fixture(scope="session")
def fake_index(chunks, tmp_path_factory):
    """Real corpus + random (deterministic) embeddings: no network, filters and BM25 still real."""
    return HybridIndex(chunks, DeterministicFakeEmbedding(size=32), tmp_path_factory.mktemp("cache"))


class FakeLLM:
    """Stands in for ChatOpenAI: returns queued outputs in order and records each call."""

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []
        self.tool_choices = []

    def with_structured_output(self, schema):
        return self

    def bind_tools(self, tools, tool_choice=None):
        self.tool_choices.append(tool_choice)
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return self.outputs.pop(0)  # IndexError = an unexpected LLM call


@pytest.fixture
def fake_llm(monkeypatch, fake_index):
    """`fake_llm(*outputs)` installs a FakeLLM for tools and agent; retrieval uses the fake index."""
    monkeypatch.setattr(tools, "get_index", lambda: fake_index)

    def install(*outputs):
        llm = FakeLLM(*outputs)
        monkeypatch.setattr(tools, "get_chat_model", lambda: llm)
        monkeypatch.setattr(agent, "get_chat_model", lambda: llm)
        return llm

    return install
