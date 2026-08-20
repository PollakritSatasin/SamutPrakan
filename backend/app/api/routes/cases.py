from fastapi import APIRouter, HTTPException

from app.schemas.case_schema import ClinicalCase, StudentCaseBriefing
from app.services.case_loader import get_case_by_id, load_all_seed_cases

router = APIRouter()


@router.get("", response_model=list[StudentCaseBriefing])
def list_cases() -> list[StudentCaseBriefing]:
    """Student-visible metadata only: title, chief complaint, setting."""
    return [case.to_student_briefing() for case in load_all_seed_cases()]


@router.get("/{case_id}/faculty", response_model=ClinicalCase, include_in_schema=False)
def get_faculty_case(case_id: str) -> ClinicalCase:
    """Full case including hidden truths. Not for student clients."""
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    return case


@router.get("/{case_id}", response_model=StudentCaseBriefing)
def get_case(case_id: str) -> StudentCaseBriefing:
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    return case.to_student_briefing()
