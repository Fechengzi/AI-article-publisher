"""GitHub 发布模块 — 以 Gist 形式发布文章"""
import httpx
from app.core.config import settings


async def publish_gist(title: str, body: str, is_markdown: bool = True) -> str:
    """
    发布为 GitHub Gist，返回 Gist HTML URL。
    需在 .env 中配置 GITHUB_TOKEN（需要 gist 权限）。
    """
    if not settings.GITHUB_TOKEN:
        raise ValueError("未配置 GITHUB_TOKEN，请在 .env 中设置")

    filename = f"{title}.md" if is_markdown else f"{title}.txt"
    payload = {
        "description": title,
        "public": settings.GITHUB_GIST_PUBLIC,
        "files": {filename: {"content": body}},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.github.com/gists",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        resp.raise_for_status()
        return resp.json()["html_url"]
