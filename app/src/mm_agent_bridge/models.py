from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mm_agent_bridge.db import Base


class IncomingMessage(Base):
    __tablename__ = "incoming_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source: Mapped[str] = mapped_column(
        String(32),
        server_default=text("'mattermost'"),
    )
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    channel_id: Mapped[str] = mapped_column(String(128), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent_tasks: Mapped[list["AgentTask"]] = relationship(back_populates="message")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("incoming_messages.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(
        String(32),
        server_default=text("'queued'"),
    )
    engine: Mapped[str] = mapped_column(
        String(64),
        server_default=text("'codex'"),
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped[IncomingMessage] = relationship(back_populates="agent_tasks")
