"""Controlador HTTP de los juegos similares."""
import logging
from typing import Any

from fastapi import HTTPException

from app.services.similar_games_service import SimilarGamesParseError, SimilarGamesService

logger = logging.getLogger(__name__)

SIMILAR_NOT_FOUND_MESSAGE = "No se encontraron juegos similares para el juego indicado"
SIMILAR_ERROR_MESSAGE = "Error al obtener juegos similares"


class SimilarGamesController:
    def __init__(self, service: SimilarGamesService):
        self.service = service

    async def get_similar_games(
        self, game_id: int, limit: int | None = None
    ) -> dict[str, Any]:
        """Similares paginados/filtrados por ``limit``; 404 si no hay datos."""
        try:
            result = await self.service.get_similar_games(game_id, limit)
        except SimilarGamesParseError as error:
            logger.exception("El JSON de similar_game es inválido: %s", error)
            raise HTTPException(status_code=500, detail=SIMILAR_ERROR_MESSAGE) from error

        if result is None:
            raise HTTPException(status_code=404, detail=SIMILAR_NOT_FOUND_MESSAGE)

        return result
