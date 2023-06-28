from fastapi import APIRouter, Depends

from ..controllers.auth import AuthController
from ..core.database import DBManager, get_db
from ..core.redis.client import RedisManager, get_redis_db
from ..depends import get_current_user, get_current_user_from_db
from ..schema._in.user import UserIn
from ..schema.out.auth import RefreshToken, Token
from ..schema.out.user import UserOut

router = APIRouter(
    prefix="/auth",
    tags=[
        "auth",
    ],
)


@router.post("/login", response_model=Token)
async def login(
    data: UserIn,
    db_session: DBManager = Depends(get_db),
    redis_db: RedisManager = Depends(get_redis_db)
):
    return await AuthController(db_session, redis_db, None).login(**data.dict())


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: RefreshToken,
    db_session: DBManager = Depends(get_db),
    redis_db: RedisManager = Depends(get_redis_db)
):
    return await AuthController(db_session, redis_db, None).refresh_token(**data.dict())


@router.post("/register", response_model=UserOut)
async def register(data: UserIn, db_session: DBManager = Depends(get_db)):
    return await AuthController(db_session, None).register(**data.dict())


@router.get("/me", response_model=UserOut)
async def me(current_user: UserOut = Depends(get_current_user_from_db)):
    return current_user


@router.post("/logout")
async def logout(
    data: RefreshToken,
    current_user: UserOut = Depends(get_current_user),
    redis_db: RedisManager = Depends(get_redis_db),
):
    return await AuthController(None, redis_db).logout(  # type: ignore
        current_user, **data.dict(),  # type: ignore
    )
