from ..adaptors.users import UserAdaptor
from ..core.database import DBManager


class UserRepository:
    adaptor = UserAdaptor

    async def get_and_create(self, username: str, password: str, db_session: DBManager):
        create_query = self.adaptor.create(
            password=password,
            username=username,
        )
        async with db_session.begin() as session:
            session.add(create_query)
            await session.flush()
            query = self.adaptor.query_by_username(username)
            user = (await session.execute(query)).first()
        return user

    async def get_by_username(self, username: str, db_session: DBManager):
        query = self.adaptor.get_by_username(username)
        async with db_session.begin() as session:
            user = await session.scalar(query)
        return user

    async def query_by_id(self, user_id: str, db_session: DBManager):
        query = self.adaptor.query_by_id(user_id)
        async with db_session.begin() as session:
            user = (await session.execute(query)).first()
        return user
