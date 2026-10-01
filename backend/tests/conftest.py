import asyncio
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://mindmap:mindmap@localhost:5432/mindmap_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """app.db.redis creates a single module-level redis.asyncio.Redis client
    at import time that binds its connection pool to whichever event loop
    first uses it. pytest-asyncio's default is a fresh loop per test
    function, which makes every test after the first raise 'RuntimeError:
    Event loop is closed' the moment it touches Redis. Sharing one
    session-scoped loop across every test (fixtures and test bodies alike)
    keeps everything - the DB engine, the redis client, and each test - on
    the same loop. This overrides a fixture pytest-asyncio provides and is
    deprecated in favor of per-test `loop_scope`, but it is the option that
    reliably keeps fixtures and test bodies on the same loop in 0.24."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    from app.core.config import settings
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(db_session):
    # Rate limiting is keyed by (path, client-identifier) in Redis, and every
    # test client here shares the same identifier (no real IP in ASGITransport
    # tests), so without a flush the very real auth rate limit added for
    # production would otherwise fail later tests in the same run once
    # earlier tests' login/register calls exhaust the shared bucket.
    from app.db.redis import redis_client

    await redis_client.flushdb()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
