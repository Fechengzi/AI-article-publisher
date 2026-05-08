"""
Agent①：整理者
输入：原始混乱文字（口语/语音转录）
输出：结构化 JSON → {viewpoints, arguments, extensions, actions}
"""
import json
import re
import uuid
from app.core.database import AsyncSessionLocal
from app.core.llm import chat_completion
from app.crud import input as input_crud
from app.models.raw_input import InputStatus

_SYSTEM_PROMPT = """\
你是一个专业的内容整理专家。用户会给你输入一段混乱的、口语化的文字（类似语音转录），\
你需要从中提炼出结构化内容。

请严格按照以下 JSON 格式输出，不要输出任何额外文字或代码块标记：
{
  "viewpoints": ["核心观点1", "核心观点2"],
  "arguments": {
    "核心观点1": ["支撑论据1", "支撑论据2"],
    "核心观点2": ["支撑论据1"]
  },
  "extensions": ["延伸思考1", "延伸思考2"],
  "actions": ["我应该做的事1", "我应该做的事2"]
}

规则：
- viewpoints：提炼 1-5 个核心观点，每条一句话
- arguments：每个观点对应的支撑材料、例子、数据
- extensions：基于这些观点可以延伸的思考方向
- actions：作者自己应该采取的具体行动
- 如果某个字段没有对应内容，返回空数组/对象
- 必须是合法 JSON，不要加 ```json 标记\
"""


async def run_organizer(raw_input_id: uuid.UUID) -> None:
    """后台任务：处理原始输入，生成结构化内容并写库"""
    async with AsyncSessionLocal() as db:
        try:
            await input_crud.update_input_status(db, raw_input_id, InputStatus.PROCESSING)
            await db.commit()

            raw_input = await input_crud.get_raw_input(db, raw_input_id)
            if not raw_input:
                return

            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": raw_input.content},
            ]
            response_text = await chat_completion(messages, temperature=0.3)

            # 宽容解析：先去代码块标记，再提取第一个 {...} 块
            clean = response_text.strip()
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
            clean = clean.strip()

            # 若模型在 JSON 前后还有多余文字，提取最外层花括号内容
            m = re.search(r"\{[\s\S]*\}", clean)
            if m:
                clean = m.group(0)

            try:
                structured_data = json.loads(clean)
            except json.JSONDecodeError:
                # 最后兜底：尝试去掉行尾注释后再解析
                clean_no_comment = re.sub(r"//[^\n]*", "", clean)
                structured_data = json.loads(clean_no_comment)

            # 确保必要字段存在
            structured_data.setdefault("viewpoints", [])
            structured_data.setdefault("arguments", {})
            structured_data.setdefault("extensions", [])
            structured_data.setdefault("actions", [])

            await input_crud.create_structured_content(db, raw_input_id, structured_data)
            await input_crud.update_input_status(db, raw_input_id, InputStatus.DONE)
            await db.commit()

        except json.JSONDecodeError as e:
            await input_crud.update_input_status(
                db, raw_input_id, InputStatus.FAILED, f"解析 JSON 失败: {e}"
            )
            await db.commit()
        except Exception as e:
            await input_crud.update_input_status(
                db, raw_input_id, InputStatus.FAILED, str(e)
            )
            await db.commit()
