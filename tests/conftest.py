import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.core.database.session import DBManager, SQLBase, get_db
from src.core.fastapi import app
from src.core.redis.client import get_redis_db
from tests.shared.mocks import redis


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="class")
async def mock_database():
    mock_database = DBManager(
        model_base=SQLBase,
        db_url="sqlite+aiosqlite:///:memory:"
    )
    await mock_database.drop_tables()
    await mock_database.create_tables()

    yield mock_database
    await mock_database.drop_tables()


@pytest.fixture(scope="class")
def mock_redis():
    yield redis.RedisMock()


@pytest_asyncio.fixture(scope="class")
async def http_client(mock_database, mock_redis):
    app.dependency_overrides[get_db] = lambda: mock_database
    app.dependency_overrides[get_redis_db] = lambda: mock_redis
    async with AsyncClient(app=app, base_url="http://test") as c:
        await app.router.startup()
        yield c
        await app.router.shutdown()
