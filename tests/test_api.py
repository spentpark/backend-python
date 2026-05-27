import pytest
from httpx import AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import asyncio

# Importamos los modelos desde tus módulos de la app
from app.models import Platform, Game, Review

# 1. Configuración de Base de Datos de Prueba (SQLite en memoria con StaticPool)
DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(
    DATABASE_URL_TEST, 
    echo=False,
    poolclass=StaticPool  # Mantiene la misma conexión abierta para que no se pierdan las tablas
)
AsyncSessionTesting = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

# 2. Override de la dependencia get_db de FastAPI
async def override_get_db():
    async with AsyncSessionTesting() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Fixture con scope "function" para aislar y limpiar la base de datos en cada test
@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    # Crear las tablas en la base de datos de prueba
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # --- INSERTAR DATOS SEMILLA (SEED DATA) ---
    async with AsyncSessionTesting() as session:
        test_platform = Platform(id=1, description="PlayStation 5", url="https://ps5.com")
        test_game = Game(id=1, title="Elden Ring", platform_id=1)
        
        session.add_all([test_platform, test_game])
        await session.commit()

    yield
    
    # Limpiar las tablas al terminar el test
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# --- PRUEBAS PARA PLATFORMS ---

@pytest.mark.asyncio
async def test_get_platforms():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/platforms/")
    assert response.status_code == 200
    assert len(response.json()) > 0


# --- PRUEBAS PARA GAMES ---

@pytest.mark.asyncio
async def test_search_game_by_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/games/search?title=Elden")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["title"] == "Elden Ring"


# --- PRUEBAS PARA REVIEWS ---

@pytest.mark.asyncio
async def test_get_reviews_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Buscamos reseñas de un juego que no existe (ID 999)
        response = await ac.get("/reviews/999")
    assert response.status_code == 404