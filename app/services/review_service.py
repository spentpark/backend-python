"""Lógica de negocio de la entidad Review."""
from typing import Any

from app.repositories.review_repo import ReviewRepository
from app.utils.pagination import build_paginated_response


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def get_reviews_by_game(
        self, game_id: int, page: int, limit: int
    ) -> dict[str, Any]:
        """Obtiene las reseñas de un juego con paginación."""
        rows, total = await self.repository.find_by_game_id_paginated(game_id, page, limit)
        return build_paginated_response(rows, total, page, limit)
