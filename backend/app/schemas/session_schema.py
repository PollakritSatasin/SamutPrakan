from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case_schema import StudentCaseBriefing


class ConversationTurn(BaseModel):
    """One student or patient utterance in the encounter."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["student", "patient"]
    content: str = Field(..., min_length=1)
    timestamp: datetime | None = None


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)


class SessionStateSnapshot(BaseModel):
    """Student-safe live session view. Does not include the system prompt."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    case_id: str
    status: Literal["active", "completed"]
    case: StudentCaseBriefing
    rapport_score: float = Field(..., ge=0, le=100)
    distress_score: float = Field(..., ge=0, le=100)
    turn_count: int = Field(..., ge=0)
    created_at: datetime
    completed_at: datetime | None = None


class CompleteSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turns: list[ConversationTurn] = Field(default_factory=list)


class CompletedSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    case_id: str
    status: Literal["completed"]
    case: StudentCaseBriefing
    transcript: list[ConversationTurn]
    disclosed_facts: list[str]
    completed_at: datetime
