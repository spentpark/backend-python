import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.game import Game
from app.models.platform import Platform
from app.models.review import Review

DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(
    DATABASE_URL_TEST,
    echo=False,
    poolclass=StaticPool,
)
AsyncSessionTesting = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with AsyncSessionTesting() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

# httpx >= 0.28 eliminó el argumento `app=`; se usa ASGITransport explícito.
transport = ASGITransport(app=app)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    async def _create():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionTesting() as session:
            test_platform = Platform(
                id=1,
                description="PlayStation 5",
                url="https://ps5.com",
            )
            test_game = Game(
                id=1,
                title="Elden Ring",
                description="An open world RPG",
                Platform="PlayStation 5",
            )
            # Segundo juego con reseñas: el juego 1 se queda sin ninguna para
            # poder seguir comprobando el 404.
            reviewed_game = Game(
                id=2,
                title="Hades",
                description="A roguelike dungeon crawler",
                Platform="PC",
            )
            reviews = [
                Review(
                    id=index,
                    name=f"Author {index}",
                    date="2024-01-01",
                    review=f"Review {index}",
                    score="8",
                    source="Metacritic",
                    id_game=2,
                )
                for index in range(1, 16)
            ]
            session.add_all([test_platform, test_game, reviewed_game, *reviews])
            await session.commit()

    async def _drop():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_create())
    yield
    asyncio.run(_drop())


@pytest.mark.asyncio
async def test_get_platforms():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/platforms/")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "pagination" in body
    assert len(body["data"]) > 0
    assert body["data"][0]["description"] == "PlayStation 5"
    assert body["pagination"]["currentPage"] == 1
    assert body["pagination"]["perPage"] == 10
    assert body["pagination"]["totalRecords"] == 1
    assert body["pagination"]["totalPages"] == 1


@pytest.mark.asyncio
async def test_get_platforms_paginated_params():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/platforms/?page=0&limit=100")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["currentPage"] == 0
    assert body["pagination"]["perPage"] == 100
    assert body["pagination"]["totalRecords"] == 1
    assert body["pagination"]["totalPages"] == 1
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_limit_invalido_devuelve_422():
    """Un `limit` menor que 1 se rechaza en lugar de provocar un error 500."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/platforms/?limit=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_games_page_zero():
    """`page=0` es válido y no genera un OFFSET negativo."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/games/?page=0")
    assert response.status_code == 200
    assert response.json()["pagination"]["currentPage"] == 0


@pytest.mark.asyncio
async def test_search_game_by_title():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/games/search?title=Elden")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["title"] == "Elden Ring"


@pytest.mark.asyncio
async def test_get_reviews_not_found():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/reviews/1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_reviews_paginadas_por_defecto():
    """Sin parámetros se devuelven las 10 reseñas de la primera página."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/reviews/2")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {
        "currentPage": 1,
        "perPage": 10,
        "totalRecords": 15,
        "totalPages": 2,
    }
    assert [review["id"] for review in body["data"]] == list(range(1, 11))


@pytest.mark.asyncio
async def test_get_reviews_segunda_pagina():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/reviews/2?page=2&limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["currentPage"] == 2
    assert body["pagination"]["totalPages"] == 2
    assert [review["id"] for review in body["data"]] == [11, 12, 13, 14, 15]


@pytest.mark.asyncio
async def test_get_reviews_pagina_fuera_de_rango():
    """Una página sin resultados responde 200 con `data` vacía."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/reviews/2?page=9&limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["pagination"]["totalRecords"] == 15
    assert body["pagination"]["totalPages"] == 2


@pytest.mark.asyncio
async def test_get_reviews_limit_invalido_devuelve_422():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/reviews/2?limit=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_games_by_platform_campos_resumidos():
    """El listado /games/ expone únicamente id, title y platform."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/games/?platform=PlayStation 5&page=0&limit=100")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "pagination"}
    assert body["data"] == [
        {"id": 1, "title": "Elden Ring", "platform": "PlayStation 5"}
    ]
    assert body["pagination"] == {
        "currentPage": 0,
        "perPage": 100,
        "totalRecords": 1,
        "totalPages": 1,
    }
