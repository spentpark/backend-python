from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.models.game import Game

class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        result = await self.db.execute(select(Game))
        return result.scalars().all()

    async def find_by_id(self, id: int):
        result = await self.db.execute(select(Game).where(Game.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: dict):
        new_game = Game(**data)
        self.db.add(new_game)
        await self.db.commit()
        await self.db.refresh(new_game)
        return new_game

    async def update(self, id: int, data: dict):
        query = update(Game).where(Game.id == id).values(**data)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def delete(self, id: int):
        query = delete(Game).where(Game.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def find_by_title_paginated(self, title: str, page: int, limit: int):
        offset = (page - 1) * limit
        search_term = f"{title}%"
        
        # Obtener registros
        query = select(Game).where(Game.title.like(search_term)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        rows = result.scalars().all()

        # Obtener total
        total_query = select(func.count(Game.id)).where(Game.title.like(search_term))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        return rows, total

    async def find_by_platform_paginated(self, platform: str, page: int, limit: int):
        offset = (page - 1) * limit
        
        query = select(Game).where(Game.Platform == platform).limit(limit).offset(offset)
        result = await self.db.execute(query)
        rows = result.scalars().all()

        total_query = select(func.count(Game.id)).where(Game.Platform == platform)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        return rows, total