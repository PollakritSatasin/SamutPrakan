from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.case_schema import (
    CaseSchema,
    ClinicalCase,
    OSCEChecklist,
    OSCEChecklistItem,
    PhysicalExamFindings,
)
from app.services.case_loader import SEED_CASES_DIR, load_all_seed_cases, load_case_from_path

EXPECTED_SEED_FILES = (
    "cardio_acute_coronary_syndrome.json",
    "gi_acute_appendicitis.json",
)

STANDARD_PE_SYSTEMS = (
    "vitals",
    "general",
    "heent",
    "respiratory",
    "cardiovascular",
    "abdomen",
    "neurologic",
    "musculoskeletal",
)


def _seed_paths() -> list[Path]:
    return sorted(SEED_CASES_DIR.glob("*.json"))


def _valid_payload() -> dict:
    return load_case_from_path(SEED_CASES_DIR / "cardio_acute_coronary_syndrome.json").model_dump()


def test_seed_case_files_exist() -> None:
    missing = [name for name in EXPECTED_SEED_FILES if not (SEED_CASES_DIR / name).exists()]
    assert missing == [], f"Missing seed case files: {missing}"


def test_every_seed_json_loads_into_case_schema_without_validation_error() -> None:
    paths = _seed_paths()
    assert paths, "No JSON files found in seed_cases/"
    assert {path.name for path in paths} == set(EXPECTED_SEED_FILES)

    for path in paths:
        case = CaseSchema.model_validate_json(path.read_text(encoding="utf-8"))
        assert isinstance(case, ClinicalCase)
        assert case.case_id


@pytest.mark.parametrize("filename", EXPECTED_SEED_FILES)
def test_seed_json_validates_against_clinical_case_schema(filename: str) -> None:
    path = SEED_CASES_DIR / filename
    case = load_case_from_path(path)

    assert isinstance(case, ClinicalCase)
    assert case.case_id
    assert case.patient_profile.language_style.uses_medical_jargon is False
    assert case.clinical_history.opqrst.onset
    assert case.pe_findings.vitals.heart_rate_bpm > 0
    assert case.osce_checklist.items
    assert all(item.points > 0 for item in case.osce_checklist.items)
    assert case.osce_checklist.passing_score > 0
    assert case.osce_checklist.total_points >= case.osce_checklist.passing_score


def test_load_all_seed_cases_returns_both_complete_cases() -> None:
    cases = load_all_seed_cases()
    case_ids = {case.case_id for case in cases}

    assert "chest_pressure_walk_in" in case_ids
    assert "migratory_abdominal_pain" in case_ids

    cardio = next(c for c in cases if c.case_id == "chest_pressure_walk_in")
    gi = next(c for c in cases if c.case_id == "migratory_abdominal_pain")

    assert cardio.specialty == "cardiology"
    assert "left arm" in cardio.clinical_history.opqrst.region_radiation.lower()
    assert gi.specialty == "gastroenterology"
    assert "mcburney" in gi.pe_findings.abdomen.palpation.lower()


def test_pe_findings_includes_all_standard_clinical_systems() -> None:
    fields = set(PhysicalExamFindings.model_fields)
    assert set(STANDARD_PE_SYSTEMS) <= fields

    for case in load_all_seed_cases():
        dumped = case.pe_findings.model_dump()
        for system in STANDARD_PE_SYSTEMS:
            assert dumped[system], f"{case.case_id} missing pe_findings.{system}"


def test_osce_checklist_rejects_duplicate_item_ids() -> None:
    payload = {
        "station_title": "Duplicate ids",
        "time_limit_minutes": 10,
        "passing_score": 1,
        "items": [
            {
                "id": "same",
                "category": "history_taking",
                "description": "Ask OPQRST",
                "points": 1,
                "required": True,
            },
            {
                "id": "same",
                "category": "communication",
                "description": "Use lay terms",
                "points": 1,
                "required": True,
            },
        ],
    }
    with pytest.raises(ValidationError, match="OSCE checklist item ids must be unique"):
        OSCEChecklist.model_validate(payload)


