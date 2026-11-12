"""Pydantic models shared by tools, agent and API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

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


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class PatientProfile(BaseModel):
    """What is known about the patient. `None` means unknown (not normal); validation flags it if needed."""

    age: int | None = Field(None, ge=0, le=120, description="Years")
    sex: Literal["female", "male"] | None = None
    weight_kg: float | None = Field(None, gt=0, le=400)
    egfr: float | None = Field(None, ge=0, le=200, description="eGFR in mL/min/1.73 m²")
    hepatic_impairment: Literal["none", "mild", "moderate", "severe"] | None = None
    pregnant: bool | None = None
    breastfeeding: bool | None = None
    # Bounded (trust boundary): each entry adds prompt text, and each current medication adds 2 retrievals.
    conditions: list[ShortText] = Field(
        default_factory=list, max_length=20, description="e.g. 'atrial fibrillation', 'peptic ulcer'"
    )
    allergies: list[ShortText] = Field(default_factory=list, max_length=20)
    current_medications: list[ShortText] = Field(
        default_factory=list, max_length=20, description="Generic names"
    )


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


class Plan(BaseModel):
    steps: list[str] = Field(description="1-4 short sub-questions or actions, in order")


class Critique(BaseModel):
    verdict: Literal["approve", "revise"]
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims in the draft that no cited passage supports, or that cite the wrong passage",
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Clinically ambiguous or conditional points the reader must know (e.g. the label says "
        "'consider' or 'monitor', sources disagree, or the answer depends on unknown patient data)",
    )
    feedback: str = Field("", description="What the writer must fix, if revising")


# Base64 data URL of a PNG/JPEG/WebP/GIF image (the formats the vision model accepts), ~3.7 MB decoded at
# most; the UI downscales photos before upload, so real requests are far smaller.
ImageDataUrl = Annotated[
    str,
    StringConstraints(
        pattern=r"^data:image/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/]+={0,2}$", max_length=5_000_000
    ),
]


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=4000)
    patient: PatientProfile | None = Field(
        None, description="Optional structured patient details, passed to the agent with the question"
    )
    images: list[ImageDataUrl] = Field(
        default_factory=list,
        max_length=3,
        description="Optional images (e.g. a photo of a prescription or a drug label) as base64 data URLs",
    )


class AskResponse(BaseModel):
    answer: str = Field(description="Markdown answer with [n] citations, sources list and disclaimer")
    citations: list[Source] = Field(description="citations[n-1] is the passage behind [n]")
    plan: list[str]
    review: Critique | None = None
    revisions: int = 0
    validation: ValidationReport | None = Field(None, description="Latest prescription check, if any")
    draft: DraftPrescription | None = Field(None, description="Latest drafted prescription, if any")
