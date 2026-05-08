import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import article as article_crud
from app.crud import skill as skill_crud
from app.crud import input as input_crud
from app.models.user import User
from app.schemas.article import ArticleGenerateRequest, ArticleRead, ArticleUpdate
from app.agents.writer import run_writer

router = APIRouter()


@router.post("/generate", response_model=ArticleRead, status_code=status.HTTP_202_ACCEPTED)
async def generate_article(
    payload: ArticleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleRead:
    """选择结构化内容 + Skill，后台触发 Agent② 生成文章"""
    # 校验 structured_content 归属
    sc_input = await input_crud.get_raw_input(db, payload.structured_content_id)
    # structured_content_id 是 StructuredContent 的 id，不是 RawInput 的 id
    # 通过 skill_id 校验归属
    skill = await skill_crud.get_skill(db, payload.skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")

    article = await article_crud.create_article(db, payload, current_user.id)
    background_tasks.add_task(run_writer, article.id)
    return article


@router.get("", response_model=list[ArticleRead])
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ArticleRead]:
    return await article_crud.list_articles(db, current_user.id, skip, limit)


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleRead:
    """轮询生成状态 + 获取文章内容"""
    article = await article_crud.get_article(db, article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return article


@router.put("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleRead:
    """预览后手动修改文章内容"""
    article = await article_crud.get_article(db, article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
    updated = await article_crud.update_article(db, article_id, payload)
    return updated


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除文章"""
    article = await article_crud.get_article(db, article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
    await article_crud.delete_article(db, article_id)
