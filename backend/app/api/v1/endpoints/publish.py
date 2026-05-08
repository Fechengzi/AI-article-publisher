import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db, AsyncSessionLocal
from app.crud import article as article_crud
from app.crud import publication as pub_crud
from app.models.user import User
from app.models.publication import Platform, PublicationStatus
from app.schemas.publish import PublishRequest, PublicationRead

router = APIRouter()


async def _do_publish(publication_id: uuid.UUID, article_id: uuid.UUID, platform: Platform) -> None:
    """后台发布任务：调用对应平台接口并更新状态"""
    async with AsyncSessionLocal() as db:
        try:
            await pub_crud.update_publication_status(db, publication_id, PublicationStatus.PUBLISHING)
            await db.commit()

            article = await article_crud.get_article(db, article_id)
            if not article or not article.body:
                raise ValueError("文章内容为空，无法发布")

            title = article.title or "无标题"
            body = article.body

            if platform == Platform.GITHUB:
                from app.publishers.github import publish_gist
                url = await publish_gist(title, body, article.is_markdown)

            elif platform == Platform.CSDN:
                from app.publishers.csdn import publish_article
                url = await publish_article(title, body, article.is_markdown)

            elif platform == Platform.XHS:
                # 小红书不支持 Markdown，统一去掉格式符
                from app.publishers.xhs import publish_note
                plain_body = body.replace("#", "").replace("*", "").replace("`", "")
                url = await publish_note(title, plain_body)

            else:
                raise ValueError(f"不支持的平台: {platform}")

            await pub_crud.update_publication_status(
                db, publication_id, PublicationStatus.SUCCESS, platform_url=url
            )
            await db.commit()

        except Exception as e:
            await pub_crud.update_publication_status(
                db, publication_id, PublicationStatus.FAILED, error_msg=str(e)
            )
            await db.commit()


@router.post("/{article_id}/publish", response_model=list[PublicationRead], status_code=status.HTTP_202_ACCEPTED)
async def publish_article(
    article_id: uuid.UUID,
    payload: PublishRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PublicationRead]:
    """向指定平台列表发布文章，每个平台创建一条发布记录并后台执行"""
    article = await article_crud.get_article(db, article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if article.status.value != "done":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="文章尚未生成完成")

    publications = []
    for platform in payload.platforms:
        pub = await pub_crud.create_publication(db, article_id, platform)
        background_tasks.add_task(_do_publish, pub.id, article_id, platform)
        publications.append(pub)

    return publications


@router.get("/{article_id}/publications", response_model=list[PublicationRead])
async def get_publications(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PublicationRead]:
    """查看文章各平台的发布状态和 URL"""
    article = await article_crud.get_article(db, article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return await pub_crud.get_publications_by_article(db, article_id)
