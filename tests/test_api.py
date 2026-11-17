"""Pruebas de integración de la Games API (FastAPI + SQLite en memoria).

Cubren el contrato equivalente al backend Node: rutas bajo ``/api``, JWT en las
rutas de negocio y rol ``admin`` en las escrituras, además del endurecimiento
HTTP (cabeceras, límite de cuerpo, errores JSON y CORS).
"""
import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app, create_app
from app.middlewares.security import RateLimitMiddleware
from app.models.game import Game
from app.models.platform import Platform
from app.models.review import Review
from app.models.similar_game import SimilarGame
from app.repositories import game_repo
from app.services import auth_service
from app.services.stats_service import clear_stats_cache

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


def auth_headers(role: str = "admin") -> dict[str, str]:
    """Cabeceras con un JWT válido para el rol indicado."""
    issued = auth_service.issue_token({"username": "admin", "role": role})
    return {"Authorization": f"Bearer {issued['token']}"}


@pytest.fixture(autouse=True)
def setup_db():
    """Crea y destruye el esquema SQLite con un catálogo de prueba."""
    clear_stats_cache()

    async def _create():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionTesting() as session:
            platforms = [
                Platform(id=1, description="PlayStation 5", url="https://ps5.com"),
                Platform(id=2, description="PC", url="https://pc.com"),
                Platform(id=3, description="Super Nintendo", url=None),
            ]
            games = [
                Game(
                    id=1,
                    title="Elden Ring",
                    description="Un RPG de mundo abierto",
                    Platform="PlayStation 5",
                    Publisher="FromSoftware",
                    releasedate="2022-02-25",
                    players="1",
                    genre="RPG",
                    metacritic_score="96",
                    image_Medium="https://img.test/elden-ring-medium.jpg",
                    image_Large="https://img.test/elden-ring-large.jpg",
                    image_Original="https://img.test/elden-ring.jpg",
                    image_Front="https://img.test/elden-ring-front.jpg",
                    youtube_Trailer="https://www.youtube.com/embed/elden-ring",
                ),
                Game(
                    id=2,
                    title="Hades",
                    description="Un roguelike de acción",
                    Platform="PC",
                    Publisher="Supergiant Games",
                    releasedate="2020-09-17",
                    players="1",
                    genre="Roguelike",
                    metacritic_score="93",
                ),
                Game(
                    id=3,
                    title="Super Metroid",
                    description="Metroidvania clásico",
                    Platform="Super Nintendo",
                    Publisher="Nintendo",
                    releasedate="1994-03-19",
                    players="1",
                    genre="Platformer",
                    metacritic_score="",
                ),
            ]
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
            similar_games = [
                SimilarGame(id_game=1, json="[]"),
                SimilarGame(
                    id_game=2,
                    json=json.dumps(
                        [
                            {"id": 2, "title": "Hades", "similarity": 1.0},
                            {"id": 1, "title": "Elden Ring", "similarity": 0.4267},
                            {"id": 3, "title": "Super Metroid", "similarity": 0.9},
                            {"id": 4, "title": "Entrada corrupta", "similarity": "x"},
                            {"id": "5", "title": "Id inválido", "similarity": 0.1},
                        ]
                    ),
                ),
                SimilarGame(id_game=99, json="esto-no-es-json"),
            ]

            session.add_all([*platforms, *games, *reviews, *similar_games])
            await session.commit()

    async def _drop():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_create())
    yield
    asyncio.run(_drop())
    clear_stats_cache()


# --- Autenticación ---------------------------------------------------------


@pytest.mark.asyncio
async def test_login_emite_token_y_me_devuelve_el_usuario():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password"},
        )
        assert login.status_code == 200
        body = login.json()
        assert body["tokenType"] == "Bearer"
        assert body["token"]
        assert body["expiresAt"].endswith("Z")
        assert login.headers["cache-control"] == "no-store"

        me = await ac.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
        )

    assert me.status_code == 200
    assert me.json() == {"username": "admin", "role": "admin"}
    assert me.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_login_sin_credenciales_devuelve_400():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", json={})

    assert response.status_code == 400
    assert response.json() == {"error": "Usuario y contraseña son obligatorios"}


@pytest.mark.asyncio
async def test_login_con_password_incorrecta_devuelve_401():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "incorrecta"},
        )

    assert response.status_code == 401
    assert response.json() == {"error": "Credenciales inválidas"}


