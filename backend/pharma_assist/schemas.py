"""Pydantic models shared by tools, agent and API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The 10 corpus drugs (generic names, as in the corpus file names). Tested against `corpus/`.
CorpusDrug = Literal[
    "acetaminophen",
    "albuterol",
    "amoxicillin",
    "apixaban",
    "aspirin",
    "atorvastatin",
    "ibuprofen",
    "metformin",
    "sertraline",
    "warfarin",
]
# Canonical section tags produced by `retrieval.canonical_section`. Tested against `retrieval.SECTIONS`.
Section = Literal[
    "contraindications",
    "interactions",
    "overdose",
    "adverse_reactions",
    "specific_populations",
    "indications",
    "dosage",
    "warnings",
    "pharmacology",
    "other",
]


class Source(BaseModel):
    """A retrieved corpus chunk; `id` is the citation key the LLM must use, e.g. `dailymed-warfarin.md#13`."""

    id: str
    file: str
    drug: str | None = None
    heading: str
    section: str
    url: str | None = None
    text: str


class PatientProfile(BaseModel):
    """What is known about the patient. `None` means unknown (not normal); validation flags it if needed."""

    age: int | None = Field(None, ge=0, le=120, description="Years")
    sex: Literal["female", "male"] | None = None
    weight_kg: float | None = Field(None, gt=0, le=400)
    egfr: float | None = Field(None, ge=0, le=200, description="eGFR in mL/min/1.73 m²")
    hepatic_impairment: Literal["none", "mild", "moderate", "severe"] | None = None
    pregnant: bool | None = None
    breastfeeding: bool | None = None
    conditions: list[str] = Field(
        default_factory=list, description="e.g. 'atrial fibrillation', 'peptic ulcer'"
    )
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list, description="Generic names")


class PrescriptionItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    drug: str = Field(min_length=1, description="Generic drug name, e.g. 'metformin'")
    dose: str = Field(min_length=1, description="Amount per administration, e.g. '500 mg'")
    route: str = "oral"
    frequency: str = Field(min_length=1, description="e.g. 'twice daily with meals'")
    duration: str | None = None
    indication: str | None = None


Severity = Literal["critical", "major", "minor"]
IssueCategory = Literal[
    "contraindication",
    "interaction",
    "dosing",
    "renal",
    "hepatic",
    "pregnancy_lactation",
    "age",
    "allergy",
    "missing_info",
    "out_of_corpus",
    "other",
]


class Issue(BaseModel):
    severity: Severity = Field(
        description="critical = contraindicated / allergy / above label maximum (do not prescribe); "
        "major = needs action (dose change, monitoring, missing data); minor = awareness only"
    )
    category: IssueCategory
    drug: str | None = None
    message: str
    source_ids: list[str] = Field(
        default_factory=list, description="Ids of the passages supporting this issue"
    )


Verdict = Literal["approved", "approved_with_warnings", "needs_more_info", "rejected"]


class ValidationReport(BaseModel):
    verdict: Verdict
    issues: list[Issue]
    summary: str


class ValidationResult(BaseModel):
    report: ValidationReport
    sources: list[Source]


class DraftPrescription(BaseModel):
    items: list[PrescriptionItem] = Field(description="Empty if no corpus drug fits the request")
    rationale: str = Field(description="Why these drugs/doses, citing passage ids like [dailymed-x.md#3]")
    source_ids: list[str] = Field(default_factory=list)


class DraftResult(BaseModel):
    draft: DraftPrescription
    validation: ValidationReport | None  # None when nothing could be drafted
    sources: list[Source]
