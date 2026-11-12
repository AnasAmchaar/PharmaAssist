"""LangGraph agent: planner -> agent (ReAct over TOOLS) <-> tools -> critic -> (revise | finalizer).

The LLM chooses the tools (`bind_tools`); nothing here routes on keywords. Citations are chunk ids taken
from tool artifacts, so the finalizer can renumber them and drop any the model invented. The disclaimer
is appended in code, never left to the model.
"""

import json
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from pharma_assist.llm import get_chat_model
from pharma_assist.schemas import Critique, Plan, Source
from pharma_assist.tools import CORPUS_DRUGS, TOOLS, render_sources

MAX_TOOL_ROUNDS = 8  # after this many tool-calling turns the agent must answer with what it has
# Critic-requested rewrites; afterwards remaining doubts are shown as reviewer notes. 1, not 2: in the eval a
# second rewrite rarely fixed what the first did not, and each one costs ~30 s.
MAX_REVISIONS = 1
RECURSION_LIMIT = 50  # backstop: the guards above cap a run at ~22 steps (planner, 8 tool rounds, 2 drafts)

DISCLAIMER = (
    "This answer is generated from FDA DailyMed labels and MedlinePlus monographs for research and "
    "educational purposes only. It is not medical advice and does not replace the judgment of a qualified "
    "clinician or pharmacist."
)


class AgentState(TypedDict, total=False):
    question: str
    plan: list[str]
    messages: Annotated[list[AnyMessage], add_messages]
    critique: Critique
    revisions: int
    answer: str
    citations: list[Source]


# --- prompts -----------------------------------------------------------------------------------

_PLANNER_SYSTEM = f"""You plan how to answer a pharmacology question from a drug-label corpus covering: \
{", ".join(CORPUS_DRUGS)}.
Break the question into 1-4 short sub-questions or actions, in order. Use generic drug names. If the user \
describes a patient and a drug/dose, include a step to validate that prescription; if they ask for a \
prescription to be written, include a step to draft it. Plan only what the user asked: no extra steps for \
counseling, alternatives, titration, quantities or refills unless requested. Do not answer the question."""

_AGENT_SYSTEM = """You are PharmaAssist, a pharmacology research assistant. You answer ONLY from passages \
returned by your tools, never from memory.

Plan:
{plan}

How to work:
- Use the tools to gather evidence for every step of the plan before answering. build_context returns \
label passages; filter by drug and section, and search each drug of a comparison or interaction \
separately (an interaction may be described in either drug's label). validate_prescription checks a \
concrete prescription for a patient; write_prescription drafts one and validates it.
- Cite every factual sentence with the passage id(s) in square brackets right after it, e.g. \
[dailymed-warfarin.md#13]. Only cite ids that appear in tool results.
- If the passages do not answer something, say so plainly instead of guessing.
- Answer what was asked, concisely (usually under 250 words) and clinically precisely: give thresholds, \
doses and conditions exactly as the label states them. Use short paragraphs or bullet points. Do not add \
counseling, alternatives or background the user did not ask for.
- After validate_prescription or write_prescription, report the verdict and its issues with their \
citations; do not re-derive them.
- Do not add a medical disclaimer; it is added automatically."""

_CRITIC_SYSTEM = """You review a draft answer to a pharmacology question before it is shown to the user.
Check the draft ONLY against the retrieved passages below:
- Every factual claim must be supported by the passage(s) it cites. List claims that are unsupported, \
cite nothing, or cite a passage that does not say it.
- The draft must answer every part of the question (and plan) that the passages can answer.
- List clinically ambiguous or conditional points the reader must be warned about (e.g. "use with \
caution", "consider", thresholds that differ between sources, answers that depend on unknown patient data).
verdict = "revise" if there is any unsupported claim, a missing citation, or an unanswered part the \
passages could answer; otherwise "approve". Ambiguities alone do not require a revision. In feedback, \
tell the writer exactly what to fix."""


# --- nodes -------------------------------------------------------------------------------------


def planner(state: AgentState) -> dict:
    plan = (
        get_chat_model()
        .with_structured_output(Plan)
        .invoke([("system", _PLANNER_SYSTEM), ("human", state["question"])])
    )
    return {"plan": plan.steps, "messages": [HumanMessage(state["question"])], "revisions": 0}


def agent(state: AgentState) -> dict:
    rounds = sum(1 for m in state["messages"] if isinstance(m, AIMessage) and m.tool_calls)
    # Out of tool budget: still bind the tools (the history contains tool calls) but forbid new ones.
    model = get_chat_model().bind_tools(TOOLS, tool_choice="none" if rounds >= MAX_TOOL_ROUNDS else "auto")
    plan = "\n".join(f"{i}. {s}" for i, s in enumerate(state["plan"], 1))
    return {"messages": [model.invoke([SystemMessage(_AGENT_SYSTEM.format(plan=plan)), *state["messages"]])]}


