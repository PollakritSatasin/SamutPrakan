from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.session import TrainingSessionRecord
from app.schemas.case_schema import StudentCaseBriefing
from app.schemas.session_schema import (
    CompleteSessionRequest,
    CompletedSessionResponse,
    CreateSessionRequest,
    SessionStateSnapshot,
)
from app.services.case_loader import get_case_by_id
from app.services.prompt_builder import build_system_prompt
from app.services.state_manager import SESSION_COMPLETED, SessionManager, SessionState

router = APIRouter()


def get_session_manager(request: Request) -> SessionManager:
    manager = getattr(request.app.state, "session_manager", None)
    if manager is None:
        manager = SessionManager()
        request.app.state.session_manager = manager
    return manager


def _briefing_for(state: SessionState) -> StudentCaseBriefing:
    case = get_case_by_id(state.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{state.case_id}' not found")
    return case.to_student_briefing()


def _snapshot(state: SessionState) -> SessionStateSnapshot:
    return SessionStateSnapshot(
        session_id=state.session_id,
        case_id=state.case_id,
        status=state.status,  # type: ignore[arg-type]
        case=_briefing_for(state),
        rapport_score=state.rapport_score,
        distress_score=state.distress_score,
        turn_count=len(state.turns),
        created_at=state.created_at,
        completed_at=state.completed_at,
    )


@router.post("", response_model=SessionStateSnapshot, status_code=201)
def create_session(
    payload: CreateSessionRequest,
    db: Session = Depends(get_db),
    manager: SessionManager = Depends(get_session_manager),
) -> SessionStateSnapshot:
    """Start a new training session for a seed case."""
    case = get_case_by_id(payload.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{payload.case_id}' not found")

    distress = float(case.pe_findings.vitals.pain_score_0_to_10) * 10.0
    state = manager.create(
        case.case_id,
        rapport_score=50.0,
        distress_score=distress,
    )
    # Prime the engine prompt so later dialogue stays consistent with this snapshot.
    build_system_prompt(case, state)

    record = TrainingSessionRecord(
        id=state.session_id,
        case_id=state.case_id,
        status=state.status,
        transcript=[],
        disclosed_facts=[],
        created_at=state.created_at,
    )
    db.add(record)
    db.commit()
    return _snapshot(state)


@router.post("/{session_id}/complete", response_model=CompletedSessionResponse)
def complete_session(
    session_id: str,
    payload: CompleteSessionRequest = Body(default_factory=CompleteSessionRequest),
    db: Session = Depends(get_db),
    manager: SessionManager = Depends(get_session_manager),
) -> CompletedSessionResponse:
    """Finalize a session and persist the transcript."""
    state = manager.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    if state.status == SESSION_COMPLETED:
        raise HTTPException(status_code=409, detail=f"Session '{session_id}' is already completed")

    if payload.turns:
        state.replace_turns(payload.turns)

    try:
        completed = manager.complete(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    record = db.get(TrainingSessionRecord, session_id)
    transcript = [turn.model_dump(mode="json") for turn in completed.transcript()]
    facts = sorted(completed.disclosed_facts)
    if record is None:
        record = TrainingSessionRecord(
            id=completed.session_id,
            case_id=completed.case_id,
            status=completed.status,
            transcript=transcript,
            disclosed_facts=facts,
            created_at=completed.created_at,
            completed_at=completed.completed_at,
        )
        db.add(record)
    else:
        record.status = completed.status
        record.transcript = transcript
        record.disclosed_facts = facts
        record.completed_at = completed.completed_at or datetime.now(timezone.utc)
    db.commit()

    return CompletedSessionResponse(
        session_id=completed.session_id,
        case_id=completed.case_id,
        status="completed",
        case=_briefing_for(completed),
        transcript=completed.transcript(),
        disclosed_facts=facts,
        completed_at=completed.completed_at or datetime.now(timezone.utc),
    )
