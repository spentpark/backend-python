"""Acceso a datos de la entidad Platform (SQLAlchemy Async)."""
from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Platform


class PlatformRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self) -> Sequence[Platform]:
        # Filtro original: url is not null
        result = await self.db.execute(select(Platform).where(Platform.url.isnot(None)))
        return result.scalars().all()

    async def find_all_paginated(
        self, page: int, limit: int
    ) -> tuple[Sequence[Platform], int]:
        """Lista plataformas con `url` no nulo, paginadas, junto al total."""
        # max() evita un OFFSET negativo si el cliente envía page <= 0
        offset = max(page - 1, 0) * limit
        condition = Platform.url.isnot(None)

        result = await self.db.execute(
            select(Platform).where(condition).limit(limit).offset(offset)
        )
        rows = result.scalars().all()

        total_query = select(func.count()).select_from(Platform).where(condition)
        total = (await self.db.execute(total_query)).scalar_one()

        return rows, total

    async def find_by_id(self, id: int) -> Platform | None:
        result = await self.db.execute(select(Platform).where(Platform.id == id))
        return result.scalar_one_or_none()

    async def create(self, platform_data: dict) -> Platform:
        new_platform = Platform(**platform_data)
        self.db.add(new_platform)
        # El commit hace flush del INSERT y ya rellena la PK autoincremental.
        await self.db.commit()
        return new_platform

    async def update(self, id: int, data: dict) -> CursorResult:
        query = update(Platform).where(Platform.id == id).values(**data)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def delete(self, id: int) -> CursorResult:
        query = delete(Platform).where(Platform.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result
