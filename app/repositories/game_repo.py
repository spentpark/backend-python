"""Acceso a datos de la entidad Game (SQLAlchemy Async)."""
import random
from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game

# Intentos de búsqueda de un id al azar con tráiler antes de rendirse. La tabla
# `games` no tiene índice sobre `youtube_Trailer`, así que se evita cualquier
# filtro o `COUNT(*)`: con ~1,4 GB, escanearla completa tarda más de un minuto.
_RANDOM_ATTEMPTS = 15


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

    async def find_random_with_trailer(self) -> Game | None:
        """Devuelve un juego al azar que tenga tráiler, o None si no hay ninguno.

        No se usa `COUNT(*)` ni `ORDER BY RAND()`: la tabla `games` es muy grande
        (~1,4 GB y sin índice sobre `youtube_Trailer`) y cualquier consulta que
        la recorra completa tarda más de un minuto. En su lugar se elige un id al
        azar dentro del rango de la clave primaria y se consulta por PK; si el id
        no existe o el juego no tiene tráiler, se reintenta.
        """
        bounds = await self._id_bounds()

        if bounds is None:
            return None

        min_id, max_id = bounds

        for _ in range(_RANDOM_ATTEMPTS):
            candidate = random.randint(min_id, max_id)

            result = await self.db.execute(select(Game).where(Game.id == candidate))
            game = result.scalar_one_or_none()

            if game and game.youtube_Trailer:
                return game

        return None

    async def _id_bounds(self) -> tuple[int, int] | None:
        """Rango de ids usando el índice de la PK (MIN/MAX tardan segundos aquí)."""
        first = await self.db.execute(select(Game.id).order_by(Game.id).limit(1))
        last = await self.db.execute(select(Game.id).order_by(Game.id.desc()).limit(1))

        min_id = first.scalar_one_or_none()
        max_id = last.scalar_one_or_none()

        if min_id is None or max_id is None:
            return None

        return min_id, max_id
