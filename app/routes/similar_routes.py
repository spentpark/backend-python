"""Endpoints REST de los juegos similares (``/api/games/{id}/similar``)."""
import re
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.similar_games_controller import SimilarGamesController
from app.database import get_db
from app.middlewares.authenticate_jwt import authenticate_jwt
from app.repositories.similar_games_repo import SimilarGamesRepository
from app.schemas.similar_schema import SimilarGamesResponse
from app.services.similar_games_service import SimilarGamesService

router = APIRouter(
    prefix="/games",
    tags=["Similares"],
    dependencies=[Depends(authenticate_jwt)],
)

_LEADING_INTEGER = re.compile(r"^\s*[+-]?\d+")


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> SimilarGamesController:
    """Factory de dependencias: Repository → Service → Controller."""
    return SimilarGamesController(SimilarGamesService(SimilarGamesRepository(db)))


ControllerDep = Annotated[SimilarGamesController, Depends(get_controller)]


def parse_limit(value: str | None) -> int | None:
    """``limit`` opcional: si no es un entero positivo se devuelven todos."""
    if value is None:
        return None

    match = _LEADING_INTEGER.match(str(value))

    if not match:
        return None

    try:
        parsed = int(match.group(0))
    except ValueError:
        return None

    return parsed if parsed > 0 else None


@router.get("/{id}/similar", response_model=SimilarGamesResponse)
async def get_similar_games(
    id: int,
    ctrl: ControllerDep,
    limit: str | None = None,
):
    """Juegos similares del juego, ordenados por similitud descendente."""
    return await ctrl.get_similar_games(id, parse_limit(limit))