@pytest.mark.asyncio
async def test_me_sin_token_devuelve_401_con_www_authenticate():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"error": "No autorizado"}
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_token_con_firma_invalida_devuelve_401():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games", headers={"Authorization": "Bearer token.invalido.firma"}
        )

    assert response.status_code == 401
    assert response.json() == {"error": "No autorizado"}


# --- Protección JWT de las rutas de negocio --------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/games",
        "/api/games/1",
        "/api/games/random",
        "/api/games/search?title=Elden",
        "/api/games/1/similar",
        "/api/platforms",
        "/api/platforms/1",
        "/api/platforms/1/top-games",
        "/api/reviews/2",
        "/api/stats",
    ],
)
async def test_rutas_de_negocio_exigen_jwt(path):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(path)

    assert response.status_code == 401
    assert response.json() == {"error": "No autorizado"}


@pytest.mark.asyncio
async def test_escrituras_exigen_rol_admin():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/games",
            json={"title": "Nuevo", "description": "Juego"},
            headers=auth_headers(role="user"),
        )

    assert response.status_code == 403
    assert response.json() == {"error": "Acceso denegado"}


# --- Utilidades ------------------------------------------------------------


@pytest.mark.asyncio
async def test_saludo_publico():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/saludo")

    assert response.status_code == 200
    assert response.json() == {"mensaje": "¡Hola desde Python con FastAPI!"}


@pytest.mark.asyncio
async def test_root_y_favicon():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        root = await ac.get("/")
        favicon = await ac.get("/favicon.ico")

    assert root.status_code == 200
    assert root.json()["docs"] == "/api-docs"
    assert favicon.status_code == 204


@pytest.mark.asyncio
async def test_documentacion_openapi_en_rutas_de_node():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        spec = await ac.get("/api-docs.json")
        docs = await ac.get("/api-docs")

    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/api/games" in paths
    assert "/api/games/{id}/similar" in paths
    assert "/api/auth/login" in paths
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text


# --- Juegos ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_listado_por_plataforma_expone_solo_resumen():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games",
            params={"platform": "PlayStation 5", "page": 0, "limit": 100},
            headers=auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == [
        {"id": 1, "title": "Elden Ring", "platform": "PlayStation 5"}
    ]
    assert body["pagination"] == {
        "currentPage": 0,
        "perPage": 100,
        "totalRecords": 1,
        "totalPages": 1,
    }


