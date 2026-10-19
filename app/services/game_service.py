"""Lógica de negocio de la entidad Game."""
from collections.abc import Sequence
from typing import Any

from app.models.game import Game
from app.repositories.game_repo import GameRepository
from app.utils.pagination import build_paginated_response


class GameService:
    def __init__(self, repository: GameRepository):
        self.repository = repository

    async def get_all(self) -> Sequence[Game]:
        return await self.repository.find_all()

    async def get_by_id(self, id: int) -> Game | None:
        return await self.repository.find_by_id(id)

    async def get_by_title(self, title: str, page: int, limit: int) -> dict[str, Any]:
        """Busca juegos por prefijo de título con paginación."""
        rows, total = await self.repository.find_by_title_paginated(title, page, limit)
        return build_paginated_response(rows, total, page, limit)

    async def get_by_platform(self, platform: str, page: int, limit: int) -> dict[str, Any]:
        """Filtra juegos por plataforma con paginación."""
        rows, total = await self.repository.find_by_platform_paginated(platform, page, limit)
        return build_paginated_response(rows, total, page, limit)

    async def create(self, data: dict[str, Any]) -> Game:
        """Crea un juego y devuelve la entidad persistida."""
        return await self.repository.create(data)

    async def update(self, id: int, data: dict[str, Any]) -> Game | None:
        """Actualiza un juego; devuelve None si el id no existe."""
        result = await self.repository.update(id, data)
        if result.rowcount == 0:
            return None
        return await self.repository.find_by_id(id)

    async def delete(self, id: int) -> bool:
        """Elimina un juego; devuelve False si el id no existía."""
        result = await self.repository.delete(id)
        return result.rowcount > 0