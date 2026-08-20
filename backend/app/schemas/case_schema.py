from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Sex(str, Enum):
    female = "female"
    male = "male"
    other = "other"


class LanguageStyle(BaseModel):
    """How the simulated patient speaks during the encounter."""

    model_config = ConfigDict(extra="forbid")

    primary_language: str = Field(..., min_length=1)
    speech_register: Literal["colloquial", "plain", "formal"] = "plain"
    uses_medical_jargon: bool = False
    accent_or_dialect: str | None = None
    speech_notes: str = Field(
        ...,
        min_length=1,
        description="Lay-term phrasing, fillers, and disclosure style.",
    )


class PatientProfile(BaseModel):
    """Demographics, demeanor, and language style for the SP agent."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=1)
    preferred_name: str = Field(..., min_length=1)
    age_years: int = Field(..., ge=0, le=120)
    sex: Sex
    occupation: str = Field(..., min_length=1)
    living_situation: str = Field(..., min_length=1)
    demeanor: str = Field(
        ...,
        min_length=1,
        description="Affect, cooperation, and emotional tone during the encounter.",
    )
    language_style: LanguageStyle


class OPQRST(BaseModel):
    """HPI parameters: Onset, Provocation/Palliation, Quality, Region/Radiation, Severity, Time."""

    model_config = ConfigDict(extra="forbid")

    onset: str = Field(..., min_length=1)
    provocation_palliation: str = Field(..., min_length=1)
    quality: str = Field(..., min_length=1)
    region_radiation: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    time_course: str = Field(..., min_length=1)


class Medication(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    dose: str = Field(..., min_length=1)
    frequency: str = Field(..., min_length=1)
    indication: str | None = None


class Allergy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allergen: str = Field(..., min_length=1)
    reaction: str = Field(..., min_length=1)


class SocialHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tobacco: str = Field(..., min_length=1)
    alcohol: str = Field(..., min_length=1)
    recreational_drugs: str = Field(..., min_length=1)
    diet_and_exercise: str | None = None
    occupation_exposures: str | None = None


class FamilyHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relation: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    notes: str | None = None


class ClinicalHistory(BaseModel):
    """Chief complaint, HPI (OPQRST), PMHx, meds, allergies, social/family history."""

    model_config = ConfigDict(extra="forbid")

    chief_complaint: str = Field(..., min_length=1)
    history_of_present_illness: str = Field(..., min_length=1)
    opqrst: OPQRST
    associated_symptoms: list[str] = Field(default_factory=list)
    pertinent_negatives: list[str] = Field(default_factory=list)
    past_medical_history: list[str] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    social_history: SocialHistory
    family_history: list[FamilyHistoryItem] = Field(default_factory=list)
    review_of_systems_positives: list[str] = Field(default_factory=list)


class VitalSigns(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blood_pressure_mmhg: str = Field(..., min_length=1, examples=["148/92"])
    heart_rate_bpm: int = Field(..., ge=20, le=250)
    respiratory_rate: int = Field(..., ge=4, le=60)
    temperature_c: float = Field(..., ge=30.0, le=45.0)
    spo2_percent: int = Field(..., ge=50, le=100)
    pain_score_0_to_10: int = Field(..., ge=0, le=10)


class HEENTExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    head: str = Field(..., min_length=1)
    eyes: str = Field(..., min_length=1)
    ears: str = Field(..., min_length=1)
    nose: str = Field(..., min_length=1)
    throat: str = Field(..., min_length=1)
    neck: str = Field(..., min_length=1)


class CardiovascularExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection: str = Field(..., min_length=1)
    palpation: str = Field(..., min_length=1)
    auscultation: str = Field(..., min_length=1)
    pulses: str = Field(..., min_length=1)
    edema: str = Field(..., min_length=1)


class RespiratoryExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection: str = Field(..., min_length=1)
    percussion: str = Field(..., min_length=1)
    auscultation: str = Field(..., min_length=1)
    work_of_breathing: str = Field(..., min_length=1)


class AbdominalExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection: str = Field(..., min_length=1)
    auscultation: str = Field(..., min_length=1)
    percussion: str = Field(..., min_length=1)
    palpation: str = Field(..., min_length=1)
    peritoneal_signs: str = Field(..., min_length=1)


class NeurologicExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mental_status: str = Field(..., min_length=1)
    cranial_nerves: str = Field(..., min_length=1)
    motor: str = Field(..., min_length=1)
    sensory: str = Field(..., min_length=1)
    reflexes: str = Field(..., min_length=1)
    gait_or_coordination: str | None = None


class MusculoskeletalExam(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspection: str = Field(..., min_length=1)
    palpation: str = Field(..., min_length=1)
    range_of_motion: str = Field(..., min_length=1)
    strength: str | None = None
    special_tests: str | None = None


class PhysicalExamFindings(BaseModel):
    """Standard clinical systems for gated PE disclosure."""

    model_config = ConfigDict(extra="forbid")

    vitals: VitalSigns
    general: str = Field(..., min_length=1)
    heent: HEENTExam
    respiratory: RespiratoryExam
    cardiovascular: CardiovascularExam
    abdomen: AbdominalExam
    neurologic: NeurologicExam
    musculoskeletal: MusculoskeletalExam


class OSCECategory(str, Enum):
    introduction_and_rapport = "introduction_and_rapport"
    history_taking = "history_taking"
    physical_examination = "physical_examination"
    communication = "communication"
    clinical_reasoning = "clinical_reasoning"
    professionalism = "professionalism"


class OSCEChecklistItem(BaseModel):
    """A single scored rubric item."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    category: OSCECategory
    description: str = Field(..., min_length=1)
    points: float = Field(..., gt=0, description="Must be a positive point weight.")
    required: bool = True
    scoring_notes: str | None = None


