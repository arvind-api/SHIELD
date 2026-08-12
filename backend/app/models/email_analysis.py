from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailAnalysis(Base):
    __tablename__ = "email_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    raw_email: Mapped[str] = mapped_column(Text, nullable=False)
    # Stored as JSON text (tone/intent, phishing signals, reply suggestion, etc.)
    # so the response shape can evolve without a migration. Revisit for Postgres JSONB later.
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
