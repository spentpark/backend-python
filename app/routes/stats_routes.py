"""Endpoints de estadísticas del catálogo (``/api/stats``)."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.stats_controller import StatsController
from app.database import get_db
from app.middlewares.authenticate_jwt import authenticate_jwt
from app.repositories.stats_repo import StatsRepository
from app.schemas.stats_schema import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter(
    prefix="/stats",
    tags=["Estadísticas"],
    dependencies=[Depends(authenticate_jwt)],
)


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> StatsController:
    """Factory de dependencias: Repository → Service → Controller."""
    return StatsController(StatsService(StatsRepository(db)))


ControllerDep = Annotated[StatsController, Depends(get_controller)]


@router.get("", response_model=StatsResponse)
@router.get("/", response_model=StatsResponse, include_in_schema=False)
async def get_stats(ctrl: ControllerDep):
    """Totales y distribuciones por plataforma, género y década (caché 10 min)."""
    return await ctrl.get_stats()
