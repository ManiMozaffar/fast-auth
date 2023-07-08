import asyncio

from fastapi import APIRouter, Depends, Request, Response

from ..controllers.auth import AuthController
from ..core.database import DBManager, get_db
from ..core.redis.client import RedisManager, get_redis_db
from ..depends import get_current_user, get_current_user_from_db
from ..schema._in.user import UserIn
from ..schema.out.auth import RefreshToken
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
    tokens, _ = await asyncio.gather(
        AuthController(db_session, redis_db, None).login(**data.dict()), asyncio.sleep(1)
    )
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
    tokens, _ = await asyncio.gather(
        AuthController(db_session, redis_db, None).refresh_token(
            request.cookies.get("Refresh-Token", "")
        ),
        asyncio.sleep(1),
    )
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


@router.post("/register")
async def register(data: UserIn, db_session: DBManager = Depends(get_db)) -> UserOut:
    return await AuthController(db_session, None).register(**data.dict())


@router.get("/me")
async def me(current_user: UserOut = Depends(get_current_user_from_db)) -> UserOut:
    return current_user


@router.post("/logout")
async def logout(
    data: RefreshToken,
    current_user: UserOut = Depends(get_current_user),
    redis_db: RedisManager = Depends(get_redis_db),
):
    return await AuthController(None, redis_db).logout(  # type: ignore
        current_user,
        **data.dict(),  # type: ignore
    )
