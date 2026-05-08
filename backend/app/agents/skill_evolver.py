"""
Agent③：Skill 进化者
触发方式：用户手动按需触发（不自动执行）
输入：当前 Skill + 一篇高质量文章
输出：进化建议 diff（人工 review 后才写库）
"""
import json
from app.core.llm import chat_completion
from app.schemas.skill import SkillEvolveDiff

_SYSTEM_PROMPT = """\
你是一个写作风格分析专家。
你会收到一份「当前 Skill 文档」和一篇「高质量文章」。

你的任务：
1. 分析这篇高质量文章的写作特点（语气、结构、用词、节奏、开头方式、结尾方式等）
2. 对比当前 Skill 文档，找出哪些地方可以改进或补充
3. 输出完整的改进后 Skill 文档

请严格按照以下 JSON 格式输出，不要输出任何额外文字或代码块标记：
{
  "suggested_changes": "建议修改的内容说明（Markdown 格式，清晰列出改了什么、为什么改）",
  "reasoning": "这篇文章好在哪里，从中可以学到什么写作技巧",
  "new_content": "改进后的完整 Skill 文档（直接可用的文本，保留原有结构）"
}\
"""


async def analyze_and_suggest(
    current_skill_content: str,
    article_body: str,
) -> SkillEvolveDiff:
    """
    分析高质量文章，返回 Skill 进化建议。
    结果需人工确认后才调用 crud.skill.create_skill_version 写库。
    """
    user_content = (
        f"=== 当前 Skill 文档 ===\n{current_skill_content}\n\n"
        f"=== 高质量文章 ===\n{article_body}"
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    response_text = await chat_completion(messages, temperature=0.4)

    clean = response_text.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(clean)

    return SkillEvolveDiff(
        current_skill=current_skill_content,
        suggested_changes=data["suggested_changes"],
        reasoning=data["reasoning"],
        new_content=data["new_content"],
    )
