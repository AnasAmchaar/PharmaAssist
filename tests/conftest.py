import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from pharma_assist.config import PROJECT_ROOT
from pharma_assist.retrieval import HybridIndex, load_corpus


@pytest.fixture(scope="session")
def chunks():
    return load_corpus(PROJECT_ROOT / "corpus")


@pytest.fixture(scope="session")
def fake_index(chunks, tmp_path_factory):
    """Real corpus + random (deterministic) embeddings: no network, filters and BM25 still real."""
    return HybridIndex(chunks, DeterministicFakeEmbedding(size=32), tmp_path_factory.mktemp("cache"))
