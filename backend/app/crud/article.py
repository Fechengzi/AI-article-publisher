import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.article import Article, ArticleStatus
from app.schemas.article import ArticleGenerateRequest, ArticleUpdate


async def create_article(
    db: AsyncSession, payload: ArticleGenerateRequest, user_id: uuid.UUID
) -> Article:
    article = Article(
        user_id=user_id,
        structured_content_id=payload.structured_content_id,
        skill_id=payload.skill_id,
        status=ArticleStatus.PENDING,
    )
    db.add(article)
    await db.flush()
    await db.refresh(article)
    return article


async def get_article(db: AsyncSession, article_id: uuid.UUID) -> Article | None:
    result = await db.execute(select(Article).where(Article.id == article_id))
    return result.scalar_one_or_none()


async def list_articles(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> list[Article]:
    result = await db.execute(
        select(Article)
        .where(Article.user_id == user_id)
        .order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_article_status(
    db: AsyncSession,
    article_id: uuid.UUID,
    status: ArticleStatus,
    title: str | None = None,
    body: str | None = None,
    error_msg: str | None = None,
) -> None:
    values: dict = {
        "status": status,
        "error_msg": error_msg,
        "updated_at": datetime.now(timezone.utc),
    }
    if title is not None:
        values["title"] = title
    if body is not None:
        values["body"] = body
    await db.execute(update(Article).where(Article.id == article_id).values(**values))


async def update_article(
    db: AsyncSession, article_id: uuid.UUID, payload: ArticleUpdate
) -> Article | None:
    article = await get_article(db, article_id)
    if not article:
        return None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(article, k, v)
    article.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(article)
    return article


async def delete_article(db: AsyncSession, article_id: uuid.UUID) -> bool:
    article = await get_article(db, article_id)
    if not article:
        return False
    await db.delete(article)
    await db.flush()
    return True
