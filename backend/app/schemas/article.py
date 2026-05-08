import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.article import ArticleStatus


class ArticleGenerateRequest(BaseModel):
    structured_content_id: uuid.UUID
    skill_id: uuid.UUID


class ArticleUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    is_markdown: bool | None = None


class ArticleRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    structured_content_id: uuid.UUID
    skill_id: uuid.UUID
    title: str | None
    body: str | None
    status: ArticleStatus
    error_msg: str | None
    is_markdown: bool
    created_at: datetime
    updated_at: datetime
