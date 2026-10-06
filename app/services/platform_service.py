"""Lógica de negocio de la entidad Platform."""
from collections.abc import Sequence
from typing import Any

from app.models.platform import Platform
from app.repositories.platform_repo import PlatformRepository
from app.utils.pagination import build_paginated_response


class PlatformService:
    def __init__(self, repository: PlatformRepository):
        self.repository = repository

    async def get_all(self) -> Sequence[Platform]:
        return await self.repository.find_all()

    async def get_all_paginated(self, page: int, limit: int) -> dict[str, Any]:
        """Lista plataformas con paginación."""
        rows, total = await self.repository.find_all_paginated(page, limit)
        return build_paginated_response(rows, total, page, limit)

    async def get_by_id(self, id: int) -> Platform | None:
        return await self.repository.find_by_id(id)
