"""Acceso a datos de la entidad Review (SQLAlchemy Async)."""
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_game_id_paginated(
        self, game_id: int, page: int, limit: int
    ) -> tuple[Sequence[Review], int]:
        """Devuelve la página de reseñas de un juego junto al total de reseñas.

        Se ordena por `id` para que el resultado de cada página sea estable
        y no se repitan ni se pierdan reseñas al avanzar.
        """
        offset = max(page - 1, 0) * limit
        condition = Review.id_game == game_id

        result = await self.db.execute(
            select(Review)
            .where(condition)
            .order_by(Review.id)
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()

        # COUNT(*) es más rápido que COUNT(columna): no evalúa la columna.
        total_query = select(func.count()).select_from(Review).where(condition)
        total = (await self.db.execute(total_query)).scalar_one()

        return rows, total
