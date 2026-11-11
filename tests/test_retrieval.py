import numpy as np
import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding, Embeddings

from conftest import EVAL_QUESTIONS
from pharma_assist.retrieval import (
    MAX_WORDS,
    SECTIONS,
    Chunk,
    HybridIndex,
    _rrf,
    canonical_section,
    chunk_markdown,
    get_index,
    load_corpus,
)


@pytest.mark.parametrize(
    ("heading", "section"),
    [
        ("4 CONTRAINDICATIONS", "contraindications"),
        ("10 OVERDOSAGE", "overdose"),  # must not fall into "dosage"
        ("2 DOSAGE AND ADMINISTRATION", "dosage"),
        ("WARNING: BLEEDING RISK", "warnings"),
        ("Uses", "indications"),  # DailyMed OTC
        ("Directions", "dosage"),
        ("Why is this medication prescribed?", "indications"),  # MedlinePlus
        ("What side effects can this medication cause?", "adverse_reactions"),
        ("What special precautions should I follow?", "warnings"),
        ("In case of emergency/overdose", "overdose"),
        ("8 USE IN SPECIFIC POPULATIONS", "specific_populations"),
        ("Nursing Mothers", "specific_populations"),
        ("12 CLINICAL PHARMACOLOGY", "pharmacology"),
        ("Brand names", "other"),
    ],
)
def test_canonical_section(heading, section):
    assert canonical_section(heading) == section


def test_chunk_markdown_heading_path_and_metadata():
    md = (
        "# Foo (DailyMed label)\n\nSource: https://example.com/foo\n\n"
        "## 4 CONTRAINDICATIONS\n\n- Bleeding.\n\n"
        "## 5 WARNINGS AND PRECAUTIONS\n\n### 5.1 Hemorrhage\n\nMay cause bleeding.\n"
    )
    out = chunk_markdown("dailymed-foo.md", md)

    assert [(c.heading, c.section) for c in out] == [
        ("Foo (DailyMed label) › 4 CONTRAINDICATIONS", "contraindications"),
        ("Foo (DailyMed label) › 5 WARNINGS AND PRECAUTIONS › 5.1 Hemorrhage", "warnings"),
    ]
    assert {(c.drug, c.url) for c in out} == {("foo", "https://example.com/foo")}
    assert all("Source:" not in c.text for c in out)


def test_long_single_line_section_is_split():
    sentence = "Warfarin increases bleeding risk in patients. "
    out = chunk_markdown("dailymed-foo.md", "# Foo\n\n## 6 ADVERSE REACTIONS\n\n" + sentence * 200)
    assert len(out) > 1
    assert all(len(c.text.split()) <= MAX_WORDS for c in out)
    assert " ".join(c.text for c in out).split() == (sentence * 200).split()  # nothing lost


def test_corpus_chunks(chunks):
    assert len({c.file for c in chunks}) == 21
    assert len({c.drug for c in chunks if c.drug}) == 10
    assert len({c.id for c in chunks}) == len(chunks)
    assert {c.section for c in chunks} <= set(SECTIONS)
    assert all(c.text.strip() and len(c.text.split()) <= MAX_WORDS for c in chunks)
    # Every Rx label's contraindications section is tagged, e.g. the metformin eGFR threshold.
    metformin = [c for c in chunks if c.file == "dailymed-metformin.md" and c.section == "contraindications"]
    assert any("eGFR below 30" in c.text for c in metformin)


def test_search_filters(fake_index):
    hits = fake_index.search("renal threshold", k=5, drugs=["Metformin "], sections=["contraindications"])
    assert hits and all(c.drug == "metformin" and c.section == "contraindications" for c, _ in hits)
    assert fake_index.search("anything", drugs=["not-in-corpus"]) == []
    assert fake_index.search("   ") == []


class KeywordEmbeddings(Embeddings):
    """Bag-of-keywords vectors so dense ranking is predictable in tests."""

    vocab = ("bleeding", "renal", "liver")

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text):
        return [text.lower().count(w) + 0.01 for w in self.vocab]


def test_fusion_maps_filtered_candidates_back_to_chunks(tmp_path):
    def chunk(i, drug, text):
        return Chunk(f"f#{i}", f"dailymed-{drug}.md", drug, None, drug, "warnings", text)

    chunks = [
        chunk(0, "a", "renal renal threshold"),  # best match overall, but filtered out below
        chunk(1, "b", "bleeding risk"),
        chunk(2, "b", "renal bleeding"),
        chunk(3, "b", "liver enzymes"),
    ]
    index = HybridIndex(chunks, KeywordEmbeddings(), tmp_path)

    assert index.search("renal", k=1)[0][0].id == "f#0"
    hits = index.search("renal", k=3, drugs=["b"])
    assert hits[0][0].id == "f#2"  # dense + BM25 agree
    assert [s for _, s in hits] == sorted((s for _, s in hits), reverse=True)


def test_rrf_ignores_zero_bm25_scores():
    fused = _rrf(np.array([0.0, 3.0, 1.0]), positive_only=True)
    assert fused[0] == 0  # no shared query term → no contribution, whatever its corpus position
    assert fused[1] == pytest.approx(1 / 61) and fused[2] == pytest.approx(1 / 62)


def test_embedding_cache_is_reused(chunks, tmp_path):
    HybridIndex(chunks, DeterministicFakeEmbedding(size=32), tmp_path)
    assert len(list(tmp_path.glob("emb-*.npy"))) == 1

    class NoEmbed(DeterministicFakeEmbedding):
        def embed_documents(self, texts):
            raise AssertionError("cache miss: corpus was re-embedded")

    NoEmbed(size=32).embed_query("ok")  # queries still embed
    HybridIndex(chunks, NoEmbed(size=32), tmp_path)  # documents come from disk


def test_missing_corpus_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"No \.md files"):
        load_corpus(tmp_path)


# --- live: real embeddings through the proxy (`uv run pytest -m live`) ---


@pytest.mark.live
def test_live_top_hit_is_warfarin_contraindications():
    chunk, _ = get_index().search("warfarin contraindications", k=1)[0]
    assert (chunk.file, chunk.section) == ("dailymed-warfarin.md", "contraindications")


@pytest.mark.live
@pytest.mark.parametrize(("question", "expected"), EVAL_QUESTIONS)
def test_live_eval_questions_retrieve_expected_files(question, expected):
    # Unfiltered search over the whole corpus; the agent will additionally filter by drug/section.
    files = {c.file for c, _ in get_index().search(question, k=8)}
    assert expected <= files
