"""Lógica de negocio de las estadísticas del catálogo.

La respuesta se cachea 10 minutos porque los ``GROUP BY`` sobre la tabla
remota son costosos, igual que en el backend Node. Las peticiones concurrentes
comparten el mismo cálculo en vuelo y un error no se cachea.
"""
import asyncio
import time
from typing import Any

from app.repositories.stats_repo import StatsRepository

CACHE_TTL_SECONDS = 10 * 60

_cache: dict[str, Any] | None = None
_cache_expires_at = 0.0
_pending: "asyncio.Task[dict[str, Any]] | None" = None


def clear_stats_cache() -> None:
    """Vacía la caché de estadísticas (solo pruebas y utilidades)."""
    global _cache, _cache_expires_at, _pending

    _cache = None
    _cache_expires_at = 0.0
    _pending = None


def peek_stats() -> dict[str, Any] | None:
    """Devuelve las estadísticas solo si ya están en caché, sin consultar la BD."""
    if _cache is not None and _cache_expires_at > time.monotonic():
        return _cache

    return None


class StatsService:
    def __init__(self, repository: StatsRepository):
        self.repository = repository

    async def get_stats(self) -> dict[str, Any]:
        """Estadísticas del catálogo con caché en memoria de 10 minutos."""
        global _pending

        cached = peek_stats()

        if cached is not None:
            return cached

        if _pending is None:
            _pending = asyncio.create_task(self._load_and_cache())

        # `shield` evita que la cancelación de un cliente aborte el cálculo que
        # comparten el resto de peticiones concurrentes.
        return await asyncio.shield(_pending)

    async def _load_and_cache(self) -> dict[str, Any]:
        global _cache, _cache_expires_at, _pending

        try:
            data = await self._load()
            _cache = data
            _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS
            return data
        finally:
            _pending = None

    async def _load(self) -> dict[str, Any]:
        summary = await self.repository.get_summary()
        platforms = await self.repository.get_games_by_platform()
        genres = await self.repository.get_games_by_genre()
        decades = await self.repository.get_games_by_decade()

        return {
            "summary": {
                "totalGames": summary["totalGames"],
                "scoredGames": summary["scoredGames"],
                "totalPlatforms": summary["totalPlatforms"] or len(platforms),
                "totalGenres": summary["totalGenres"] or len(genres),
            },
            "platforms": platforms,
            "genres": genres,
            "decades": decades,
        }