@pytest.mark.parametrize("points", [0, -1, -0.5])
def test_osce_item_requires_positive_point_weights(points: float) -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        OSCEChecklistItem.model_validate(
            {
                "id": "hx",
                "category": "history_taking",
                "description": "Ask OPQRST",
                "points": points,
                "required": True,
            }
        )


def test_osce_passing_score_cannot_exceed_total_points() -> None:
    with pytest.raises(ValidationError, match="passing_score cannot exceed total rubric points"):
        OSCEChecklist.model_validate(
            {
                "station_title": "Overweighted pass mark",
                "time_limit_minutes": 10,
                "passing_score": 10,
                "items": [
                    {
                        "id": "hx",
                        "category": "history_taking",
                        "description": "Ask OPQRST",
                        "points": 1,
                        "required": True,
                    }
                ],
            }
        )


def test_clinical_case_rejects_unknown_fields() -> None:
    extra = _valid_payload()
    extra["secret_diagnosis"] = "do not leak"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CaseSchema.model_validate(extra)


def test_hidden_truths_are_isolated_from_student_metadata() -> None:
    for case in load_all_seed_cases():
        briefing = case.to_student_briefing().model_dump()
        assert set(briefing) == {"case_id", "title", "chief_complaint", "setting"}
        visible = " ".join(briefing.values()).lower()
        for term in case.hidden.student_forbidden_terms:
            assert term.lower() not in visible
        assert "final_diagnosis" not in briefing
        assert "differential_diagnoses" not in briefing


def test_leaked_diagnosis_in_student_title_is_rejected() -> None:
    payload = _valid_payload()
    payload["metadata"]["title"] = "Acute Coronary Syndrome Walk-In"
    with pytest.raises(ValidationError, match="leaked into student-visible metadata"):
        CaseSchema.model_validate(payload)


def test_missing_chief_complaint_is_rejected_with_field_required() -> None:
    payload = _valid_payload()
    del payload["clinical_history"]["chief_complaint"]
    with pytest.raises(ValidationError) as exc_info:
        CaseSchema.model_validate(payload)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("clinical_history", "chief_complaint")
    assert error["type"] == "missing"
    assert "Field required" in error["msg"]


def test_empty_chief_complaint_is_rejected() -> None:
    payload = _valid_payload()
    payload["clinical_history"]["chief_complaint"] = ""
    with pytest.raises(ValidationError, match="at least 1 character"):
        CaseSchema.model_validate(payload)


def test_negative_rubric_points_on_full_case_are_rejected() -> None:
    payload = _valid_payload()
    payload["osce_checklist"]["items"][0]["points"] = -2
    with pytest.raises(ValidationError) as exc_info:
        CaseSchema.model_validate(payload)

    error = next(err for err in exc_info.value.errors() if err["loc"][-1] == "points")
    assert error["loc"] == ("osce_checklist", "items", 0, "points")
    assert "greater than 0" in error["msg"]


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(ValidationError, match="JSON decode error|Invalid JSON"):
        CaseSchema.model_validate_json("{not valid json")


def test_out_of_range_vitals_are_rejected() -> None:
    payload = _valid_payload()
    payload["pe_findings"]["vitals"]["pain_score_0_to_10"] = 11
    with pytest.raises(ValidationError, match="less than or equal to 10"):
        CaseSchema.model_validate(payload)

    payload = _valid_payload()
    payload["pe_findings"]["vitals"]["heart_rate_bpm"] = 10
    with pytest.raises(ValidationError, match="greater than or equal to 20"):
        CaseSchema.model_validate(payload)


def test_missing_pe_system_is_rejected() -> None:
    payload = _valid_payload()
    del payload["pe_findings"]["heent"]
    with pytest.raises(ValidationError) as exc_info:
        CaseSchema.model_validate(payload)

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("pe_findings", "heent")
    assert error["type"] == "missing"


