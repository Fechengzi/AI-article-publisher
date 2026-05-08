import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.publication import Publication, Platform, PublicationStatus


async def create_publication(
    db: AsyncSession, article_id: uuid.UUID, platform: Platform
) -> Publication:
    pub = Publication(
        article_id=article_id,
        platform=platform,
        status=PublicationStatus.PENDING,
    )
    db.add(pub)
    await db.flush()
    await db.refresh(pub)
    return pub


async def get_publications_by_article(
    db: AsyncSession, article_id: uuid.UUID
) -> list[Publication]:
    result = await db.execute(
        select(Publication)
        .where(Publication.article_id == article_id)
        .order_by(Publication.created_at.desc())
    )
    return list(result.scalars().all())


async def update_publication_status(
    db: AsyncSession,
    publication_id: uuid.UUID,
    status: PublicationStatus,
    platform_url: str | None = None,
    error_msg: str | None = None,
) -> None:
    values: dict = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if platform_url is not None:
        values["platform_url"] = platform_url
    if error_msg is not None:
        values["error_msg"] = error_msg
    await db.execute(
        update(Publication).where(Publication.id == publication_id).values(**values)
    )
