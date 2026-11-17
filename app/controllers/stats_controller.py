"""Controlador HTTP de las estadísticas del catálogo."""
import logging
from typing import Any

from fastapi import HTTPException

from app.services.stats_service import StatsService

logger = logging.getLogger(__name__)

STATS_ERROR_MESSAGE = "Error al obtener las estadísticas del catálogo"


class StatsController:
    def __init__(self, service: StatsService):
        self.service = service

    async def get_stats(self) -> dict[str, Any]:
        """Estadísticas del catálogo (cacheadas 10 minutos en el servicio)."""
        try:
            return await self.service.get_stats()
        except Exception as error:
            logger.exception("Error al obtener las estadísticas del catálogo: %s", error)
            raise HTTPException(status_code=500, detail=STATS_ERROR_MESSAGE) from error
