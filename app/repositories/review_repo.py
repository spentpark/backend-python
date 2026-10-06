"""Acceso a datos de la entidad Review (SQLAlchemy Async)."""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_game_id(self, game_id: int) -> Sequence[Review]:
        """Devuelve todas las reseñas asociadas a un juego."""
        result = await self.db.execute(select(Review).where(Review.id_game == game_id))
        return result.scalars().all()
