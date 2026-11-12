"""Agent tools: build_context, validate_prescription, write_prescription.

Each tool returns (text for the LLM, artifact) via `response_format="content_and_artifact"`. Artifacts
carry the retrieved `Source`s, so citations come from real chunks, never from the model's memory.
`run_validation` / `run_draft` are the plain functions behind the tools (unit-testable without the agent).
"""

import json
from typing import get_args

from langchain_core.tools import tool
from pydantic import BaseModel

from pharma_assist.llm import get_chat_model
from pharma_assist.retrieval import Chunk, get_index
from pharma_assist.schemas import (
    CorpusDrug,
    DraftPrescription,
    DraftResult,
    Issue,
    PatientProfile,
    PrescriptionItem,
    Section,
    Source,
    ValidationReport,
    ValidationResult,
    Verdict,
)

CORPUS_DRUGS: tuple[str, ...] = get_args(CorpusDrug)


# --- retrieval helpers -------------------------------------------------------------------------


def _source(c: Chunk) -> Source:
    return Source(
        id=c.id, file=c.file, drug=c.drug, heading=c.heading, section=c.section, url=c.url, text=c.text
    )


def retrieve(
    query: str, drugs: list[str] | None = None, sections: list[str] | None = None, k: int = 6
) -> list[Source]:
    return [_source(c) for c, _ in get_index().search(query, k=k, drugs=drugs, sections=sections)]


def _unique(sources: list[Source]) -> list[Source]:
    return list({s.id: s for s in sources}.values())


def render_sources(sources: list[Source]) -> str:
    return "\n\n".join(f"[{s.id}] {s.heading}\n{s.text}" for s in sources)


def _known_ids(ids: list[str], sources: list[Source]) -> list[str]:
    """Keep only citation ids that were actually retrieved (models sometimes wrap them in [] or invent)."""
    valid = {s.id for s in sources}
    return [i.strip("[] ") for i in ids if i.strip("[] ") in valid]


def _norm(drug: str) -> str:
    # shortcut: generic names only (brand names are not mapped; the corpus lists them for 6/10 drugs and
    # mixes in combination products). The agent sees the drug enum; the UI uses a dropdown.
    return drug.strip().lower()


# --- validate_prescription ---------------------------------------------------------------------

# (query suffix, sections, k) retrieved for every prescribed corpus drug.
_BASE_QUERIES: list[tuple[str, list[str], int]] = [
    ("contraindications", ["contraindications"], 4),
    ("dosage and administration, recommended and maximum dose", ["dosage"], 3),
    (
        "renal impairment eGFR kidney function dose adjustment",
        ["dosage", "contraindications", "warnings", "specific_populations"],
        3,
    ),
    ("hepatic impairment liver disease", ["dosage", "warnings", "specific_populations"], 2),
]


def _validation_queries(
    drug: str, others: list[str], patient: PatientProfile
) -> list[tuple[str, list[str], list[str], int]]:
    """(query, drugs filter, sections filter, k) for one prescribed drug."""
    queries = [(f"{drug} {q}", [drug], sections, k) for q, sections, k in _BASE_QUERIES]
    if patient.sex != "male" and (patient.pregnant is not False or patient.breastfeeding is not False):
        queries.append(
            (
                f"{drug} pregnancy lactation breastfeeding",
                [drug],
                ["specific_populations", "contraindications", "warnings"],
                3,
            )
        )
    if patient.age is not None and (patient.age < 18 or patient.age >= 65):
        group = "pediatric use in children" if patient.age < 18 else "geriatric use in elderly patients"
        queries.append((f"{drug} {group}", [drug], ["specific_populations", "dosage", "warnings"], 2))
    if patient.conditions or patient.allergies:
        terms = ", ".join(patient.conditions + patient.allergies)
        queries.append((f"{drug} {terms} hypersensitivity", [drug], ["contraindications", "warnings"], 3))
    # Interactions both ways: drug A's label may mention B even when B's label is silent about A.
    for other in others:
        queries.append((f"{drug} interaction with {other}", [drug], ["interactions", "warnings"], 3))
        if other in CORPUS_DRUGS:
            queries.append((f"{other} interaction with {drug}", [other], ["interactions", "warnings"], 3))
    return queries


