from fastapi import APIRouter
from app.api.v1.endpoints import auth, inputs, skills, articles, publish, platform_settings

router = APIRouter()

router.include_router(auth.router,             prefix="/auth",     tags=["auth"])
router.include_router(inputs.router,           prefix="/inputs",   tags=["inputs"])
router.include_router(skills.router,           prefix="/skills",   tags=["skills"])
router.include_router(articles.router,         prefix="/articles", tags=["articles"])
router.include_router(publish.router,          prefix="/articles", tags=["publish"])
router.include_router(platform_settings.router, prefix="/settings/platforms", tags=["settings"])
