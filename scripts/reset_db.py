import asyncio

from src.core.database import SQL_DB
from src.models import MarketPlace, Profile, User

__all__ = ["Profile", "MarketPlace", "User"]


async def up_database():
    await SQL_DB.drop_tables()
    await SQL_DB.create_tables()


asyncio.run(up_database())
