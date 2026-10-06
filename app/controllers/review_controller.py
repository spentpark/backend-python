"""Controlador HTTP de la entidad Review."""
from collections.abc import Sequence

from fastapi import HTTPException

from app.models.review import Review
from app.services.review_service import ReviewService


class ReviewController:
    def __init__(self, service: ReviewService):
        self.service = service

    async def get_reviews(self, game_id: int) -> Sequence[Review]:
        rows = await self.service.get_reviews_by_game(game_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Reseñas no encontradas para este juego")
        return rows
