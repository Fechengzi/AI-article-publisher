import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate


async def create_skill(
    db: AsyncSession, payload: SkillCreate, user_id: uuid.UUID
) -> Skill:
    skill = Skill(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        content=payload.content,
        version=1,
        is_active=True,
    )
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return skill


async def get_skill(db: AsyncSession, skill_id: uuid.UUID) -> Skill | None:
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    return result.scalar_one_or_none()


async def list_skills(db: AsyncSession, user_id: uuid.UUID) -> list[Skill]:
    result = await db.execute(
        select(Skill)
        .where(Skill.user_id == user_id)
        .order_by(Skill.created_at.desc())
    )
    return list(result.scalars().all())


async def get_skill_history(db: AsyncSession, skill_id: uuid.UUID) -> list[Skill]:
    """获取某个 Skill 的所有子版本（由它进化出来的版本）"""
    result = await db.execute(
        select(Skill)
        .where(Skill.parent_id == skill_id)
        .order_by(Skill.version.asc())
    )
    return list(result.scalars().all())


async def update_skill(
    db: AsyncSession, skill_id: uuid.UUID, payload: SkillUpdate
) -> Skill | None:
    skill = await get_skill(db, skill_id)
    if not skill:
        return None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(skill, k, v)
    skill.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(skill)
    return skill


async def create_skill_version(
    db: AsyncSession, parent_skill: Skill, new_content: str
) -> Skill:
    """创建新版本 Skill，并将旧版标记为 inactive"""
    # 停用旧版本
    await db.execute(
        update(Skill).where(Skill.id == parent_skill.id).values(is_active=False)
    )
    new_skill = Skill(
        user_id=parent_skill.user_id,
        name=parent_skill.name,
        description=parent_skill.description,
        content=new_content,
        version=parent_skill.version + 1,
        is_active=True,
        parent_id=parent_skill.id,
    )
    db.add(new_skill)
    await db.flush()
    await db.refresh(new_skill)
    return new_skill
