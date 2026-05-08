from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import PlatformSettingsRead

router = APIRouter()


@router.get("", response_model=PlatformSettingsRead)
async def get_platform_settings(
    current_user: User = Depends(get_current_user),
) -> PlatformSettingsRead:
    """查看各平台是否已配置（只返回布尔值，不暴露密钥）"""
    return PlatformSettingsRead(
        github_configured=bool(settings.GITHUB_TOKEN),
        csdn_configured=bool(settings.CSDN_API_KEY),
        xhs_configured=bool(settings.XHS_COOKIES),
    )
