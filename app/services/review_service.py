"""Lógica de negocio de la entidad Review."""
from collections.abc import Sequence

from app.models.review import Review
from app.repositories.review_repo import ReviewRepository


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def get_reviews_by_game(self, game_id: int) -> Sequence[Review]:
        """Obtiene las reseñas de un juego."""
        return await self.repository.find_by_game_id(game_id)
