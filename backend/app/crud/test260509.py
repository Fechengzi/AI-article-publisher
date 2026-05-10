import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import hash_password

# async def get_reload_news(db: AsyncSession, news_id = int, category_id:int, limlm: int = 5):
    # # order_by 排序 -> 浏览器于发布时间
    # stmt = select(News).where(
    #     News.category
    #     News.id != news_id
    # ).order_by(
    #     News.views.desc() # 默认是升序,desc表示降序
    #     News.publish_time.desc()
    # ).limit(limit)
    # result = await db.execute(stmt)
    # return result.scalars().all()
    

# async def increase_news(db:AsyncSession, news_id:int):
#     stmt = update(News).where(News.id == news_id).values(views:News.views + 1)
#     await db.execute(stmt)
#     await db.commit()
# # 增加浏览器方法

