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
    user_repository = UserRepository()
    password_handler = PasswordHandler
    jwt_handler = JWTHandler

    def __init__(
        self,
        database: DBManager,
        redis: RedisManager | None = None,
        user_repository: UserRepository | None = None,
    ):
        self.user_repository = user_repository or self.user_repository
        self.database = database
        self.redis = redis

    async def register(self, password: str, username: str) -> UserOut:
        user_query = self.user_repository.get_by_username(username)
        async with self.database.begin() as session:
            user = await session.scalar(user_query)

        if user:
            raise BadRequestException("User already exists with this username")

        password = self.password_handler.hash(password)
        create_query = self.user_repository.create(
            password=password,
            username=username,
        )
        async with self.database.begin() as session:
            session.add(create_query)
            await session.flush()
            query = self.user_repository.query_by_username(username)
            user = (await session.execute(query)).first()

        if not user:
            raise BadRequestException("Weird error, please contact the administrator")

        return UserOut(**user._asdict())

    async def login(self, username: str, password: str) -> Token:
        if not self.redis:
            raise CustomException("Database connection is not initialized")

        find_user_query = self.user_repository.get_by_username(username)

        async with self.database.begin() as session:
            user = await session.scalar(find_user_query)

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
                "refresh_token": refresh_token,
                "access_token": access_token,
            }
        )
        await self.redis.set(
            name=refresh_token, value=user.id, ex=self.jwt_handler.refresh_token_expire
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )

    async def logout(self, user_id: str, refresh_token):
        refresh_payload = self.jwt_handler.decode(refresh_token)
        if not refresh_payload.get("verify") == user_id:
            raise BadRequestException

        if not self.redis:
            raise CustomException("Database connection is not initialized")

    async def me(self, user_id) -> UserOut:
        query = self.user_repository.query_by_id(user_id)
        async with self.database.begin() as session:
            user = (await session.execute(query)).first()
        if not user:
            raise BadRequestException("Invalid credentials")
        return UserOut(**user._asdict())

    async def refresh_token(self, old_refresh_token: str) -> Token:
        if not self.redis:
            raise CustomException("Database connection is not initialized")

        user_id, ttl = await asyncio.gather(
            self.redis.get(old_refresh_token), self.redis.ttl(old_refresh_token)
        )
        if not user_id or len(user_id) < 5:
            raise UnauthorizedException("Invalid refresh token")

        access_token = self.jwt_handler.encode(payload={"user_id": user_id})
        refresh_token = self.jwt_handler.encode_refresh_token(
            payload={"sub": "refresh_token", "verify": user_id}
        )
        csrf_token = self.jwt_handler.encode_refresh_token(
            payload={
                "sub": "csrf_token",
                "refresh_token": refresh_token,
                "access_token": access_token,
            }
        )
        await asyncio.gather(
            self.redis.set(refresh_token, user_id, ex=ttl),
            self.redis.delete(old_refresh_token),
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
