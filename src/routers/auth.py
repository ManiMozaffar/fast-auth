import asyncio
import time

from fastapi import APIRouter, Depends, Request, Response

from ..controllers.auth import AuthController
from ..core.database import DBManager, get_db
from ..core.redis.client import RedisManager, get_redis_db
from ..depends import get_current_user, get_current_user_from_db
from ..schema._in.user import UserIn
from ..schema.out.user import UserOut

router = APIRouter(
    prefix="/auth",
    tags=[
        "auth",
    ],
)


@router.post("/login")
async def login(
    data: UserIn,
    response: Response,
    db_session: DBManager = Depends(get_db),
    redis_db: RedisManager = Depends(get_redis_db),
):
    start_time = time.time()
    try:
        tokens = await AuthController(db_session=db_session, redis_session=redis_db).login(
            **data.dict()
        )
        elapsed_time = time.time() - start_time
        if elapsed_time < 1:
            await asyncio.sleep(1 - elapsed_time)
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time < 1:
            await asyncio.sleep(1 - elapsed_time)
        raise e from None

    response.set_cookie(
        key="Refresh-Token",
        value=tokens.refresh_token,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        key="Access-Token",
        value=tokens.access_token,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["X-CSRF-TOKEN"] = tokens.csrf_token


@router.post("/refresh")
async def refresh_token(
    response: Response,
    request: Request,
    db_session: DBManager = Depends(get_db),
    redis_db: RedisManager = Depends(get_redis_db),
    user_id: str = Depends(get_current_user),
):
    start_time = time.time()
    try:
        tokens = await AuthController(db_session=db_session, redis_session=redis_db).refresh_token(
            request.cookies.get("Refresh-Token", "")
        )
        elapsed_time = time.time() - start_time
        if elapsed_time < 1:
            await asyncio.sleep(1 - elapsed_time)
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time < 1:
            await asyncio.sleep(1 - elapsed_time)
        raise e from None

    response.set_cookie(
        key="Refresh-Token",
        value=tokens.refresh_token,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        key="Access-Token",
        value=tokens.access_token,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["X-CSRF-TOKEN"] = tokens.csrf_token
    return None


@router.post("/register")
async def register(data: UserIn, db_session: DBManager = Depends(get_db)) -> UserOut:
    return await AuthController(db_session=db_session).register(**data.dict())


@router.get("/me")
async def me(current_user: UserOut = Depends(get_current_user_from_db)) -> UserOut:
    return current_user


@router.delete("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: str = Depends(get_current_user),
    redis_db: RedisManager = Depends(get_redis_db),
):
    await AuthController(redis_db=redis_db, db_session=None).logout(  # type: ignore
        request.cookies.get("Refresh-Token", ""),  # type: ignore
    )
    response.set_cookie(
        key="Refresh-Token",
        value="",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        key="Access-Token",
        value="",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return None
