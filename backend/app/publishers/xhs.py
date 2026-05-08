"""
小红书发布模块
依赖开源库：pip install xhs
注意：无官方 API，基于逆向工程，可能随版本更新失效。
"""
import asyncio
import json
from app.core.config import settings


async def publish_note(title: str, body: str) -> str:
    """
    发布图文笔记到小红书，返回笔记 URL。
    需在 .env 中配置 XHS_COOKIES（JSON 字符串格式）。
    """
    try:
        from xhs import XhsClient
    except ImportError:
        raise RuntimeError("xhs 库未安装，请执行: pip install xhs")

    if not settings.XHS_COOKIES:
        raise ValueError("未配置 XHS_COOKIES，请在 .env 中设置")

    cookies: dict = json.loads(settings.XHS_COOKIES)
    client = XhsClient(cookie="; ".join(f"{k}={v}" for k, v in cookies.items()))

    # xhs 库为同步操作，用 asyncio.to_thread 避免阻塞事件循环
    def _publish() -> dict:
        return client.create_simple_note(title=title, desc=body, imgs=[])

    result = await asyncio.to_thread(_publish)
    note_id = result.get("id", "")
    return f"https://www.xiaohongshu.com/explore/{note_id}"
