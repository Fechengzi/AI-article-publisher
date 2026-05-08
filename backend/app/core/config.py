from pathlib import Path
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8")

    # App
    APP_NAME: str = "AI Media Publisher"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # LLM — 可配置切换供应商
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"

    # Platform publish tokens（初版从 .env 读取，无需 UI 配置）
    GITHUB_TOKEN: str = ""
    GITHUB_GIST_PUBLIC: bool = False
    CSDN_API_KEY: str = ""
    XHS_COOKIES: str = ""  # JSON 字符串，格式: {"key": "value", ...}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
