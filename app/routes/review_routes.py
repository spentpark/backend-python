from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.review_repo import ReviewRepository
from app.services.review_service import ReviewService
from app.controllers.review_controller import ReviewController
from app.schemas.review_schema import ReviewResponse
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])

async def get_controller(db: AsyncSession = Depends(get_db)):
    repo = ReviewRepository(db)
    service = ReviewService(repo)
    return ReviewController(service)

@router.get("/{id}", response_model=List[ReviewResponse])
async def get_by_game_id(id: int, ctrl: ReviewController = Depends(get_controller)):
    # Nota: 'id' aquí representa el id del juego según tu lógica original
    return await ctrl.get_reviews(id)