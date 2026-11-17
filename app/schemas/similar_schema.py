"""Contratos Pydantic de juegos similares (``similar_game``)."""
from pydantic import BaseModel


class SimilarGameItem(BaseModel):
    """Juego similar con su similitud cruda y en porcentaje."""

    id: int
    title: str | None = None
    similarity: float
    similarityPercentage: float


class SimilarGamesResponse(BaseModel):
    """Respuesta de ``GET /api/games/{id}/similar``."""

    gameId: int
    total: int
    similarGames: list[SimilarGameItem]