class OSCEChecklist(BaseModel):
    """OSCE rubric with categories and point weights."""

    model_config = ConfigDict(extra="forbid")

    station_title: str = Field(..., min_length=1)
    time_limit_minutes: int = Field(..., ge=5, le=30)
    passing_score: float = Field(..., gt=0)
    items: list[OSCEChecklistItem] = Field(..., min_length=1)

    @field_validator("items")
    @classmethod
    def unique_item_ids(cls, items: list[OSCEChecklistItem]) -> list[OSCEChecklistItem]:
        ids = [item.id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("OSCE checklist item ids must be unique")
        return items

    @property
    def total_points(self) -> float:
        return sum(item.points for item in self.items)

    @model_validator(mode="after")
    def passing_score_within_total(self) -> Self:
        if self.passing_score > self.total_points:
            raise ValueError("passing_score cannot exceed total rubric points")
        return self


class StudentVisibleCaseMetadata(BaseModel):
    """Briefing a student may see. Must not contain diagnosis or differentials."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    chief_complaint: str = Field(..., min_length=1)
    setting: str = Field(..., min_length=1)


class HiddenClinicalTruths(BaseModel):
    """Faculty/engine only. Never serialize on student-facing endpoints."""

    model_config = ConfigDict(extra="forbid")

    final_diagnosis: str = Field(..., min_length=1)
    differential_diagnoses: list[str] = Field(..., min_length=1)
    student_forbidden_terms: list[str] = Field(
        ...,
        min_length=1,
        description="Diagnosis strings that must never appear in student-visible metadata.",
    )
    teaching_points: list[str] = Field(default_factory=list)


class StudentCaseBriefing(BaseModel):
    """Public case card: title, chief complaint, and setting only."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    title: str
    chief_complaint: str
    setting: str


class ClinicalCase(BaseModel):
    """Full seed case for the patient agent and faculty tools."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_]+$")
    specialty: Literal["cardiology", "gastroenterology", "other"]
    learning_objectives: list[str] = Field(..., min_length=1)
    metadata: StudentVisibleCaseMetadata
    hidden: HiddenClinicalTruths
    disclosure_notes: str = Field(
        ...,
        min_length=1,
        description="Engine-only: what the SP may volunteer vs. disclose only if asked.",
    )
    patient_profile: PatientProfile
    clinical_history: ClinicalHistory
    pe_findings: PhysicalExamFindings
    osce_checklist: OSCEChecklist

    @model_validator(mode="after")
    def isolate_hidden_truths_from_student_metadata(self) -> Self:
        visible = " ".join(
            [
                self.metadata.title,
                self.metadata.chief_complaint,
                self.metadata.setting,
            ]
        ).lower()
        for term in self.hidden.student_forbidden_terms:
            needle = term.strip().lower()
            if needle and needle in visible:
                raise ValueError(
                    f"Hidden clinical term {term!r} leaked into student-visible metadata"
                )
        return self

    def to_student_briefing(self) -> StudentCaseBriefing:
        return StudentCaseBriefing(
            case_id=self.case_id,
            title=self.metadata.title,
            chief_complaint=self.metadata.chief_complaint,
            setting=self.metadata.setting,
        )


CaseSchema = ClinicalCase