@pytest.mark.asyncio
async def test_listado_sin_plataforma_devuelve_pagina_vacia():
    """Igual que Node: sin `platform` la comparación con NULL no coincide."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["pagination"]["totalRecords"] == 0


@pytest.mark.asyncio
async def test_filtros_avanzados_y_orden():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        by_genre = await ac.get(
            "/api/games",
            params={"platform": "PC", "genre": "Roguelike"},
            headers=auth_headers(),
        )
        by_year = await ac.get(
            "/api/games",
            params={"platform": "PlayStation 5", "year": "2022", "sort": "score_desc"},
            headers=auth_headers(),
        )

    assert by_genre.status_code == 200
    assert [game["id"] for game in by_genre.json()["data"]] == [2]
    assert by_year.status_code == 200
    assert [game["id"] for game in by_year.json()["data"]] == [1]


@pytest.mark.asyncio
async def test_buscar_juego_por_titulo():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/search",
            params={"title": "Elden"},
            headers=auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == [
        {"id": 1, "title": "Elden Ring", "platform": "PlayStation 5"}
    ]


@pytest.mark.asyncio
async def test_buscar_sin_title_devuelve_400_con_mensaje_de_node():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/search", headers=auth_headers())

    assert response.status_code == 400
    assert response.json() == {"error": 'El parámetro "title" es requerido'}


@pytest.mark.asyncio
async def test_get_game_by_id_y_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        found = await ac.get("/api/games/1", headers=auth_headers())
        missing = await ac.get("/api/games/9999", headers=auth_headers())

    assert found.status_code == 200
    assert found.json()["title"] == "Elden Ring"
    assert missing.status_code == 404
    assert missing.json() == {"error": "Juego no encontrado"}


@pytest.mark.asyncio
async def test_random_game_con_trailer(monkeypatch):
    monkeypatch.setattr(game_repo, "_random_id", lambda _low, _high: 1)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/random", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Elden Ring",
        "description": "Un RPG de mundo abierto",
        "platform": "PlayStation 5",
        "publisher": "FromSoftware",
        "releasedate": "2022-02-25",
        "players": "1",
        "genre": "RPG",
        "imageMedium": "https://img.test/elden-ring-medium.jpg",
        "imageLarge": "https://img.test/elden-ring-large.jpg",
        "imageOriginal": "https://img.test/elden-ring.jpg",
        "imageFront": "https://img.test/elden-ring-front.jpg",
        "youtubeTrailer": "https://www.youtube.com/embed/elden-ring",
    }


@pytest.mark.asyncio
async def test_random_game_por_genero(monkeypatch):
    monkeypatch.setattr(game_repo, "_random_id", lambda _low, _high: 1)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/random", params={"genre": "RPG"}, headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Elden Ring"


@pytest.mark.asyncio
async def test_random_game_sin_trailers():
    async with AsyncSessionTesting() as session:
        await session.execute(update(Game).values(youtube_Trailer=None))
        await session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/random", headers=auth_headers())

    assert response.status_code == 404
    assert response.json() == {"error": "No hay ningún juego con tráiler disponible"}


@pytest.mark.asyncio
async def test_crud_de_juegos_con_admin():
    headers = auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(
            "/api/games",
            json={"title": "Hollow Knight", "description": "Metroidvania"},
            headers=headers,
        )
        updated = await ac.put(
            "/api/games/1",
            json={"title": "Elden Ring Nightreign", "description": "DLC"},
            headers=headers,
        )
        deleted = await ac.delete("/api/games/3", headers=headers)
        after = await ac.get("/api/games/3", headers=headers)

    assert created.status_code == 201
    assert created.json()["title"] == "Hollow Knight"
    assert updated.status_code == 200
    assert updated.json()["title"] == "Elden Ring Nightreign"
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True}
    assert after.status_code == 404


@pytest.mark.asyncio
async def test_crud_de_juegos_con_id_inexistente():
    headers = auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        updated = await ac.put(
            "/api/games/9999",
            json={"title": "Nada", "description": "No existe"},
            headers=headers,
        )
        deleted = await ac.delete("/api/games/9999", headers=headers)

    assert updated.status_code == 404
    assert deleted.status_code == 404


# --- Plataformas -----------------------------------------------------------


@pytest.mark.asyncio
async def test_plataformas_paginadas():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/platforms",
            params={"page": 1, "limit": 2},
            headers=auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    # Solo las plataformas con url no nula.
    assert body["pagination"] == {
        "currentPage": 1,
        "perPage": 2,
        "totalRecords": 2,
        "totalPages": 1,
    }
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_plataforma_por_id_y_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        found = await ac.get("/api/platforms/1", headers=auth_headers())
        missing = await ac.get("/api/platforms/9999", headers=auth_headers())

    assert found.status_code == 200
    assert found.json()["description"] == "PlayStation 5"
    assert missing.status_code == 404
    assert missing.json() == {"error": "Plataforma no encontrada"}


@pytest.mark.asyncio
async def test_top_games_por_plataforma():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/platforms/1/top-games", headers=auth_headers())
        empty = await ac.get("/api/platforms/3/top-games", headers=auth_headers())

    assert response.status_code == 200
    assert [game["id"] for game in response.json()] == [1]
    assert response.json()[0]["metacritic_score"] == "96"
    assert empty.status_code == 200
    assert empty.json() == []


@pytest.mark.asyncio
async def test_crud_de_plataformas_con_admin():
    headers = auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(
            "/api/platforms",
            json={"description": "Nintendo Switch", "url": "https://switch.com"},
            headers=headers,
        )
        updated = await ac.put(
            "/api/platforms/2",
            json={"description": "PC Master Race", "url": "https://pc.com"},
            headers=headers,
        )
        deleted = await ac.delete("/api/platforms/1", headers=headers)

    assert created.status_code == 200
    assert created.json()["description"] == "Nintendo Switch"
    assert updated.status_code == 200
    assert updated.json()["description"] == "PC Master Race"
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True}


# --- Reseñas ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_reviews_paginadas_por_defecto():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/reviews/2", headers=auth_headers())

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
async def test_reviews_segunda_pagina_y_fuera_de_rango():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        second = await ac.get(
            "/api/reviews/2", params={"page": 2, "limit": 10}, headers=auth_headers()
        )
        out_of_range = await ac.get(
            "/api/reviews/2", params={"page": 9, "limit": 10}, headers=auth_headers()
        )

    assert [review["id"] for review in second.json()["data"]] == [11, 12, 13, 14, 15]
    assert out_of_range.status_code == 200
    assert out_of_range.json()["data"] == []


@pytest.mark.asyncio
async def test_reviews_sin_resenas_devuelve_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/reviews/1", headers=auth_headers())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_limit_invalido_devuelve_400_generico():
    """La validación de FastAPI se normaliza al contrato JSON de Node."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/reviews/2", params={"limit": 0}, headers=auth_headers()
        )

    assert response.status_code == 400
    assert response.json() == {"error": "Petición inválida"}


