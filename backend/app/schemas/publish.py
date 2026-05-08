import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.publication import Platform, PublicationStatus


class PublishRequest(BaseModel):
    platforms: list[Platform]


class PublicationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    article_id: uuid.UUID
    platform: Platform
    status: PublicationStatus
    platform_url: str | None
    error_msg: str | None
    created_at: datetime
    updated_at: datetime
