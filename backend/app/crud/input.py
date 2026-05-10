import uuid
from datetime import datetime, timezone
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.raw_input import RawInput, InputStatus
from app.models.structured_content import StructuredContent
from app.models.article import Article
from app.models.publication import Publication
from app.schemas.input import RawInputCreate


async def create_raw_input(
    db: AsyncSession, payload: RawInputCreate, user_id: uuid.UUID
) -> RawInput:
    title = payload.title.strip() if payload.title else None
    raw_input = RawInput(
        title=title or None,
        content=payload.content,
        user_id=user_id,
        status=InputStatus.PENDING,
    )
    db.add(raw_input)
    await db.flush()
    await db.refresh(raw_input)
    return raw_input


async def get_raw_input(db: AsyncSession, input_id: uuid.UUID) -> RawInput | None:
    result = await db.execute(
        select(RawInput)
        .where(RawInput.id == input_id)
        .options(selectinload(RawInput.structured_content))
    )
    return result.scalar_one_or_none()


async def list_raw_inputs(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> list[RawInput]:
    result = await db.execute(
        select(RawInput)
        .where(RawInput.user_id == user_id)
        .options(selectinload(RawInput.structured_content))
        .order_by(RawInput.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_input_status(
    db: AsyncSession,
    input_id: uuid.UUID,
    status: InputStatus,
    error_msg: str | None = None,
) -> None:
    await db.execute(
        update(RawInput)
        .where(RawInput.id == input_id)
        .values(
            status=status,
            error_msg=error_msg,
            updated_at=datetime.now(timezone.utc),
        )
    )


async def create_structured_content(
    db: AsyncSession, raw_input_id: uuid.UUID, content: dict
) -> StructuredContent:
    sc = StructuredContent(raw_input_id=raw_input_id, content=content)
    db.add(sc)
    await db.flush()
    await db.refresh(sc)
    return sc


async def delete_raw_input(db: AsyncSession, input_id: uuid.UUID) -> bool:
    """级联删除：原始输入 → 结构化内容 → 引用它的文章 → 文章的发布记录。"""
    raw = await get_raw_input(db, input_id)
    if not raw:
        return False

    if raw.structured_content is not None:
        sc_id = raw.structured_content.id
        # 找出引用此结构化内容的所有文章
        article_ids = (
            await db.execute(
                select(Article.id).where(Article.structured_content_id == sc_id)
            )
        ).scalars().all()
        if article_ids:
            # 先删发布记录
            await db.execute(
                delete(Publication).where(Publication.article_id.in_(article_ids))
            )
            # 再删文章
            await db.execute(delete(Article).where(Article.id.in_(article_ids)))
        # 删结构化内容
        await db.delete(raw.structured_content)

    await db.delete(raw)
    await db.flush()
    return True
