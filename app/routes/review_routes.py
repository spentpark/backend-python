"""Endpoints REST de la entidad Review."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.review_controller import ReviewController
from app.database import get_db
from app.repositories.review_repo import ReviewRepository
from app.schemas.review_schema import ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> ReviewController:
    """Factory de dependencias: construye Repository → Service → Controller."""
    return ReviewController(ReviewService(ReviewRepository(db)))


ControllerDep = Annotated[ReviewController, Depends(get_controller)]


@router.get("/{id}", response_model=list[ReviewResponse])
async def get_by_game_id(id: int, ctrl: ControllerDep):
    return await ctrl.get_reviews(id)
