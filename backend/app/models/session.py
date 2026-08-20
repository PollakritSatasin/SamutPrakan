import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrainingSessionRecord(Base):
    """Persisted training session and finalized transcript."""

    __tablename__ = "training_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    disclosed_facts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
