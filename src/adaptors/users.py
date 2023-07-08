import sqlalchemy as sa
from sqlalchemy import func

from ..models import User
from ..schema.query.user import UserQuery


class UserAdaptor:
    @staticmethod
    def get_selects():
        return [getattr(User, field) for field in UserQuery.__fields__]

    @staticmethod
    def get_by_username(username: str):
        return sa.select(User).where(func.lower(User.username) == func.lower(username))

    @staticmethod
    def get_by_id(user_id: str):
        return sa.select(User).where(User.id == user_id)

    @staticmethod
    def query_by_username(username: str):
        return sa.select(*UserAdaptor.get_selects()).where(User.username.ilike(username))

    @staticmethod
    def query_by_id(user_id: str):
        return sa.select(*UserAdaptor.get_selects()).where(User.id == user_id)

    @staticmethod
    def create(username: str, password: str):
        return User(username=username, password=password)
