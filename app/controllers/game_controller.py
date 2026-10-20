"""Controlador HTTP de la entidad Game."""
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException

from app.models.game import Game
from app.schemas.game_schema import GameCreate
from app.services.game_service import GameService


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

    async def search_by_title(self, title: str, page: int, limit: int) -> dict[str, Any]:
        if not title:
            raise HTTPException(status_code=400, detail="El parámetro 'title' es requerido")
        return await self.service.get_by_title(title, page, limit)

    async def filter_by_platform(self, platform: str, page: int, limit: int) -> dict[str, Any]:
        return await self.service.get_by_platform(platform, page, limit)

    async def get_random_game(self) -> Game:
        """Devuelve un juego al azar con tráiler; 404 si la colección no tiene ninguno."""
        game = await self.service.get_random_with_trailer()
        if not game:
            raise HTTPException(status_code=404, detail="No hay juegos con tráiler disponible")
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