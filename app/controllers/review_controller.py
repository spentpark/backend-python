"""Controlador HTTP de la entidad Review."""
from typing import Any

from fastapi import HTTPException

from app.services.review_service import ReviewService


class ReviewController:
    def __init__(self, service: ReviewService):
        self.service = service

    async def get_reviews(self, game_id: int, page: int, limit: int) -> dict[str, Any]:
        """Devuelve las reseñas paginadas de un juego.

        Lanza 404 solo cuando el juego no tiene ninguna reseña; una página
        fuera de rango se responde con `data` vacía y su paginación.
        """
        result = await self.service.get_reviews_by_game(game_id, page, limit)

        if result["pagination"]["totalRecords"] == 0:
            raise HTTPException(
                status_code=404, detail="Reseñas no encontradas para este juego"
            )

        return result
