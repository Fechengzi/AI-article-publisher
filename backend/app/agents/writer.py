"""
Agent②：写作者
输入：结构化内容 + Skill 文档
输出：完整文章（标题 + 正文）
"""
import json
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.llm import chat_completion
from app.crud import article as article_crud
from app.models.article import ArticleStatus
from app.models.structured_content import StructuredContent
from app.models.skill import Skill

_SYSTEM_PROMPT_TEMPLATE = """\
你是一个专业的内容创作者。
你需要严格按照以下 Skill 文档的要求，将给定的结构化内容写成一篇完整的文章。

=== Skill 文档 ===
{skill_content}
=================

输出格式要求：
- 第一行：文章标题（不加任何前缀，纯文字）
- 第二行：空行
- 第三行起：文章正文
- 不要输出任何额外说明或前言
- 完全遵循 Skill 文档中的语气、结构、禁忌，将内容自然融入，不要机械列举\
"""


async def run_writer(article_id: uuid.UUID) -> None:
    """后台任务：根据结构化内容和 Skill 生成文章并写库"""
    async with AsyncSessionLocal() as db:
        try:
            await article_crud.update_article_status(
                db, article_id, ArticleStatus.GENERATING
            )
            await db.commit()

            article = await article_crud.get_article(db, article_id)
            if not article:
                return

            sc_result = await db.execute(
                select(StructuredContent).where(
                    StructuredContent.id == article.structured_content_id
                )
            )
            sc = sc_result.scalar_one_or_none()

            skill_result = await db.execute(
                select(Skill).where(Skill.id == article.skill_id)
            )
            skill = skill_result.scalar_one_or_none()

            if not sc or not skill:
                await article_crud.update_article_status(
                    db, article_id, ArticleStatus.FAILED, "找不到结构化内容或 Skill"
                )
                await db.commit()
                return

            system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(skill_content=skill.content)
            user_content = (
                "请基于以下结构化内容写作：\n\n"
                + json.dumps(sc.content, ensure_ascii=False, indent=2)
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
            response_text = await chat_completion(messages, temperature=0.7, max_tokens=4096)

            lines = response_text.strip().split("\n")
            # 跳过开头可能的空行，找第一个非空行作标题
            title = None
            body_start = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped:
                    title = stripped
                    body_start = i + 1
                    break
            # 跳过标题后的空行，取正文
            while body_start < len(lines) and not lines[body_start].strip():
                body_start += 1
            body = "\n".join(lines[body_start:]).strip() if body_start < len(lines) else ""

            await article_crud.update_article_status(
                db, article_id, ArticleStatus.DONE, title=title, body=body
            )
            await db.commit()

        except Exception as e:
            await article_crud.update_article_status(
                db, article_id, ArticleStatus.FAILED, str(e)
            )
            await db.commit()
