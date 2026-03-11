from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.platform import Platform

class PlatformRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        # Filtro original: url is not null
        result = await self.db.execute(select(Platform).where(Platform.url.isnot(None)))
        return result.scalars().all()

    async def find_by_id(self, id: int):
        result = await self.db.execute(select(Platform).where(Platform.id == id))
        return result.scalar_one_or_none()

    async def create(self, platform_data: dict):
        new_platform = Platform(**platform_data)
        self.db.add(new_platform)
        await self.db.commit()
        await self.db.refresh(new_platform)
        return new_platform

    async def update(self, id: int, data: dict):
        query = update(Platform).where(Platform.id == id).values(**data)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def delete(self, id: int):
        query = delete(Platform).where(Platform.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result