# 统一导入，alembic env.py 只需 from app.models import *
from app.models.user import User
from app.models.raw_input import RawInput, InputStatus
from app.models.structured_content import StructuredContent
from app.models.skill import Skill
from app.models.article import Article, ArticleStatus
from app.models.publication import Publication, Platform, PublicationStatus

__all__ = [
    "User",
    "RawInput",
    "InputStatus",
    "StructuredContent",
    "Skill",
    "Article",
    "ArticleStatus",
    "Publication",
    "Platform",
    "PublicationStatus",
]
