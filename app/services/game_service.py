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
