import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import skill as skill_crud
from app.crud import article as article_crud
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillUpdate, SkillRead, SkillEvolveRequest, SkillEvolveDiff
from app.agents.skill_evolver import analyze_and_suggest

router = APIRouter()


@router.get("", response_model=list[SkillRead])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SkillRead]:
    return await skill_crud.list_skills(db, current_user.id)


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillRead:
    return await skill_crud.create_skill(db, payload, current_user.id)


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillRead:
    skill = await skill_crud.get_skill(db, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")
    return skill


@router.put("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillRead:
    skill = await skill_crud.get_skill(db, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")
    updated = await skill_crud.update_skill(db, skill_id, payload)
    return updated


@router.get("/{skill_id}/history", response_model=list[SkillRead])
async def get_skill_history(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SkillRead]:
    skill = await skill_crud.get_skill(db, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")
    return await skill_crud.get_skill_history(db, skill_id)


@router.post("/{skill_id}/evolve", response_model=SkillEvolveDiff)
async def evolve_skill(
    skill_id: uuid.UUID,
    payload: SkillEvolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillEvolveDiff:
    """
    手动触发 Agent③：分析高质量文章，返回 Skill 进化建议。
    返回 diff 后需调用 POST /skills/{id}/evolve/confirm 才真正写库。
    """
    skill = await skill_crud.get_skill(db, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")

    if payload.article_id:
        article = await article_crud.get_article(db, payload.article_id)
        if not article or article.user_id != current_user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if not article.body:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="文章内容为空")
        article_body = f"{article.title or ''}\n\n{article.body}"
    elif payload.external_content:
        article_body = payload.external_content
    else:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请提供 article_id 或 external_content",
        )

    return await analyze_and_suggest(skill.content, article_body)


@router.post("/{skill_id}/evolve/confirm", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def confirm_skill_evolution(
    skill_id: uuid.UUID,
    payload: SkillEvolveDiff,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillRead:
    """用户确认进化建议后，创建新版本 Skill"""
    skill = await skill_crud.get_skill(db, skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill 不存在")
    new_skill = await skill_crud.create_skill_version(db, skill, payload.new_content)
    return new_skill
