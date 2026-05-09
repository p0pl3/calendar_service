from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, String, Text, text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.types import StringListType


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    event_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False, index=True)
    remind_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    channels: Mapped[list] = mapped_column(StringListType(), nullable=False, default=lambda: ["email"])
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["Event"] = relationship("Event", back_populates="reminders")  # noqa: F821
