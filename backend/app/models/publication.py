import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Platform(str, enum.Enum):
    GITHUB = "github"
    CSDN = "csdn"
    XHS = "xhs"


class PublicationStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    SUCCESS = "success"
    FAILED = "failed"


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False, index=True
    )
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus), default=PublicationStatus.PENDING, nullable=False
    )
    platform_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    article: Mapped["Article"] = relationship("Article", back_populates="publications")
