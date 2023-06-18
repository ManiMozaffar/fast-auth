import sqlalchemy as sa
from sqlalchemy import func

from ..models import User
from ..schema.query.user import UserQuery


class UserRepository:
    def get_selects(self):
        return [getattr(User, field) for field in UserQuery.__fields__]

    def get_by_username(self, username: str):
        return sa.select(User).where(func.lower(User.username) == func.lower(username))

    def get_by_id(self, user_id: str):
        return sa.select(User).where(User.id == user_id)

    def query_by_username(self, username: str):
        return sa.select(*self.get_selects()).where(
            User.username.ilike(username)
        )

    def query_by_id(self, user_id: str):
        return sa.select(*self.get_selects()).where(User.id == user_id)

    def create(self, username: str, password: str):
        return User(username=username, password=password)