def test_acs_seed_is_clinically_coherent() -> None:
    case = load_case_from_path(SEED_CASES_DIR / "cardio_acute_coronary_syndrome.json")
    hx = case.clinical_history
    vitals = case.pe_findings.vitals
    opqrst = hx.opqrst

    assert case.patient_profile.age_years >= 45
    assert case.patient_profile.sex.value == "male"
    assert "40 minute" in hx.chief_complaint.lower() or "40 minute" in opqrst.onset.lower()
    assert "sudden" in opqrst.onset.lower()
    assert "walking" in opqrst.onset.lower()
    assert "rest" in opqrst.provocation_palliation.lower()
    assert "not" in opqrst.provocation_palliation.lower() or "no" in opqrst.provocation_palliation.lower()
    assert any(word in opqrst.quality.lower() for word in ("crushing", "pressure", "heavy"))
    assert "left arm" in opqrst.region_radiation.lower()
    assert "jaw" in opqrst.region_radiation.lower()
    assert "8" in opqrst.severity and "7" in opqrst.severity
    assert vitals.pain_score_0_to_10 == 7
    assert vitals.heart_rate_bpm >= 100
    assert vitals.respiratory_rate >= 20
    assert vitals.temperature_c < 37.5
    assert vitals.spo2_percent >= 94
    assert "158/94" == vitals.blood_pressure_mmhg
    assert "diaphoretic" in case.pe_findings.general.lower()
    assert "no" in case.pe_findings.musculoskeletal.palpation.lower()
    assert "tenderness" in case.pe_findings.musculoskeletal.palpation.lower()
    assert any("diaphoresis" in item.lower() for item in hx.associated_symptoms)
    assert any("nausea" in item.lower() for item in hx.associated_symptoms)
    assert any("tearing" in item.lower() for item in hx.pertinent_negatives)
    assert "smoking" in hx.social_history.tobacco.lower() or "smokes" in hx.social_history.tobacco.lower()
    assert case.hidden.final_diagnosis.lower().startswith("acute coronary")
    assert "diaphoresis" not in hx.history_of_present_illness.lower()
    assert "nause" not in hx.history_of_present_illness.lower()


def test_appendicitis_seed_is_clinically_coherent() -> None:
    case = load_case_from_path(SEED_CASES_DIR / "gi_acute_appendicitis.json")
    hx = case.clinical_history
    vitals = case.pe_findings.vitals
    opqrst = hx.opqrst
    abdomen = case.pe_findings.abdomen

    assert 15 <= case.patient_profile.age_years <= 40
    assert case.patient_profile.sex.value == "female"
    assert "18 hour" in opqrst.time_course.lower()
    assert "periumbilical" in opqrst.region_radiation.lower()
    assert "right lower" in opqrst.region_radiation.lower()
    assert "walking" in opqrst.provocation_palliation.lower()
    assert any(word in opqrst.quality.lower() for word in ("sharp", "constant"))
    assert "8" in opqrst.severity
    assert vitals.pain_score_0_to_10 == 8
    assert 37.5 <= vitals.temperature_c <= 38.5
    assert 90 <= vitals.heart_rate_bpm <= 110
    assert vitals.spo2_percent >= 97
    assert "mcburney" in abdomen.palpation.lower()
    assert "rovsing" in abdomen.palpation.lower()
    assert "rebound" in abdomen.peritoneal_signs.lower()
    assert "psoas" in case.pe_findings.musculoskeletal.special_tests.lower()
    assert any("anorexia" in item.lower() for item in hx.associated_symptoms)
    assert any("fever" in item.lower() for item in hx.associated_symptoms)
    assert any("dysuria" in item.lower() for item in hx.pertinent_negatives)
    assert any("menstrual" in item.lower() or "period" in item.lower() for item in hx.pertinent_negatives)
    assert case.hidden.final_diagnosis.lower() == "acute appendicitis"
    assert "anorexia" not in hx.history_of_present_illness.lower()
    assert "fever" not in hx.history_of_present_illness.lower()
