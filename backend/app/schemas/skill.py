import uuid
from datetime import datetime
from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    description: str | None = None
    content: str  # 实际的 Skill 风格说明文档


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content: str | None = None


class SkillRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    content: str
    version: int
    is_active: bool
    parent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SkillEvolveRequest(BaseModel):
    # 二选一：用自己库里的文章，或者直接粘贴外部文章全文
    article_id: uuid.UUID | None = None
    external_content: str | None = None


class SkillEvolveDiff(BaseModel):
    """Agent③ 返回的进化建议，需人工确认后才写库"""
    current_skill: str
    suggested_changes: str  # Markdown 格式，说明改了什么
    reasoning: str          # 为什么这篇文章好，能学到什么
    new_content: str        # 完整的新版 Skill 文档（确认后直接写库）
