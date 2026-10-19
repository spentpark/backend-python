"""Endpoints REST de la entidad Review."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.review_controller import ReviewController
from app.database import get_db
from app.repositories.review_repo import ReviewRepository
from app.schemas.review_schema import PaginatedReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> ReviewController:
    """Factory de dependencias: construye Repository ? Service ? Controller."""
    return ReviewController(ReviewService(ReviewRepository(db)))


ControllerDep = Annotated[ReviewController, Depends(get_controller)]


@router.get("/{id}", response_model=PaginatedReviewResponse)
async def get_by_game_id(
    id: int,
    ctrl: ControllerDep,
    page: Annotated[int, Query(ge=0)] = 1,
    # El detalle del juego muestra las reseñas de 10 en 10.
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await ctrl.get_reviews(id, page, limit)
