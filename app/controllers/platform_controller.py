"""Controlador HTTP de la entidad Platform."""
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException

from app.models.platform import Platform
from app.services.platform_service import PlatformService


class PlatformController:
    def __init__(self, service: PlatformService):
        self.service = service

    async def get_all_platforms(self) -> Sequence[Platform]:
        return await self.service.get_all()

    async def get_all_platforms_paginated(self, page: int, limit: int) -> dict[str, Any]:
        return await self.service.get_all_paginated(page, limit)

    async def get_platform_by_id(self, id: int) -> Platform:
        platform = await self.service.get_by_id(id)
        if not platform:
            raise HTTPException(status_code=404, detail="Plataforma no encontrada")
        return platform
