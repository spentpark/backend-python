"""Controlador HTTP de la entidad Platform."""
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException

from app.models.platform import Platform
from app.schemas.platform_schema import PlatformCreate
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

    async def create_platform(self, data: PlatformCreate) -> Platform:
        """Crea una plataforma a partir del contrato de entrada."""
        return await self.service.create(data.model_dump())

    async def update_platform(self, id: int, data: PlatformCreate) -> Platform:
        """Actualiza una plataforma; lanza 404 si el id no existe."""
        platform = await self.service.update(id, data.model_dump())
        if not platform:
            raise HTTPException(status_code=404, detail="Plataforma no encontrada")
        return platform

    async def delete_platform(self, id: int) -> dict[str, bool]:
        """Elimina una plataforma; lanza 404 si el id no existe."""
        if not await self.service.delete(id):
            raise HTTPException(status_code=404, detail="Plataforma no encontrada")
        return {"deleted": True}