def _precheck(items: list[PrescriptionItem], patient: PatientProfile) -> list[Issue]:
    """Deterministic checks that must never depend on the LLM."""
    issues = []
    for item in items:
        drug = _norm(item.drug)
        if drug not in CORPUS_DRUGS:
            issues.append(
                Issue(
                    severity="major",
                    category="out_of_corpus",
                    drug=item.drug,
                    message=f"'{item.drug}' is not in the reference corpus ({', '.join(CORPUS_DRUGS)}), "
                    "so it cannot be validated here. Needs pharmacist review.",
                )
            )
        for allergy in patient.allergies:
            if drug in allergy.lower():
                issues.append(
                    Issue(
                        severity="critical",
                        category="allergy",
                        drug=item.drug,
                        message=f"Patient has a documented allergy: '{allergy}'.",
                    )
                )
    return issues


def compute_verdict(issues: list[Issue]) -> Verdict:
    """Fail closed: any critical issue rejects; unknown data or unvalidated drugs block approval."""
    if any(i.severity == "critical" for i in issues):
        return "rejected"
    if any(i.category in ("missing_info", "out_of_corpus") for i in issues):
        return "needs_more_info"
    return "approved_with_warnings" if issues else "approved"


class _Review(BaseModel):
    issues: list[Issue]
    summary: str


_VALIDATE_SYSTEM = """You check a prescription for one patient against FDA drug-label passages.
Rules:
- Use ONLY the passages. Every issue must cite the ids of the passages that support it in source_ids.
- For each prescribed drug check: contraindications, dose/frequency against label limits, renal (eGFR) and \
hepatic adjustments, pregnancy/lactation, age, allergies and conditions, and interactions with the patient's \
current medications and with the other prescribed drugs.
- Severity: critical = the label contraindicates it for this patient, or the dose exceeds the label \
maximum; major = needs action (dose adjustment, monitoring, avoid unless benefit outweighs risk); \
minor = awareness only.
- Patient fields that are null are UNKNOWN, not normal. If a label rule depends on an unknown field \
(e.g. eGFR for a drug with renal limits, pregnancy status for a drug contraindicated in pregnancy), add a \
`missing_info` issue (severity major) naming the field. Do not add missing_info for fields no passage \
makes relevant.
- Do not report anything the passages do not support. Skip drugs marked out of corpus.
- summary: 1-3 plain sentences."""


def run_validation(items: list[PrescriptionItem], patient: PatientProfile) -> ValidationResult:
    issues = _precheck(items, patient)
    drugs = [d for d in dict.fromkeys(_norm(i.drug) for i in items) if d in CORPUS_DRUGS]
    if not drugs:  # nothing validated (empty or out-of-corpus only): never approve
        report = ValidationReport(
            verdict=compute_verdict(issues) if issues else "needs_more_info",
            issues=issues,
            summary="No prescribed drug could be validated.",
        )
        return ValidationResult(report=report, sources=[])

    current = [_norm(m) for m in patient.current_medications]
    sources: list[Source] = []
    for drug in drugs:
        others = [d for d in dict.fromkeys(current + drugs) if d != drug]
        for query, drug_filter, sections, k in _validation_queries(drug, others, patient):
            sources += retrieve(query, drugs=drug_filter, sections=sections, k=k)
    sources = _unique(sources)

    request = {
        "prescription": [i.model_dump(exclude_none=True) for i in items],
        "patient": patient.model_dump(),
        "out_of_corpus": [i.drug for i in items if _norm(i.drug) not in CORPUS_DRUGS],
    }
    review = (
        get_chat_model()
        .with_structured_output(_Review)
        .invoke(
            [
                ("system", _VALIDATE_SYSTEM),
                ("human", f"{json.dumps(request, indent=1)}\n\nPassages:\n\n{render_sources(sources)}"),
            ]
        )
    )
    for issue in review.issues:
        issue.source_ids = _known_ids(issue.source_ids, sources)
    issues += review.issues
    report = ValidationReport(verdict=compute_verdict(issues), issues=issues, summary=review.summary)
    return ValidationResult(report=report, sources=sources)


def render_report(report: ValidationReport) -> str:
    lines = [f"Verdict: {report.verdict}"]
    for i in report.issues:
        cites = " ".join(f"[{s}]" for s in i.source_ids)
        lines.append(f"- [{i.severity}] {i.category} ({i.drug or '-'}): {i.message} {cites}".rstrip())
    lines.append(f"Summary: {report.summary}")
    return "\n".join(lines)


# --- write_prescription ------------------------------------------------------------------------

