import asyncio
import base64
import io

import qrcode
from pyotp import random_base32, totp

from src.core.config import settings

from ..core.database import DBManager
from ..core.exceptions import BadRequestException, CustomException, UnauthorizedException
from ..core.redis.client import RedisManager
from ..repository.jwt import JWTHandler
from ..repository.password import PasswordHandler
from ..repository.users import UserRepository
from ..schema.out.auth import Token
from ..schema.out.user import UserOut, UserOutRegister


class AuthController:
    user_adaptor = UserRepository()
    password_handler = PasswordHandler
    jwt_handler = JWTHandler

    def __init__(
        self,
        db_session: DBManager,
        redis_session: RedisManager | None = None,
        user_adaptor: UserRepository | None = None,
    ):
        self.user_adaptor = user_adaptor or self.user_adaptor
        self.db_session = db_session
        self.redis_session = redis_session

    async def register(self, password: str, username: str) -> UserOutRegister:
        user = await self.user_adaptor.get_by_username(username, db_session=self.db_session)

        if user:
            raise BadRequestException("User already exists with this username")

        password = self.password_handler.hash(password)
        user = await self.user_adaptor.get_and_create(
            username=username,
            password=password,
            gauth=str(random_base32()),
            db_session=self.db_session,
        )
        assert user is not None
        provisioning_uri = totp.TOTP(user.gauth).provisioning_uri()
        buffered = io.BytesIO()
        qrcode.make(provisioning_uri).save(buffered)
        return UserOutRegister(
            username=user.username,
            updated_at=user.updated_at,
            created_at=user.created_at,
            gauth=user.gauth,
            qr_img=base64.b64encode(buffered.getvalue()).decode(),
        )

    async def login(self, username: str, password: str) -> Token:
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")

        user = await self.user_adaptor.get_by_username(username, db_session=self.db_session)
        print(user)
        if (not user) or (not self.password_handler.verify(user.password, password)):
            raise BadRequestException("Invalid credentials")

        refresh_token = self.jwt_handler.encode_refresh_token(
            payload={"sub": "refresh_token", "verify": str(user.id)}
        )
        csrf_token = self.jwt_handler.encode_refresh_token(
            payload={
                "sub": "csrf_token",
                "refresh_token": str(refresh_token),
            }
        )
        await self.redis_session.set(
            name=refresh_token, value=user.id, ex=self.jwt_handler.refresh_token_expire
        )
        return Token(
            access_token=None,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )

    async def logout(self, refresh_token) -> None:
        if not refresh_token:
            raise BadRequestException
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")
        await self.redis_session.delete(refresh_token)
        return None

    async def me(self, user_id) -> UserOut:
        user = await self.user_adaptor.query_by_id(user_id, db_session=self.db_session)
        if not user:
            raise BadRequestException("Invalid credentials")
        return UserOut(
            username=user.username, updated_at=user.updated_at, created_at=user.created_at
        )

    async def verify(
        self,
        refresh_token: str,
        session_id: str,
        code: str,
        settings=settings,
    ) -> None:
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")
        session_id_redis, user_id = await asyncio.gather(
            self.redis_session.get(session_id), self.redis_session.get(refresh_token)
        )
        if not user_id or len(str(user_id)) < 5:
            raise UnauthorizedException("Invalid Refresh Token")
        elif session_id_redis != user_id:
            user = await self.user_adaptor.query_by_id(user_id, db_session=self.db_session)
            assert user is not None
            if not totp.TOTP(user.gauth).verify(code):
                raise BadRequestException("Invalid Code")
            print(user_id)
            await self.redis_session.set(
                session_id, value=user_id, ex=(settings.SESSION_EXPIRE_MINUTES) * 60
            )
        else:
            raise BadRequestException("Already Verified")
        return None

    async def refresh_token(self, old_refresh_token: str, session_id: str) -> Token:
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")

        user_id, ttl, session_id = await asyncio.gather(
            self.redis_session.get(old_refresh_token),
            self.redis_session.ttl(old_refresh_token),
            self.redis_session.get(session_id),
        )
        if not user_id or len(str(user_id)) < 5:
            raise UnauthorizedException("Invalid Refresh Token")

        if session_id != user_id:
            raise UnauthorizedException("Please verify using 2 step authenication first")

        access_token = self.jwt_handler.encode(payload={"user_id": str(user_id)})
        refresh_token = self.jwt_handler.encode_refresh_token(
            payload={"sub": "refresh_token", "verify": str(user_id)}
        )
        csrf_token = self.jwt_handler.encode_refresh_token(
            payload={
                "sub": "csrf_token",
                "refresh_token": str(refresh_token),
                "access_token": str(access_token),
            }
        )
        await asyncio.gather(
            self.redis_session.set(refresh_token, user_id, ex=ttl),
            self.redis_session.delete(old_refresh_token),
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
