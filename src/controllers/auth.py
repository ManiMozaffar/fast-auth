import asyncio

from ..core.database import DBManager
from ..core.exceptions import (BadRequestException, CustomException,
                               UnauthorizedException)
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

        initial_amount: None | int = await self.redis.get(name=user.id)
        if not initial_amount:
            initial_amount = 0
        else:
            initial_amount = int(initial_amount)

        if initial_amount > 15:
            raise BadRequestException("Too many login attempts recently, please retry in 24hours")

        refresh_token = self.jwt_handler.encode_refresh_token(payload={
            "sub": "refresh_token", "verify": str(user.id)
        })

        await asyncio.gather(
            self.redis.set(
                name=refresh_token, value=user.id, ex=self.jwt_handler.refresh_token_expire
            ),
            self.redis.set(name=user.id, value=initial_amount+1, ex=60*60*24)
        )
        return Token(
            access_token=self.jwt_handler.encode(
                payload={"user_id": str(user.id)}
            ),
            refresh_token=refresh_token,
        )

    async def me(self, user_id) -> UserOut:
        query = self.user_repository.query_by_id(user_id)
        async with self.database.begin() as session:
            user = (await session.execute(query)).first()
        if not user:
            raise BadRequestException("Invalid credentials")
        return UserOut(**user._asdict())

    async def refresh_token(self, refresh_token: str) -> Token:
        if not self.redis:
            raise CustomException("Database connection is not initialized")

        user_id = await self.redis.get(refresh_token)
        if not user_id:
            raise UnauthorizedException("Invalid refresh token")
        user_id = str(user_id)

        return Token(
            access_token=self.jwt_handler.encode(
                payload={"user_id": user_id}
            ),
            refresh_token=refresh_token,
        )
