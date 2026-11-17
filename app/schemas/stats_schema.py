"""Contratos Pydantic de las estadísticas del catálogo."""
from pydantic import BaseModel


class StatsSummary(BaseModel):
    """Totales generales del catálogo."""

    totalGames: int
    scoredGames: int
    totalPlatforms: int
    totalGenres: int


class StatsDistribution(BaseModel):
    """Entrada de una distribución (plataforma, género o década)."""

    label: str
    total: int


class StatsResponse(BaseModel):
    """Respuesta de ``GET /api/stats``."""

    summary: StatsSummary
    platforms: list[StatsDistribution]
    genres: list[StatsDistribution]
    decades: list[StatsDistribution]
