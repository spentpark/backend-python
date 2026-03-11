from fastapi import HTTPException
from services.platform_service import PlatformService

class PlatformController:
    def __init__(self, service: PlatformService):
        self.service = service

    async def get_all_platforms(self):
        return await self.service.get_all()

    async def get_platform_by_id(self, id: int):
        platform = await self.service.get_by_id(id)
        if not platform:
            raise HTTPException(status_code=404, detail="Plataforma no encontrada")
        return platform
