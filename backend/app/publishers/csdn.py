"""CSDN 发布模块 — 通过 CSDN 官方博客 API 发布文章"""
import httpx
from app.core.config import settings

_API_BASE = "https://bizapi.csdn.net/blog-console-api/v3"


async def publish_article(title: str, body: str, is_markdown: bool = True) -> str:
    """
    发布文章到 CSDN，返回文章 URL。
    需在 .env 中配置 CSDN_API_KEY（从 CSDN 开发者后台申请）。
    """
    if not settings.CSDN_API_KEY:
        raise ValueError("未配置 CSDN_API_KEY，请在 .env 中设置")

    payload = {
        "title": title,
        "markdowncontent": body if is_markdown else "",
        "content": body,
        "type": "original",
        "status": 0,       # 0 = 立即发布，1 = 草稿
        "categories": "",
        "tags": "",
        "read_type": "public",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_API_BASE}/mdeditor/saveArticle",
            json=payload,
            headers={
                "x-ca-key": settings.CSDN_API_KEY,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        article_id = data.get("data", {}).get("id", "")
        return f"https://blog.csdn.net/article/details/{article_id}"
