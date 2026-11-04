"""Endpoints REST de la entidad Game (bajo ``/api/games``)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.game_controller import GameController, build_filters
from app.database import get_db
from app.middlewares.authenticate_jwt import authenticate_jwt, require_admin
from app.repositories.game_repo import GameRepository
from app.schemas.game_schema import (
    GameCreate,
    GameResponse,
    PaginatedGameSummaryResponse,
    RandomGameResponse,
)
from app.services.game_service import GameService

router = APIRouter(
    prefix="/games",
    tags=["Games"],
    dependencies=[Depends(authenticate_jwt)],
)


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> GameController:
    """Factory de dependencias: construye Repository → Service → Controller."""
    return GameController(GameService(GameRepository(db)))


ControllerDep = Annotated[GameController, Depends(get_controller)]

PageParam = Annotated[int, Query(ge=0)]
LimitParam = Annotated[int, Query(ge=1)]


@router.get("/search", response_model=PaginatedGameSummaryResponse)
async def search(
    ctrl: ControllerDep,
    title: str | None = None,
    page: PageParam = 1,
    limit: LimitParam = 10,
):
    """Busca juegos por prefijo de título (``title`` obligatorio)."""
    return await ctrl.search_by_title(title, page, limit)


@router.get("/random", response_model=RandomGameResponse)
async def get_random(
    ctrl: ControllerDep,
    platform: str | None = None,
    genre: str | None = None,
):
    """Devuelve un juego al azar que tenga tráiler (pantalla de inicio del SPA)."""
    return await ctrl.get_random_game(build_filters(platform=platform, genre=genre))


@router.get("", response_model=PaginatedGameSummaryResponse)
# Alias con barra final: Node tolera `/api/games/` y `/api/games` sin redirigir,
# pero la ruta documentada es la del contrato (`/api/games`).
@router.get("/", response_model=PaginatedGameSummaryResponse, include_in_schema=False)
async def get_all(
    ctrl: ControllerDep,
    platform: str | None = None,
    genre: str | None = None,
    year: str | None = None,
    decade: str | None = None,
    players: str | None = None,
    sort: str | None = None,
    page: PageParam = 1,
    limit: LimitParam = 10,
):
    """Lista juegos por plataforma o con filtros avanzados (paginado)."""
    filters = build_filters(
        platform=platform,
        genre=genre,
        year=year,
        decade=decade,
        players=players,
        sort=sort,
    )

    return await ctrl.filter_games(filters, page, limit)


@router.get("/{id}", response_model=GameResponse)
async def get_by_id(id: int, ctrl: ControllerDep):
    return await ctrl.get_game_by_id(id)


@router.post(
    "",
    response_model=GameResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
# Alias con barra final: Node tolera `/api/games/` y `/api/games` sin redirigir.
@router.post(
    "/",
    response_model=GameResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
    include_in_schema=False,
)
async def create(data: GameCreate, ctrl: ControllerDep):
    return await ctrl.create_game(data)


@router.put("/{id}", dependencies=[Depends(require_admin)])
async def update(id: int, data: GameCreate, ctrl: ControllerDep):
    return await ctrl.update_game(id, data)


@router.delete("/{id}", dependencies=[Depends(require_admin)])
async def delete(id: int, ctrl: ControllerDep):
    return await ctrl.delete_game(id)
