from typing import get_args

import pytest
from pydantic import ValidationError

from pharma_assist import tools
from pharma_assist.retrieval import SECTIONS
from pharma_assist.schemas import (
    DraftPrescription,
    Issue,
    PatientProfile,
    PrescriptionItem,
    Section,
)


class FakeLLM:
    """Stands in for ChatOpenAI: returns queued structured outputs and records the prompts."""

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return self.outputs.pop(0)  # IndexError = an unexpected LLM call


@pytest.fixture
def fake_llm(monkeypatch, fake_index):
    monkeypatch.setattr(tools, "get_index", lambda: fake_index)

    def install(*outputs):
        llm = FakeLLM(*outputs)
        monkeypatch.setattr(tools, "get_chat_model", lambda: llm)
        return llm

    return install


def call(tool, args):
    """Invoke like the agent's ToolNode does, so content *and* artifact come back."""
    return tool.invoke({"type": "tool_call", "id": "t1", "name": tool.name, "args": args})


def item(drug, dose="500 mg"):
    return PrescriptionItem(drug=drug, dose=dose, frequency="twice daily")


def test_enums_match_corpus(chunks):
    assert set(tools.CORPUS_DRUGS) == {c.drug for c in chunks if c.drug}
    assert set(get_args(Section)) == set(SECTIONS)


@pytest.mark.parametrize(
    ("issues", "verdict"),
    [
        ([], "approved"),
        ([("minor", "other")], "approved_with_warnings"),
        ([("major", "interaction")], "approved_with_warnings"),
        ([("major", "missing_info"), ("minor", "other")], "needs_more_info"),
        ([("major", "out_of_corpus")], "needs_more_info"),
        ([("critical", "contraindication"), ("major", "missing_info")], "rejected"),
    ],
)
def test_compute_verdict_fails_closed(issues, verdict):
    parsed = [Issue(severity=s, category=c, message="x") for s, c in issues]
    assert tools.compute_verdict(parsed) == verdict


def test_build_context_returns_sources_as_artifact(fake_llm):
    fake_llm()
    msg = call(build := tools.build_context, {"query": "contraindications", "drugs": ["warfarin"], "k": 3})
    assert len(msg.artifact) == 3 and all(s.drug == "warfarin" for s in msg.artifact)
    assert all(f"[{s.id}]" in msg.content for s in msg.artifact)  # the LLM sees the citation keys

    empty = call(build, {"query": "  "})
    assert empty.artifact == [] and "No passages found" in empty.content


def test_out_of_corpus_only_prescription_never_calls_llm(fake_llm):
    fake_llm()  # no queued outputs: any LLM call fails the test
    report = tools.run_validation([item("lisinopril", "10 mg")], PatientProfile()).report
    assert report.verdict == "needs_more_info"
    assert [i.category for i in report.issues] == ["out_of_corpus"]


def test_empty_prescription_is_never_approved(fake_llm):
    fake_llm()
    assert tools.run_validation([], PatientProfile()).report.verdict == "needs_more_info"
    with pytest.raises(ValidationError):
        PrescriptionItem(drug="  ", dose="5 mg", frequency="daily")


def test_documented_allergy_rejects_even_if_llm_misses_it(fake_llm):
    fake_llm(tools._Review(issues=[], summary="Looks fine."))
    report = tools.run_validation(
        [item("Amoxicillin")], PatientProfile(allergies=["amoxicillin (hives)"])
    ).report
    assert report.verdict == "rejected"
    assert report.issues[0].category == "allergy"


def test_validation_keeps_only_retrieved_citations_and_checks_interactions_both_ways(fake_llm, chunks):
    contra_id = next(c.id for c in chunks if c.drug == "sertraline" and c.section == "contraindications")
    llm = fake_llm(
        tools._Review(
            issues=[
                Issue(
                    severity="major",
                    category="interaction",
                    drug="sertraline",
                    message="Bleeding risk with warfarin.",
                    source_ids=[f"[{contra_id}]", "made-up.md#99"],
                )
            ],
            summary="Monitor INR.",
        )
    )
    result = tools.run_validation(
        [item("Sertraline", "50 mg")], PatientProfile(sex="male", current_medications=["Warfarin"])
    )

    assert result.report.issues[0].source_ids == [contra_id]  # brackets stripped, invented id dropped
    assert result.report.verdict == "approved_with_warnings"
    # Passages come from both labels: sertraline's and the current medication's (reverse direction).
    assert {s.drug for s in result.sources} == {"sertraline", "warfarin"}
    assert any(s.drug == "warfarin" and s.section == "interactions" for s in result.sources)
    prompt = llm.calls[0][1][1]
    assert all(f"[{s.id}]" in prompt for s in result.sources)


def test_write_prescription_is_validated_automatically(fake_llm):
    llm = fake_llm(
        DraftPrescription(items=[item("metformin")], rationale="Label start dose.", source_ids=["bogus#1"]),
        tools._Review(
            issues=[Issue(severity="major", category="missing_info", message="eGFR unknown.")],
            summary="Need eGFR.",
        ),
    )
    msg = call(tools.write_prescription, {"description": "type 2 diabetes"})

    assert len(llm.calls) == 2  # draft, then validation
    assert msg.artifact.draft.source_ids == []
    assert msg.artifact.validation.verdict == "needs_more_info"
    assert "Automatic validation" in msg.content and "metformin 500 mg" in msg.content


def test_write_prescription_without_items_skips_validation(fake_llm):
    llm = fake_llm(DraftPrescription(items=[], rationale="No corpus drug treats this."))
    result = tools.run_draft("treatment for glaucoma")
    assert result.validation is None and len(llm.calls) == 1


# --- live: real LLM + embeddings (`uv run pytest -m live`) ---


@pytest.mark.live
def test_live_metformin_egfr_25_is_rejected_with_cited_label():
    msg = call(
        tools.validate_prescription,
        {
            "prescription": [{"drug": "metformin", "dose": "500 mg", "frequency": "twice daily"}],
            "patient": {"age": 67, "egfr": 25},
        },
    )
    report = msg.artifact.report
    assert report.verdict == "rejected"
    critical = [i for i in report.issues if i.severity == "critical"]
    assert any(s.startswith("dailymed-metformin.md#") for i in critical for s in i.source_ids)


@pytest.mark.live
def test_live_sertraline_with_warfarin_flags_interaction():
    msg = call(
        tools.validate_prescription,
        {
            "prescription": [{"drug": "sertraline", "dose": "50 mg", "frequency": "once daily"}],
            "patient": {"age": 58, "sex": "male", "current_medications": ["warfarin"]},
        },
    )
    interactions = [i for i in msg.artifact.report.issues if i.category == "interaction"]
    assert interactions and all(i.severity in ("major", "critical") for i in interactions)
    assert any(
        s.split(".md#")[0] in ("dailymed-sertraline", "dailymed-warfarin") for s in interactions[0].source_ids
    )


@pytest.mark.live
def test_live_write_prescription_for_type_2_diabetes():
    msg = call(
        tools.write_prescription,
        {"description": "first-line oral therapy for type 2 diabetes", "patient": {"age": 60, "egfr": 75}},
    )
    assert [i.drug.lower() for i in msg.artifact.draft.items] == ["metformin"]
    assert msg.artifact.validation is not None
