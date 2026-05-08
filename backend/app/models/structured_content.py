import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StructuredContent(Base):
    __tablename__ = "structured_contents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 1:1 关联 raw_input（unique 约束确保每条输入只整理一次）
    raw_input_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_inputs.id"), unique=True, nullable=False
    )
    # JSONB 存储结构化内容: {viewpoints, arguments, extensions, actions}
    content: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    raw_input: Mapped["RawInput"] = relationship(  # noqa: F821
        "RawInput", back_populates="structured_content"
    )
    articles: Mapped[list["Article"]] = relationship(  # noqa: F821
        "Article", back_populates="structured_content"
    )