# --- Similares -------------------------------------------------------------


@pytest.mark.asyncio
async def test_juegos_similares_excluye_el_propio_y_calcula_porcentaje():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/2/similar", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["gameId"] == 2
    assert body["total"] == 2
    assert [game["id"] for game in body["similarGames"]] == [3, 1]
    assert body["similarGames"][1] == {
        "id": 1,
        "title": "Elden Ring",
        "similarity": 0.4267,
        "similarityPercentage": 42.67,
    }


@pytest.mark.asyncio
async def test_juegos_similares_respeta_limit():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/2/similar", params={"limit": 1}, headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["similarGames"][0]["id"] == 3


@pytest.mark.asyncio
async def test_juegos_similares_sin_registros_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/1/similar", headers=auth_headers())

    assert response.status_code == 404
    assert response.json() == {
        "error": "No se encontraron juegos similares para el juego indicado"
    }


@pytest.mark.asyncio
async def test_juegos_similares_json_corrupto_500():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/99/similar", headers=auth_headers())

    assert response.status_code == 500
    assert response.json() == {"error": "Error al obtener juegos similares"}


@pytest.mark.asyncio
async def test_juegos_similares_id_no_numerico_400():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/abc/similar", headers=auth_headers())

    assert response.status_code == 400
    assert response.json() == {"error": "Petición inválida"}


# --- Estadísticas ----------------------------------------------------------


@pytest.mark.asyncio
async def test_stats_devuelve_totales_y_distribuciones():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/stats", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "totalGames": 3,
        "scoredGames": 2,
        "totalPlatforms": 3,
        "totalGenres": 3,
    }
    assert {entry["label"]: entry["total"] for entry in body["platforms"]} == {
        "PlayStation 5": 1,
        "PC": 1,
        "Super Nintendo": 1,
    }
    assert {entry["label"]: entry["total"] for entry in body["decades"]} == {
        "2020": 2,
        "1990": 1,
    }


@pytest.mark.asyncio
async def test_stats_se_cachean_diez_minutos():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.get("/api/stats", headers=auth_headers())

        async with AsyncSessionTesting() as session:
            await session.execute(delete(Game))
            await session.commit()

        cached = await ac.get("/api/stats", headers=auth_headers())

    assert first.json() == cached.json()
    assert cached.json()["summary"]["totalGames"] == 3


# --- Endurecimiento HTTP ---------------------------------------------------


@pytest.mark.asyncio
async def test_cabeceras_de_seguridad():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/saludo")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "max-age=31536000" in response.headers["strict-transport-security"]


@pytest.mark.asyncio
async def test_404_json_de_ruta_desconocida():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/ruta-inexistente")

    assert response.status_code == 404
    assert response.json() == {"error": "Ruta no encontrada"}


@pytest.mark.asyncio
async def test_json_malformado_devuelve_400():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            content="{no-es-json",
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json() == {"error": "Petición inválida"}


@pytest.mark.asyncio
async def test_cuerpo_mayor_de_10kb_devuelve_413():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "x" * 11000},
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 413
    assert response.json() == {
        "error": "El cuerpo de la petición es demasiado grande"
    }


@pytest.mark.asyncio
async def test_cors_permite_origen_de_la_allowlist():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/saludo", headers={"Origin": "http://localhost:5173"}
        )
        preflight = await ac.options(
            "/api/games",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert preflight.status_code == 200
    assert "GET" in preflight.headers["access-control-allow-methods"]


@pytest.mark.asyncio
async def test_cors_permite_origenes_del_frontend_react():
    """El SPA React (Vite, preview y Nginx) debe poder llamar a la API."""
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8065",
        "http://127.0.0.1:8065",
        "http://192.168.1.82:8065",
        "http://200.83.105.123:8065",
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for origin in origins:
            response = await ac.get("/api/saludo", headers={"Origin": origin})

            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin

        # Preflight real del navegador: método GET con JWT y cabecera `apikey`.
        preflight = await ac.options(
            "/api/games",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type,apikey",
            },
        )

    assert preflight.status_code == 200
    allowed_headers = preflight.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
    assert "apikey" in allowed_headers


