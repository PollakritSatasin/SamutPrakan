from __future__ import annotations

import uuid
from datetime import datetime, timezone
from threading import Lock

from app.schemas.session_schema import ConversationTurn

SESSION_ACTIVE = "active"
SESSION_COMPLETED = "completed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


class SessionState:
    """In-memory simulation state for one training encounter."""

    def __init__(
        self,
        case_id: str,
        *,
        session_id: str | None = None,
        rapport_score: float = 50.0,
        distress_score: float = 40.0,
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.case_id = case_id
        self.status: str = SESSION_ACTIVE
        self.turns: list[ConversationTurn] = []
        self.disclosed_facts: set[str] = set()
        self.rapport_score = clamp_score(rapport_score)
        self.distress_score = clamp_score(distress_score)
        self.created_at = _utcnow()
        self.completed_at: datetime | None = None

    def add_turn(
        self,
        role: str,
        content: str,
        *,
        disclosed_facts: list[str] | None = None,
        timestamp: datetime | None = None,
    ) -> ConversationTurn:
        if self.status != SESSION_ACTIVE:
            raise ValueError("Cannot add turns to a completed session")
        turn = ConversationTurn(
            role=role,  # type: ignore[arg-type]
            content=content,
            timestamp=timestamp or _utcnow(),
        )
        self.turns.append(turn)
        if role == "patient":
            self.disclose(content)
        if disclosed_facts:
            self.remember(*disclosed_facts)
        return turn

    def replace_turns(self, turns: list[ConversationTurn]) -> None:
        if self.status != SESSION_ACTIVE:
            raise ValueError("Cannot replace turns on a completed session")
        normalized: list[ConversationTurn] = []
        for turn in turns:
            normalized.append(
                ConversationTurn(
                    role=turn.role,
                    content=turn.content,
                    timestamp=turn.timestamp or _utcnow(),
                )
            )
            if turn.role == "patient":
                self.disclose(turn.content)
        self.turns = normalized

    def disclose(self, fact: str) -> bool:
        """Record a disclosed clinical fact. Returns True if it was new."""
        key = fact.strip()
        if not key:
            return False
        if key in self.disclosed_facts:
            return False
        self.disclosed_facts.add(key)
        return True

    def remember(self, *facts: str) -> None:
        """Persist one or more disclosed items in session memory."""
        for fact in facts:
            self.disclose(fact)

    def has_disclosed(self, fact: str) -> bool:
        return fact.strip() in self.disclosed_facts

    def locked_disclosures(self) -> list[str]:
        """Stable, sorted view of facts the patient must not contradict."""
        return sorted(self.disclosed_facts)

    def adjust_rapport(self, delta: float) -> float:
        self.rapport_score = clamp_score(self.rapport_score + delta)
        return self.rapport_score

    def adjust_distress(self, delta: float) -> float:
        self.distress_score = clamp_score(self.distress_score + delta)
        return self.distress_score

    def complete(self) -> None:
        if self.status == SESSION_COMPLETED:
            raise ValueError("Session is already completed")
        self.status = SESSION_COMPLETED
        self.completed_at = _utcnow()

    def transcript(self) -> list[ConversationTurn]:
        return list(self.turns)


class SessionManager:
    """Process-local registry of live SessionState objects."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

    def create(
        self,
        case_id: str,
        *,
        rapport_score: float = 50.0,
        distress_score: float = 40.0,
    ) -> SessionState:
        state = SessionState(
            case_id,
            rapport_score=rapport_score,
            distress_score=distress_score,
        )
        with self._lock:
            self._sessions[state.session_id] = state
        return state

    def get(self, session_id: str) -> SessionState | None:
        with self._lock:
            return self._sessions.get(session_id)

    def complete(self, session_id: str) -> SessionState:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                raise KeyError(session_id)
            state.complete()
            return state

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()
