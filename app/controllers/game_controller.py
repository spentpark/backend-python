"""Controlador HTTP de la entidad Game."""
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException

from app.models.game import Game
from app.repositories.game_repo import has_advanced_filters
from app.schemas.game_schema import GameCreate
from app.services.game_service import GameService

TITLE_REQUIRED_MESSAGE = 'El parámetro "title" es requerido'


def build_filters(
    platform: str | None = None,
    genre: str | None = None,
    year: str | None = None,
    decade: str | None = None,
    players: str | None = None,
    sort: str | None = None,
) -> dict[str, str]:
    """Construye el diccionario de filtros con los valores no vacíos."""
    candidates = {
        "platform": platform,
        "genre": genre,
        "year": year,
        "decade": decade,
        "players": players,
        "sort": sort,
    }

    return {key: value for key, value in candidates.items() if value}


class GameController:
    def __init__(self, service: GameService):
        self.service = service

    async def get_all_games(self) -> Sequence[Game]:
        return await self.service.get_all()

    async def get_game_by_id(self, id: int) -> Game:
        game = await self.service.get_by_id(id)
        if not game:
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        return game

    async def search_by_title(
        self, title: str | None, page: int, limit: int
    ) -> dict[str, Any]:
        if not title:
            raise HTTPException(status_code=400, detail=TITLE_REQUIRED_MESSAGE)
        return await self.service.get_by_title(title, page, limit)

    async def filter_games(
        self, filters: dict[str, str], page: int, limit: int
    ) -> dict[str, Any]:
        """Listado del catálogo: camino clásico por plataforma o filtros avanzados."""
        if has_advanced_filters(filters):
            return await self.service.get_filtered_paginated(filters, page, limit)

        return await self.service.get_by_platform(filters.get("platform"), page, limit)

    async def get_random_game(self, filters: dict[str, str] | None = None) -> Game:
        """Devuelve un juego al azar con tráiler; 404 si la colección no tiene ninguno."""
        game = await self.service.get_random_with_trailer(filters)
        if not game:
            raise HTTPException(
                status_code=404, detail="No hay ningún juego con tráiler disponible"
            )
        return game

    async def create_game(self, data: GameCreate) -> Game:
        """Crea un juego a partir del contrato de entrada."""
        return await self.service.create(data.model_dump())

    async def update_game(self, id: int, data: GameCreate) -> Game:
        """Actualiza un juego; lanza 404 si el id no existe."""
        game = await self.service.update(id, data.model_dump())
        if not game:
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        return game

    async def delete_game(self, id: int) -> dict[str, bool]:
        """Elimina un juego; lanza 404 si el id no existe."""
        if not await self.service.delete(id):
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        return {"deleted": True}