_DRAFT_SYSTEM = f"""You draft a prescription from a clinician's request using ONLY the drug-label passages.
- Use only these drugs (generic names): {", ".join(CORPUS_DRUGS)}. If none fits, return no items and say why.
- Take dose, route and frequency from the label's dosing passages for the stated indication; prefer the \
usual starting dose and apply adjustments the passages give for this patient.
- Cite passage ids in the rationale like [dailymed-metformin.md#3] and list them in source_ids.
This is a draft for clinician review; it is validated automatically afterwards."""


def run_draft(description: str, patient: PatientProfile | None = None) -> DraftResult:
    patient = patient or PatientProfile()
    sources = retrieve(description, sections=["indications"], k=6) + retrieve(description, k=4)
    candidates = [d for d in dict.fromkeys(s.drug for s in sources) if d][:3]
    for drug in candidates:
        sources += retrieve(f"{drug} dosage {description}", drugs=[drug], sections=["dosage"], k=3)
    sources = _unique(sources)

    draft = (
        get_chat_model()
        .with_structured_output(DraftPrescription)
        .invoke(
            [
                ("system", _DRAFT_SYSTEM),
                (
                    "human",
                    f"Request: {description}\nPatient: {patient.model_dump_json(exclude_none=True)}"
                    f"\n\nPassages:\n\n{render_sources(sources)}",
                ),
            ]
        )
    )
    draft.source_ids = _known_ids(draft.source_ids, sources)
    if not draft.items:
        return DraftResult(draft=draft, validation=None, sources=sources)

    validation = run_validation(draft.items, patient)  # every draft is validated before it is shown
    return DraftResult(
        draft=draft, validation=validation.report, sources=_unique(sources + validation.sources)
    )


# --- LangChain tools (descriptions are what the agent uses to choose) ---------------------------


@tool(response_format="content_and_artifact", parse_docstring=True)
def build_context(
    query: str,
    drugs: list[CorpusDrug] | None = None,
    sections: list[Section] | None = None,
    k: int = 6,
) -> tuple[str, list[Source]]:
    """Search the drug-label corpus and return relevant passages with citation ids.

    The corpus holds FDA DailyMed labels and MedlinePlus monographs for acetaminophen, albuterol,
    amoxicillin, apixaban, aspirin, atorvastatin, ibuprofen, metformin, sertraline and warfarin, plus a
    pharmacology glossary. Use it for factual questions (indications, dosing, contraindications, warnings,
    interactions, special populations, mechanism). Call it once per sub-question; filter by drug and
    section for precise results.

    Args:
        query: What to look for, in plain words (e.g. "contraindications in pregnancy").
        drugs: Only search these drugs. Omit for glossary or general terms.
        sections: Only search these label sections.
        k: Number of passages to return (1-12).
    """
    sources = retrieve(query, drugs=drugs, sections=sections, k=max(1, min(k, 12)))
    if not sources:
        return "No passages found. Try a broader query or fewer filters.", []
    return render_sources(sources), sources


@tool(response_format="content_and_artifact", parse_docstring=True)
def validate_prescription(
    prescription: list[PrescriptionItem], patient: PatientProfile
) -> tuple[str, ValidationResult]:
    """Check a concrete prescription for a specific patient against the drug labels.

    Checks contraindications, dose limits, renal/hepatic adjustment, pregnancy/lactation, age, allergies
    and interactions (including the patient's current medications). Returns a verdict (approved,
    approved_with_warnings, needs_more_info, rejected) with cited issues. Use it when the user gives a
    drug and dose for a described patient or asks whether one is safe for them.

    Args:
        prescription: The prescribed items, with generic drug names.
        patient: What is known about the patient; leave unknown fields null.
    """
    result = run_validation(prescription, patient)
    return render_report(result.report), result


@tool(response_format="content_and_artifact", parse_docstring=True)
def write_prescription(description: str, patient: PatientProfile | None = None) -> tuple[str, DraftResult]:
    """Draft a prescription from a clinical request, then validate it automatically for the patient.

    Uses only corpus drugs and label dosing. Use it when the user asks to write, draft or suggest a
    prescription, or what to prescribe (e.g. "what should I give this patient for type 2 diabetes?").

    Args:
        description: The clinical request, including the indication.
        patient: What is known about the patient, if anything.
    """
    result = run_draft(description, patient)
    lines = [f"- {i.drug} {i.dose} {i.route} {i.frequency}" for i in result.draft.items]
    text = "Draft prescription:\n" + ("\n".join(lines) or "(none)") + f"\nRationale: {result.draft.rationale}"
    if result.validation:
        text += "\n\nAutomatic validation:\n" + render_report(result.validation)
    return text, result


TOOLS = [build_context, validate_prescription, write_prescription]
