from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Imports con prefijo app.
from app.database import get_db
from app.repositories.review_repo import ReviewRepository
from app.services.review_service import ReviewService
from app.controllers.review_controller import ReviewController
from app.schemas.review_schema import ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])

async def get_controller(db: AsyncSession = Depends(get_db)):
    repo = ReviewRepository(db)
    service = ReviewService(repo)
    return ReviewController(service)

@router.get("/{id}", response_model=List[ReviewResponse])
async def get_by_game_id(id: int, ctrl: ReviewController = Depends(get_controller)):
    return await ctrl.get_reviews(id)
