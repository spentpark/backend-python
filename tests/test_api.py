import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.platform import Platform
from app.models.game import Game
from app.models.review import Review

DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(
    DATABASE_URL_TEST,
    echo=False,
    poolclass=StaticPool
)
AsyncSessionTesting = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with AsyncSessionTesting() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    async def _create():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionTesting() as session:
            test_platform = Platform(
                id=1, 
                description="PlayStation 5", 
                url="https://ps5.com"
            )
            test_game = Game(
                id=1,
                title="Elden Ring",
                description="An open world RPG",
                Platform="PlayStation 5"
            )
            session.add_all([test_platform, test_game])
            await session.commit()

    async def _drop():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_create())
    yield
    asyncio.run(_drop())

@pytest.mark.asyncio
async def test_get_platforms():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/platforms/")
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_search_game_by_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/games/search?title=Elden")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["title"] == "Elden Ring"

@pytest.mark.asyncio
async def test_get_reviews_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/reviews/1")
    assert response.status_code == 404