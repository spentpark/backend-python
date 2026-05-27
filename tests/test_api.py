import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import asyncio

# Importamos tus modelos para el seed data (ajusta los nombres de las clases según tu app)
from app.models import platform, game, review # <-- Asegúrate de que las rutas sean correctas

# 1. Configuración de Base de Datos de Prueba (SQLite en memoria)
DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"
engine_test = create_async_engine(DATABASE_URL_TEST, echo=False)
AsyncSessionTesting = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

# 2. Override de la dependencia get_db
async def override_get_db():
    async with AsyncSessionTesting() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Cambiamos el scope a "function" para evitar pérdidas de conexión en memoria entre tests
@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # --- INSERTAR DATOS SEMILLA (SEED DATA) ---
    async with AsyncSessionTesting() as session:
        # Añade aquí registros de ejemplo que tus pruebas necesitan
        test_platform = Platform(id=1, description="PlayStation 5", url="https://ps5.com")
        test_game = Game(id=1, title="Elden Ring", platform_id=1) # Ajusta según tus columnas reales
        
        session.add_all([test_platform, test_game])
        await session.commit()

    yield
    
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