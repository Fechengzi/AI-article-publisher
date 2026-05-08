from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 传统制造业就不够市场化
# 记住理论 能让1000个人给你付费, 你这杯子就不愁了
# 所以赚钱的根本在那里?
# 在于传播, 在于销售, 在于信任
# 而AI时其中最趁手好用的工具
# 
# 80年代靠什么赚钱 - 只靠倒卖就行
# 90年代靠什么赚钱 - 
# 持续不断的保持高水准工作, 虽说努力不会成功, 但是保持水准, 当机会真的来时, 让自己成为最有把握的那一个
# 不是有成功才保持高水准, 而是因为一直高水准所以才有一些机会成功
# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