@pytest.mark.asyncio
async def test_cors_en_produccion_solo_acepta_la_allowlist(monkeypatch):
    """En producción se desactiva el comodín local: solo vale la allowlist."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    production_transport = ASGITransport(app=create_app())

    async with AsyncClient(
        transport=production_transport, base_url="http://test"
    ) as ac:
        allowed = await ac.get(
            "/api/saludo", headers={"Origin": "http://localhost:5173"}
        )
        allowed_ip = await ac.get(
            "/api/saludo", headers={"Origin": "http://200.83.105.123:8065"}
        )
        blocked = await ac.get(
            "/api/saludo", headers={"Origin": "http://localhost:9999"}
        )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert (
        allowed_ip.headers["access-control-allow-origin"]
        == "http://200.83.105.123:8065"
    )
    assert "access-control-allow-origin" not in blocked.headers


@pytest.mark.asyncio
async def test_rate_limit_devuelve_429_con_cabeceras():
    limited_app = Starlette(routes=[Route("/api/x", lambda request: JSONResponse({}))])
    limited_app.add_middleware(
        RateLimitMiddleware,
        window_seconds=60,
        limit=2,
        message="Demasiadas solicitudes. Inténtalo más tarde.",
    )

    async with AsyncClient(
        transport=ASGITransport(app=limited_app), base_url="http://test"
    ) as ac:
        first = await ac.get("/api/x")
        second = await ac.get("/api/x")
        third = await ac.get("/api/x")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json() == {"error": "Demasiadas solicitudes. Inténtalo más tarde."}
    assert third.headers["ratelimit-limit"] == "2"
    assert third.headers["retry-after"]


# --- Dependencias ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_db_entrega_y_cierra_la_sesion():
    """`get_db` produce una sesión y la cierra al agotar el generador."""
    generator = get_db()
    session = await generator.__anext__()
    assert isinstance(session, AsyncSession)
    await generator.aclose()


# --- Cobertura de ramas defensivas y utilidades internas -------------------

import runpy
import time
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import uvicorn
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request
from starlette.responses import Response

from app.config import auth as auth_config
from app.controllers.game_controller import GameController
from app.controllers.main_controller import MainController
from app.controllers.platform_controller import PlatformController
from app.controllers.stats_controller import StatsController
from app.middlewares.authenticate_jwt import authenticate_jwt
from app.middlewares.security import (
    MAX_WINDOW_ENTRIES,
    BodyLimitMiddleware,
    _env_positive_int,
)
from app.repositories import main_repo
from app.repositories.game_repo import GameRepository
from app.repositories.platform_repo import PlatformRepository
from app.routes import similar_routes
from app.services.game_service import GameService
from app.services.platform_service import PlatformService
from app.services.similar_games_service import (
    SimilarGamesParseError,
    parse_similar_games,
    to_similar_game,
)


async def _responder_sin_contenido(_request):
    return Response(status_code=204)


def _peticion(method: str = "GET", path: str = "/api/x", headers=None) -> Request:
    """Construye un `Request` de Starlette sin pasar por un servidor HTTP."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": headers or [],
        "client": ("1.2.3.4", 123),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


# --- Autenticación: utilidades internas ------------------------------------


def test_extraer_token_bearer():
    assert auth_service.extract_bearer_token(None) is None
    assert auth_service.extract_bearer_token(123) is None
    assert auth_service.extract_bearer_token("Basic abc") is None
    assert auth_service.extract_bearer_token("Bearer abc.def") == "abc.def"
    assert auth_service.extract_bearer_token("bearer   xyz   ") == "xyz"


def test_parse_expires_in_valores():
    assert auth_service._parse_expires_in(None) == 3600
    assert auth_service._parse_expires_in("") == 3600
    assert auth_service._parse_expires_in("abc") == 3600
    assert auth_service._parse_expires_in("0") == 3600
    assert auth_service._parse_expires_in("30m") == 1800
    assert auth_service._parse_expires_in("2d") == 172800
    assert auth_service._parse_expires_in("3600") == 3600


def test_login_sin_hash_configurado(monkeypatch):
    monkeypatch.setenv("AUTH_PASSWORD_HASH", "")

    assert auth_service.login("admin", "cualquiera") is None


