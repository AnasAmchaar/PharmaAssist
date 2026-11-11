import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from conftest import EVAL_QUESTIONS
from pharma_assist import agent
from pharma_assist.schemas import Critique, Plan, Source


def src(i, file="dailymed-warfarin.md"):
    return Source(id=f"{file}#{i}", file=file, heading="h", section="other", text="t")


def test_renumber_citations_orders_merges_and_drops_unknown_ids():
    sources = {s.id: s for s in (src(4), src(9), src(2, "dailymed-apixaban.md"))}
    text = (
        "Pregnancy [dailymed-warfarin.md#9]. Bleeding [dailymed-apixaban.md#2, dailymed-warfarin.md#9]. "
        "Invented [made-up.md#1]. Again [dailymed-warfarin.md#9; dailymed-warfarin.md#4]. Keep [sic]."
    )
    body, cited = agent.renumber_citations(text, sources)
    assert body == "Pregnancy [1]. Bleeding [2][1]. Invented. Again [1][3]. Keep [sic]."
    assert [s.id for s in cited] == [
        "dailymed-warfarin.md#9",
        "dailymed-apixaban.md#2",
        "dailymed-warfarin.md#4",
    ]


def _run(monkeypatch, fake_llm, max_revisions, *outputs):
    monkeypatch.setattr(agent, "MAX_REVISIONS", max_revisions)
    llm = fake_llm(*outputs)
    return agent.ask("What are the contraindications of warfarin?"), llm


def test_agent_uses_tools_revises_on_critique_and_finalizes(monkeypatch, fake_llm, chunks):
    cid = next(c.id for c in chunks if c.drug == "warfarin" and c.section == "contraindications")
    call = {
        "name": "build_context",
        "args": {"query": "contraindications", "drugs": ["warfarin"]},
        "id": "c1",
    }
    state, llm = _run(
        monkeypatch,
        fake_llm,
        2,
        Plan(steps=["Find warfarin contraindications"]),
        AIMessage("", tool_calls=[call]),  # the LLM picks the tool
        AIMessage("Contraindicated in pregnancy [made-up.md#1]. Never with grapefruit."),
        Critique(verdict="revise", unsupported_claims=["grapefruit"], feedback="Cite or drop."),
        AIMessage(f"Contraindicated in pregnancy [{cid}]."),
        Critique(verdict="approve", ambiguities=["Mechanical heart valve exception."]),
    )

    assert not llm.outputs  # every queued LLM step ran, in order
    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1 and tool_msgs[0].artifact  # retrieved passages travel as the artifact
    assert any(isinstance(m, HumanMessage) and "Cite or drop." in m.text for m in state["messages"])
    assert state["revisions"] == 1

    answer = state["answer"]
    assert answer.startswith("Contraindicated in pregnancy [1].")
    assert "[1] dailymed-warfarin.md — " in answer and "Mechanical heart valve exception." in answer
    assert "not medical advice" in answer
    assert [s.id for s in state["citations"]] == [cid]


def test_revision_budget_spent_flags_unverified_claims(monkeypatch, fake_llm):
    state, _ = _run(
        monkeypatch,
        fake_llm,
        0,
        Plan(steps=["x"]),
        AIMessage("Warfarin cures headaches."),  # answered without tools
        Critique(verdict="revise", unsupported_claims=["Warfarin cures headaches."], feedback="No source."),
    )
    assert "Not verified against the sources: Warfarin cures headaches." in state["answer"]
    assert "No corpus passage supports this answer." in state["answer"]
    assert state["citations"] == [] and "not medical advice" in state["answer"]


def test_agent_must_answer_once_tool_budget_is_spent(fake_llm):
    llm = fake_llm(AIMessage("final"))
    calls = [
        AIMessage("", tool_calls=[{"name": "build_context", "args": {}, "id": f"c{i}"}])
        for i in range(agent.MAX_TOOL_ROUNDS)
    ]
    agent.agent({"plan": ["x"], "messages": [HumanMessage("q"), *calls]})
    assert llm.tool_choices == ["none"]


# --- live: full graph through the proxy (`uv run pytest -m live`) ---


@pytest.mark.live
@pytest.mark.parametrize(("question", "expected"), EVAL_QUESTIONS)
def test_live_eval_questions_cite_expected_files(question, expected):
    state = agent.ask(question)
    assert expected <= {s.file for s in state["citations"]}
    assert state["answer"].rstrip().endswith(f"*Disclaimer: {agent.DISCLAIMER}*")
    assert len(state["plan"]) >= 1
