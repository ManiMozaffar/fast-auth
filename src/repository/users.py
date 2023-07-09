from typing import Any

from sqlalchemy.engine import Row

from ..adaptors.users import UserAdaptor
from ..core.database import DBManager
from ..models.user import User


class UserRepository:
    adaptor = UserAdaptor

    @staticmethod
    def base_return(user: Row[Any] | None) -> User | None:
        if not user:
            return None
        return user._mapping.get("User", user._mapping)

    async def get_and_create(
        self, username: str, password: str, gauth: str, db_session: DBManager
    ) -> User | None:
        create_query = self.adaptor.create(password=password, username=username, gauth=gauth)
        async with db_session.begin() as session:
            session.add(create_query)
            await session.flush()
            query = self.adaptor.query_by_username(username)
            user = (await session.execute(query)).first()
        return UserRepository.base_return(user)

    async def get_by_username(self, username: str, db_session: DBManager) -> User | None:
        query = self.adaptor.get_by_username(username)
        async with db_session.begin() as session:
            user = (await session.execute(query)).first()
        return UserRepository.base_return(user)

    async def query_by_id(self, user_id: str, db_session: DBManager) -> User | None:
        query = self.adaptor.query_by_id(user_id)
        async with db_session.begin() as session:
            user = (await session.execute(query)).first()
        return UserRepository.base_return(user)
