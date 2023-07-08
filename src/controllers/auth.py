import asyncio

from ..core.database import DBManager
from ..core.exceptions import BadRequestException, CustomException, UnauthorizedException
from ..core.redis.client import RedisManager
from ..repository.jwt import JWTHandler
from ..repository.password import PasswordHandler
from ..repository.users import UserRepository
from ..schema.out.auth import Token
from ..schema.out.user import UserOut


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

    async def register(self, password: str, username: str) -> UserOut:
        user = await self.user_adaptor.get_by_username(username, db_session=self.db_session)

        if user:
            raise BadRequestException("User already exists with this username")

        password = self.password_handler.hash(password)
        user = await self.user_adaptor.get_and_create(
            username=username, password=password, db_session=self.db_session
        )

        if not user:
            raise BadRequestException("Weird error, please contact the administrator")

        return UserOut(**user._asdict())

    async def login(self, username: str, password: str) -> Token:
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")

        user = await self.user_adaptor.get_by_username(username, db_session=self.db_session)
        if (not user) or (not self.password_handler.verify(user.password, password)):
            raise BadRequestException("Invalid credentials")

        refresh_token = self.jwt_handler.encode_refresh_token(
            payload={"sub": "refresh_token", "verify": str(user.id)}
        )
        access_token = self.jwt_handler.encode(
            payload={"sub": "access_token", "user_id": str(user.id)}
        )
        csrf_token = self.jwt_handler.encode_refresh_token(
            payload={
                "sub": "csrf_token",
                "refresh_token": str(refresh_token),
                "access_token": str(access_token),
            }
        )
        await self.redis_session.set(
            name=refresh_token, value=user.id, ex=self.jwt_handler.refresh_token_expire
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )

    async def logout(self, refresh_token):
        if not refresh_token:
            raise BadRequestException
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")
        await self.redis_session.delete(refresh_token)

    async def me(self, user_id) -> UserOut:
        user = await self.user_adaptor.query_by_id(user_id, db_session=self.db_session)
        if not user:
            raise BadRequestException("Invalid credentials")
        return UserOut(**user._asdict())

    async def refresh_token(self, old_refresh_token: str) -> Token:
        if not self.redis_session:
            raise CustomException("Database connection is not initialized")

        user_id, ttl = await asyncio.gather(
            self.redis_session.get(old_refresh_token), self.redis_session.ttl(old_refresh_token)
        )
        if not user_id or len(str(user_id)) < 5:
            raise UnauthorizedException("Invalid refresh token")

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
