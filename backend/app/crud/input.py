import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.raw_input import RawInput, InputStatus
from app.models.structured_content import StructuredContent
from app.schemas.input import RawInputCreate


async def create_raw_input(
    db: AsyncSession, payload: RawInputCreate, user_id: uuid.UUID
) -> RawInput:
    raw_input = RawInput(
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