def collect_sources(messages: list[AnyMessage]) -> dict[str, Source]:
    """Every passage any tool returned, by citation id (tool artifacts are list[Source] or have .sources)."""
    out: dict[str, Source] = {}
    for m in messages:
        if isinstance(m, ToolMessage) and m.artifact is not None:
            for s in m.artifact if isinstance(m.artifact, list) else m.artifact.sources:
                out[s.id] = s
    return out


def critic(state: AgentState) -> dict:
    sources = collect_sources(state["messages"])
    review = {
        "question": state["question"],
        "plan": state["plan"],
        "draft_answer": state["messages"][-1].text,
    }
    critique = (
        get_chat_model()
        .with_structured_output(Critique)
        .invoke(
            [
                ("system", _CRITIC_SYSTEM),
                (
                    "human",
                    f"{json.dumps(review, indent=1)}\n\nRetrieved passages:\n\n"
                    + (render_sources(list(sources.values())) or "(none: no tool returned passages)"),
                ),
            ]
        )
    )
    update: dict = {"critique": critique}
    if critique.verdict == "revise" and state["revisions"] < MAX_REVISIONS:
        issues = "\n".join(f"- {c}" for c in critique.unsupported_claims)
        update["revisions"] = state["revisions"] + 1
        update["messages"] = [
            HumanMessage(
                f"Reviewer feedback on your draft:\n{critique.feedback}\n{issues}\n"
                "Revise the answer: gather more evidence with the tools if needed, and remove any claim "
                "you cannot support with a cited passage. Reply with the full revised answer."
            )
        ]
    return update


_BRACKET = re.compile(r"(\s*)\[([^\[\]]+)\]")


def renumber_citations(text: str, sources: dict[str, Source]) -> tuple[str, list[Source]]:
    """`[file.md#n]` / `[a.md#1, b.md#2]` -> `[1]` / `[1][2]` in order of first use; unknown ids dropped."""
    numbers: dict[str, int] = {}

    def sub(m: re.Match) -> str:
        parts = [p.strip() for p in re.split(r"[,;]", m.group(2))]
        if not any(".md#" in p for p in parts):
            return m.group(0)  # not a citation, e.g. a markdown link label
        cited = [numbers.setdefault(p, len(numbers) + 1) for p in parts if p in sources]
        return m.group(1) + "".join(f"[{n}]" for n in cited) if cited else ""

    body = _BRACKET.sub(sub, text)
    return body, [sources[i] for i in numbers]


def finalizer(state: AgentState) -> dict:
    body, citations = renumber_citations(state["messages"][-1].text, collect_sources(state["messages"]))
    parts = [body.strip()]

    critique = state.get("critique")
    notes = []
    if critique and critique.verdict == "revise":  # revision budget spent: say what stayed unverified
        notes += [f"Not verified against the sources: {c}" for c in critique.unsupported_claims]
    if critique:
        notes += critique.ambiguities
    if notes:
        parts.append("**Reviewer notes**\n" + "\n".join(f"- {n}" for n in notes))

    if citations:
        refs = [f"[{n}] {s.file} — {s.heading}" for n, s in enumerate(citations, 1)]
        parts.append("**Sources**\n" + "\n".join(refs))
    else:
        parts.append("**Sources**\nNo corpus passage supports this answer.")

    parts.append(f"*Disclaimer: {DISCLAIMER}*")
    return {"answer": "\n\n".join(parts), "citations": citations}


# --- graph -------------------------------------------------------------------------------------


def _after_agent(state: AgentState) -> str:
    return "tools" if state["messages"][-1].tool_calls else "critic"


def _after_critic(state: AgentState) -> str:
    # The critic only appends feedback when it asked for a revision and budget remained.
    return "agent" if isinstance(state["messages"][-1], HumanMessage) else "finalizer"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("planner", planner)
    g.add_node("agent", agent)
    # handle_tool_errors=True: a failing tool becomes an error message the agent can react to, not a crash.
    g.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))
    g.add_node("critic", critic)
    g.add_node("finalizer", finalizer)
    g.add_edge(START, "planner")
    g.add_edge("planner", "agent")
    g.add_conditional_edges("agent", _after_agent, ["tools", "critic"])
    g.add_edge("tools", "agent")
    g.add_conditional_edges("critic", _after_critic, ["agent", "finalizer"])
    g.add_edge("finalizer", END)
    return g.compile().with_config(recursion_limit=RECURSION_LIMIT)


graph = build_graph()


def ask(question: str) -> AgentState:
    return graph.invoke({"question": question})