def test_login_con_hash_invalido_no_lanza(monkeypatch):
    monkeypatch.setenv("AUTH_PASSWORD_HASH", "esto-no-es-un-hash-bcrypt")

    assert auth_service.login("admin", "cualquiera") is None


def test_verify_token_con_claims_de_tipo_incorrecto():
    ahora = int(datetime.now(timezone.utc).timestamp())
    opciones = auth_config.get_verify_options()
    payload = {
        "sub": "admin",
        "role": 7,
        "iss": opciones["issuer"],
        "aud": opciones["audience"],
        "iat": ahora,
        "exp": ahora + 600,
    }
    token = pyjwt.encode(
        payload, auth_config.get_jwt_secret_or_raise(), algorithm="HS256"
    )

    with pytest.raises(auth_service.AuthError):
        auth_service.verify_token(token)


def test_get_jwt_secret_or_raise_sin_secreto(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        auth_config.get_jwt_secret_or_raise()


def test_validate_auth_configuration_incompleta_en_desarrollo(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("AUTH_PASSWORD_HASH", raising=False)

    assert auth_config.validate_auth_configuration() is False


def test_validate_auth_configuration_incompleta_en_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        auth_config.validate_auth_configuration()


def test_validate_auth_configuration_secreto_corto_en_desarrollo(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET", "corto")
    monkeypatch.setenv("AUTH_PASSWORD_HASH", "hash-de-prueba")

    assert auth_config.validate_auth_configuration() is True


def test_validate_auth_configuration_secreto_corto_en_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "corto")
    monkeypatch.setenv("AUTH_PASSWORD_HASH", "hash-de-prueba")

    with pytest.raises(RuntimeError):
        auth_config.validate_auth_configuration()


def test_authenticate_jwt_con_token_en_blanco():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="   ")

    with pytest.raises(HTTPException) as exc_info:
        authenticate_jwt(credentials)

    assert exc_info.value.status_code == 401


# --- Configuración de la aplicación ---------------------------------------


def test_app_sin_documentacion_cuando_api_docs_esta_deshabilitado(monkeypatch):
    monkeypatch.setenv("API_DOCS_ENABLED", "false")

    application = create_app()

    assert application.docs_url is None
    assert application.openapi_url is None


@pytest.mark.asyncio
async def test_cors_usa_cors_origins_del_entorno(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS", "http://app.example.com, http://otro.example.com"
    )
    application = create_app()
    transport_cors = ASGITransport(app=application)

    async with AsyncClient(transport=transport_cors, base_url="http://test") as ac:
        response = await ac.get(
            "/api/saludo", headers={"Origin": "http://app.example.com"}
        )

    assert response.headers["access-control-allow-origin"] == "http://app.example.com"


def test_punto_de_entrada_usa_host_y_puerto_del_entorno(monkeypatch):
    llamadas = {}
    monkeypatch.setattr(
        uvicorn, "run", lambda *args, **kwargs: llamadas.update(args=args, kwargs=kwargs)
    )
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8123")

    runpy.run_module("app.main", run_name="__main__")

    assert llamadas["args"] == ("app.main:app",)
    assert llamadas["kwargs"]["host"] == "127.0.0.1"
    assert llamadas["kwargs"]["port"] == 8123


# --- Errores no controlados ------------------------------------------------


@pytest.mark.asyncio
async def test_error_no_controlado_devuelve_500_json(monkeypatch):
    def _falla(*_args, **_kwargs):
        raise ValueError("error inesperado")

    monkeypatch.setattr(auth_service, "issue_token", _falla)
    transport_sin_errores = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(
        transport=transport_sin_errores, base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password"},
        )

    assert response.status_code == 500
    assert response.json() == {"error": "Error interno del servidor"}


# --- Controlador de autenticación: ramas de error -------------------------


@pytest.mark.asyncio
async def test_login_credenciales_demasiado_largas_400():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        usuario_largo = await ac.post(
            "/api/auth/login", json={"username": "a" * 101, "password": "x"}
        )
        password_larga = await ac.post(
            "/api/auth/login", json={"username": "admin", "password": "x" * 201}
        )

    assert usuario_largo.status_code == 400
    assert usuario_largo.json() == {"error": "Credenciales inválidas"}
    assert password_larga.status_code == 400


@pytest.mark.asyncio
async def test_login_error_interno_al_validar_credenciales(monkeypatch):
    def _falla(*_args, **_kwargs):
        raise RuntimeError("fallo de validación")

    monkeypatch.setattr(auth_service, "login", _falla)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password"},
        )

    assert response.status_code == 500
    assert response.json() == {"error": "Error al iniciar sesión"}


