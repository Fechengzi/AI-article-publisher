from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.crud.user import get_user_by_email, get_user_by_username, create_user
from app.schemas.auth import UserCreate, UserRead, TokenResponse

router = APIRouter()
# 这个是验证 账号是否存在\要不就是验证新用户注册的输出的内容是否正确
# 感觉还是后者可能性偏大

# 在register里面的payload的数据输入的 UserCreate 有创造账户的标准
"""
    问题①:
        为什么要将填写的注意事项和检验分开来?
        猜测:①方便扩展 "注册所需要的内容" 如之后加上用xx快捷登录之类的?或者增加使用谷歌账号来登录
        猜测:②这样对于结构来说更加清晰, 且更加容易检查错误+解决报错(延伸:①是否说所有的函数都拆开检查报错就非常简单? 
        ②使用class+其他内容, 怎么让代码也好写? 这样导入来导入去是不是增加了复杂性,
        怎么克服这种"复杂性")
"""

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    if await get_user_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="该邮箱已被注册")
    if await get_user_by_username(db, payload.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="该用户名已被占用")
    user = await create_user(db, payload)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)

@router.get("/returntext", response_model=TokenResponse)
async def get_message(a : str):
    login()
    print(f"当前登录用户的信息:")
    
