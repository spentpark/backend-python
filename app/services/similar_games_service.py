"""Lógica de negocio de los juegos similares precalculados.

Réplica de ``similar-games.service.js`` de ``backend-node20``: parsea el JSON
de ``similar_game``, descarta entradas corruptas, excluye el propio juego,
ordena por similitud descendente y calcula el porcentaje redondeado.
"""
import json
import math
from typing import Any

from app.repositories.similar_games_repo import SimilarGamesRepository

PERCENTAGE_MULTIPLIER = 100
PERCENTAGE_DECIMALS = 2
PERCENTAGE_FACTOR = 10**PERCENTAGE_DECIMALS


class SimilarGamesParseError(Exception):
    """El campo ``json`` de ``similar_game`` no contiene un array válido."""


def to_similarity_percentage(similarity: float) -> float:
    """Convierte la similitud cruda (0–1) al porcentaje recortado a [0, 100]."""
    percentage = min(PERCENTAGE_MULTIPLIER, max(0.0, similarity * PERCENTAGE_MULTIPLIER))

    return round(percentage * PERCENTAGE_FACTOR) / PERCENTAGE_FACTOR


def to_similar_game(entry: Any) -> dict[str, Any] | None:
    """Normaliza una entrada del JSON; ``None`` si está corrupta."""
    if not isinstance(entry, dict):
        return None

    raw_id = entry.get("id")
    similarity = entry.get("similarity")

    if isinstance(raw_id, bool) or not isinstance(raw_id, int):
        return None

    if isinstance(similarity, bool) or not isinstance(similarity, (int, float)):
        return None

    if not math.isfinite(similarity):
        return None

    return {
        "id": raw_id,
        "title": entry.get("title"),
        "similarity": float(similarity),
        "similarityPercentage": to_similarity_percentage(float(similarity)),
    }


def parse_similar_games(raw_json: str | None) -> list[dict[str, Any]]:
    """Parsea el TEXT de ``similar_game`` y filtra entradas corruptas."""
    if raw_json is None or raw_json == "":
        return []

    try:
        entries = json.loads(raw_json)
    except (TypeError, ValueError) as error:
        raise SimilarGamesParseError("El campo json de similar_game no es JSON válido") from error

    if not isinstance(entries, list):
        raise SimilarGamesParseError('El campo "json" de similar_game no contiene un array')

    return [item for item in (to_similar_game(entry) for entry in entries) if item]


class SimilarGamesService:
    def __init__(self, repository: SimilarGamesRepository):
        self.repository = repository

    async def get_similar_games(
        self, game_id: int, limit: int | None = None
    ) -> dict[str, Any] | None:
        """Similares del juego; ``None`` si no hay fila o no quedan similares."""
        row = await self.repository.find_by_game_id(game_id)

        if row is None:
            return None

        similar_games = [
            game
            for game in parse_similar_games(row.json)
            # El propio juego aparece con similitud ~1 por definición.
            if game["id"] != game_id
        ]
        similar_games.sort(key=lambda game: game["similarity"], reverse=True)

        limited = similar_games[:limit] if limit and limit > 0 else similar_games

        if not limited:
            return None

        return {
            "gameId": game_id,
            "total": len(limited),
            "similarGames": limited,
        }