@pytest.mark.asyncio
async def test_login_error_al_emitir_token(monkeypatch):
    def _falla(*_args, **_kwargs):
        raise RuntimeError("configuración JWT inválida")

    monkeypatch.setattr(auth_service, "issue_token", _falla)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password"},
        )

    assert response.status_code == 500
    assert response.json() == {"error": "Error al iniciar sesión"}


# --- Middlewares de seguridad: ramas defensivas ---------------------------


def test_env_positive_int_invalido_usa_fallback(monkeypatch):
    monkeypatch.setenv("VALOR_NO_NUMERICO", "abc")

    assert _env_positive_int("VALOR_NO_NUMERICO", 9) == 9

    monkeypatch.setenv("VALOR_NO_NUMERICO", "0")

    assert _env_positive_int("VALOR_NO_NUMERICO", 9) == 9

    monkeypatch.delenv("VALOR_NO_NUMERICO")

    assert _env_positive_int("VALOR_NO_NUMERICO", 9) == 9


@pytest.mark.asyncio
async def test_body_limit_con_content_length_invalido():
    middleware = BodyLimitMiddleware(Starlette())
    request = _peticion(
        method="POST", headers=[(b"content-length", b"no-es-un-numero")]
    )

    response = await middleware.dispatch(request, _responder_sin_contenido)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_rate_limit_ignora_metodo_distinto():
    middleware = RateLimitMiddleware(
        Starlette(),
        window_seconds=60,
        limit=1,
        message="Demasiadas solicitudes",
        path_prefix="/api/auth/login",
        method="POST",
    )
    request = _peticion(method="GET", path="/api/auth/login")

    response = await middleware.dispatch(request, _responder_sin_contenido)

    assert response.status_code == 204
    assert middleware._requests == {}


