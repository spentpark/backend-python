"""Endpoints REST de la entidad Game."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.game_controller import GameController
from app.database import get_db
from app.repositories.game_repo import GameRepository
from app.schemas.game_schema import (
    GameCreate,
    GameResponse,
    PaginatedGameResponse,
    PaginatedGameSummaryResponse,
)
from app.services.game_service import GameService

router = APIRouter(prefix="/games", tags=["Games"])


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> GameController:
    """Factory de dependencias: construye Repository → Service → Controller."""
    return GameController(GameService(GameRepository(db)))


ControllerDep = Annotated[GameController, Depends(get_controller)]


@router.get("/search", response_model=PaginatedGameResponse)
async def search(
    title: str,
    ctrl: ControllerDep,
    page: Annotated[int, Query(ge=0)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await ctrl.search_by_title(title, page, limit)


@router.get("/", response_model=PaginatedGameSummaryResponse)
async def get_all(
    ctrl: ControllerDep,
    platform: str | None = None,
    page: Annotated[int, Query(ge=0)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await ctrl.filter_by_platform(platform, page, limit)


@router.get("/{id}", response_model=GameResponse)
async def get_by_id(id: int, ctrl: ControllerDep):
    return await ctrl.get_game_by_id(id)


@router.post("/", response_model=GameResponse, status_code=201)
async def create(data: GameCreate, ctrl: ControllerDep):
    return await ctrl.create_game(data)


@router.put("/{id}")
async def update(id: int, data: GameCreate, ctrl: ControllerDep):
    return await ctrl.update_game(id, data)


@router.delete("/{id}")
async def delete(id: int, ctrl: ControllerDep):
    return await ctrl.delete_game(id)
