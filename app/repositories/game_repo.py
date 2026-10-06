"""Acceso a datos de la entidad Game (SQLAlchemy Async)."""
from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game


class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self) -> Sequence[Game]:
        result = await self.db.execute(select(Game))
        return result.scalars().all()

    async def find_by_id(self, id: int) -> Game | None:
        result = await self.db.execute(select(Game).where(Game.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Game:
        new_game = Game(**data)
        self.db.add(new_game)
        # El commit hace flush del INSERT y ya rellena la PK autoincremental,
        # por lo que un refresh() posterior sería un SELECT innecesario.
        await self.db.commit()
        return new_game

    async def update(self, id: int, data: dict) -> CursorResult:
        query = update(Game).where(Game.id == id).values(**data)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def delete(self, id: int) -> CursorResult:
        query = delete(Game).where(Game.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def find_by_title_paginated(
        self, title: str, page: int, limit: int
    ) -> tuple[Sequence[Game], int]:
        """Busca por prefijo de título y devuelve la página junto al total."""
        offset = max(page - 1, 0) * limit
        condition = Game.title.like(f"{title}%")

        result = await self.db.execute(
            select(Game).where(condition).limit(limit).offset(offset)
        )
        rows = result.scalars().all()

        # COUNT(*) es más rápido que COUNT(columna): no evalúa la columna.
        total_query = select(func.count()).select_from(Game).where(condition)
        total = (await self.db.execute(total_query)).scalar_one()

        return rows, total

    async def find_by_platform_paginated(
        self, platform: str, page: int, limit: int
    ) -> tuple[Sequence[Row], int]:
        """Filtra por plataforma y devuelve la página junto al total.

        Solo selecciona las columnas que expone el listado (id, title y
        Platform), evitando transferir columnas de texto pesadas que no se usan.
        """
        offset = max(page - 1, 0) * limit
        condition = Game.Platform == platform

        result = await self.db.execute(
            select(Game.id, Game.title, Game.Platform)
            .where(condition)
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()

        total_query = select(func.count()).select_from(Game).where(condition)
        total = (await self.db.execute(total_query)).scalar_one()

        return rows, total
