import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.models.raw_input import InputStatus


class RawInputCreate(BaseModel):
    content: str
    title: str | None = None


class StructuredContentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    raw_input_id: uuid.UUID
    content: dict[str, Any]
    created_at: datetime


class RawInputRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str | None = None
    content: str
    status: InputStatus
    error_msg: str | None = None
    created_at: datetime
    structured_content: StructuredContentRead | None = None