@pytest.mark.asyncio
async def test_rate_limit_trust_proxy_usa_x_forwarded_for(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "true")
    middleware = RateLimitMiddleware(
        Starlette(), window_seconds=60, limit=1, message="Demasiadas solicitudes"
    )
    request = _peticion(headers=[(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")])

    assert middleware._client_key(request) == "203.0.113.9"


def test_rate_limit_poda_entradas_expiradas():
    middleware = RateLimitMiddleware(
        Starlette(), window_seconds=60, limit=10, message="Demasiadas solicitudes"
    )
    ahora = time.monotonic()

    for indice in range(MAX_WINDOW_ENTRIES + 1):
        middleware._requests[f"clave-{indice}"] = (ahora - 120, 1)

    middleware._prune(ahora)

    assert middleware._requests == {}


@pytest.mark.asyncio
async def test_rate_limit_reinicia_ventana_expirada(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    middleware = RateLimitMiddleware(
        Starlette(), window_seconds=60, limit=1, message="Demasiadas solicitudes"
    )
    middleware._requests["1.2.3.4"] = (time.monotonic() - 120, 5)

    response = await middleware.dispatch(_peticion(), _responder_sin_contenido)

    assert response.status_code == 204
    assert middleware._requests["1.2.3.4"][1] == 1


# --- Controladores y repositorios: caminos sin cubrir ---------------------


@pytest.mark.asyncio
async def test_controles_get_all_usan_los_repositorios():
    async with AsyncSessionTesting() as session:
        controlador_juegos = GameController(GameService(GameRepository(session)))
        controlador_plataformas = PlatformController(
            PlatformService(PlatformRepository(session))
        )

        juegos = await controlador_juegos.get_all_games()
        plataformas = await controlador_plataformas.get_all_platforms()

    assert len(juegos) == 3
    assert [plataforma.id for plataforma in plataformas] == [1, 2]


@pytest.mark.asyncio
async def test_hello_devuelve_fecha_de_la_base_de_datos():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/hello")

    assert response.status_code == 200
    assert response.json()["mensaje"] == "¡Conectado a MariaDB!"
    assert isinstance(response.json()["fecha"], str)


class _RepositorioQueFalla:
    async def find_current_date(self):
        raise RuntimeError("sin base de datos")


@pytest.mark.asyncio
async def test_hello_con_error_de_base_de_datos_devuelve_500():
    controlador = MainController(_RepositorioQueFalla())

    with pytest.raises(HTTPException) as exc_info:
        await controlador.hello()

    assert exc_info.value.status_code == 500


class _ServicioDeStatsQueFalla:
    async def get_stats(self):
        raise RuntimeError("sin estadísticas")


@pytest.mark.asyncio
async def test_stats_con_error_interno_devuelve_500():
    controlador = StatsController(_ServicioDeStatsQueFalla())

    with pytest.raises(HTTPException) as exc_info:
        await controlador.get_stats()

    assert exc_info.value.status_code == 500


def test_iso_z_normaliza_fechas_naive_y_con_zona():
    naive = datetime(2024, 1, 2, 3, 4, 5, 123456)
    con_zona = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-3)))

    assert main_repo._iso_z(naive) == "2024-01-02T03:04:05.123Z"
    assert main_repo._iso_z(con_zona) == "2024-01-02T06:04:05.000Z"


class _ResultadoDeTexto:
    def scalar_one(self):
        return "2024-01-02 03:04:05"


class _SesionQueDevuelveTexto:
    async def execute(self, _query):
        return _ResultadoDeTexto()


@pytest.mark.asyncio
async def test_find_current_date_con_valor_no_datetime():
    """Motores que no devuelven `datetime` se serializan con `str()`."""
    repositorio = main_repo.MainRepository(_SesionQueDevuelveTexto())

    assert await repositorio.find_current_date() == "2024-01-02 03:04:05"


@pytest.mark.asyncio
async def test_actualizar_y_borrar_plataforma_inexistente_404():
    headers = auth_headers()
    cuerpo = {"description": "Inexistente", "url": "https://inexistente.test"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        updated = await ac.put("/api/platforms/9999", json=cuerpo, headers=headers)
        deleted = await ac.delete("/api/platforms/9999", headers=headers)

    assert updated.status_code == 404
    assert updated.json() == {"error": "Plataforma no encontrada"}
    assert deleted.status_code == 404
    assert deleted.json() == {"error": "Plataforma no encontrada"}


# --- Juegos aleatorios y filtros avanzados --------------------------------


@pytest.mark.asyncio
async def test_filtros_por_players_y_decada():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        por_players = await ac.get(
            "/api/games",
            params={"platform": "PlayStation 5", "players": "1"},
            headers=auth_headers(),
        )
        por_decada = await ac.get(
            "/api/games",
            params={"platform": "Super Nintendo", "decade": "199"},
            headers=auth_headers(),
        )

    assert [juego["id"] for juego in por_players.json()["data"]] == [1]
    assert [juego["id"] for juego in por_decada.json()["data"]] == [3]


@pytest.mark.asyncio
async def test_random_sin_juegos_en_la_base_devuelve_404():
    async with AsyncSessionTesting() as session:
        await session.execute(delete(Game))
        await session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/random", headers=auth_headers())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_random_filtrado_sin_coincidencias_devuelve_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/random", params={"genre": "NoExiste"}, headers=auth_headers()
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_random_filtrado_usa_el_fallback(monkeypatch):
    monkeypatch.setattr(game_repo, "_random_id", lambda _low, _high: 999)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/random", params={"genre": "RPG"}, headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["id"] == 1


# --- Juegos similares: parseo y rutas -------------------------------------


def test_parse_similar_games_vacio():
    assert parse_similar_games(None) == []
    assert parse_similar_games("") == []


def test_parse_similar_games_no_es_lista():
    with pytest.raises(SimilarGamesParseError):
        parse_similar_games('{"id": 1}')


def test_to_similar_game_filtra_entradas_invalidas():
    assert to_similar_game("texto") is None
    assert to_similar_game({"id": 1, "similarity": float("nan")}) is None
    assert to_similar_game({"id": True, "similarity": 0.5}) is None
    assert to_similar_game({"id": 1, "similarity": True}) is None


@pytest.mark.asyncio
async def test_similar_de_juego_inexistente_404():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/games/9999/similar", headers=auth_headers())

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_similar_con_limit_invalido_devuelve_todos():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/games/2/similar", params={"limit": "abc"}, headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_parse_limit_casos(monkeypatch):
    assert similar_routes.parse_limit(None) is None
    assert similar_routes.parse_limit("0") is None
    assert similar_routes.parse_limit("3") == 3

    def _entero_que_falla(_value):
        raise ValueError("no convertible")

    monkeypatch.setattr(similar_routes, "int", _entero_que_falla, raising=False)

    assert similar_routes.parse_limit("42") is None
