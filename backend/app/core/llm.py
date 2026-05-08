"""LLM 客户端工厂 — 统一接口，屏蔽 OpenAI / Anthropic 差异"""
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAYS = [2, 5, 10]  # 秒，指数退避


def _get_openai_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE
    )


def _get_anthropic_client():
    from anthropic import AsyncAnthropic
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def get_model_name() -> str:
    if settings.LLM_PROVIDER == "openai":
        return settings.OPENAI_MODEL
    return settings.ANTHROPIC_MODEL


async def chat_completion(messages: list[dict[str, str]], **kwargs) -> str:
    """
    统一的 LLM 调用入口，内置指数退避重试（最多 3 次）。
    messages: [{"role": "system/user/assistant", "content": "..."}]
    返回: 模型回复的纯文本字符串
    """
    model = get_model_name()
    last_err: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            if settings.LLM_PROVIDER == "openai":
                client = _get_openai_client()
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
                return response.choices[0].message.content or ""

            # Anthropic — system message 需单独传
            client = _get_anthropic_client()
            system_msg = next(
                (m["content"] for m in messages if m["role"] == "system"), None
            )
            user_msgs = [m for m in messages if m["role"] != "system"]
            create_kwargs: dict = {
                "model": model,
                "messages": user_msgs,
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            if system_msg:
                create_kwargs["system"] = system_msg
            response = await client.messages.create(**create_kwargs)
            return response.content[0].text

        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    "LLM 调用失败 (第 %d 次)，%d 秒后重试: %s",
                    attempt + 1, delay, e,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("LLM 调用失败 (已重试 %d 次): %s", _MAX_RETRIES, e)

    raise last_err  # type: ignore
