from functools import lru_cache
from pathlib import Path

from app.schemas.case_schema import CaseSchema, ClinicalCase

SEED_CASES_DIR = Path(__file__).resolve().parents[2] / "data" / "seed_cases"


def load_case_from_path(path: Path) -> ClinicalCase:
    """Validate a JSON case file against the Pydantic v2 CaseSchema."""
    return CaseSchema.model_validate_json(path.read_text(encoding="utf-8"))


@lru_cache
def load_all_seed_cases() -> tuple[ClinicalCase, ...]:
    if not SEED_CASES_DIR.exists():
        return ()
    cases = [
        load_case_from_path(path)
        for path in sorted(SEED_CASES_DIR.glob("*.json"))
    ]
    return tuple(cases)


def get_case_by_id(case_id: str) -> ClinicalCase | None:
    for case in load_all_seed_cases():
        if case.case_id == case_id:
            return case
    return None
