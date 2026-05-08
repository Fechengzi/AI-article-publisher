import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.crud import input as input_crud
from app.models.user import User
from app.schemas.input import RawInputCreate, RawInputRead
from app.agents.organizer import run_organizer

router = APIRouter()

@router.post("", response_model=RawInputRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_text(
    payload: RawInputCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RawInputRead:
    """提交文字输入，后台异步触发 Agent① 整理"""
    raw_input = await input_crud.create_raw_input(db, payload, current_user.id)
    background_tasks.add_task(run_organizer, raw_input.id)
    return raw_input
# 

@router.post("/voice", response_model=RawInputRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_voice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RawInputRead:
    """上传音频，先用 Whisper 转文字，再走同一整理流程"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        audio_bytes = await file.read()
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(file.filename or "audio.m4a", audio_bytes, file.content_type or "audio/mpeg"),
        )
        text_content = transcription.text
    except Exception as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"语音转文字失败: {e}")

    raw_input = await input_crud.create_raw_input(
        db, RawInputCreate(content=text_content), current_user.id
    )
    background_tasks.add_task(run_organizer, raw_input.id)
    return raw_input


@router.get("", response_model=list[RawInputRead])
async def list_inputs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RawInputRead]:
    return await input_crud.list_raw_inputs(db, current_user.id, skip, limit)

# 那你为什么不直接进ark里面看剧情呢
@router.get("/{input_id}", response_model=RawInputRead)
async def get_input(
    input_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RawInputRead:
    """轮询处理状态 + 获取结构化结果"""
    raw_input = await input_crud.get_raw_input(db, input_id)
    if not raw_input or raw_input.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="输入不存在")
    return raw_input
