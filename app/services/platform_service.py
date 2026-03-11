from repositories.platform_repo import PlatformRepository

class PlatformService:
    def __init__(self, repository: PlatformRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.find_all()

    async def get_by_id(self, id: int):
        return await self.repository.find_by_id(id)
