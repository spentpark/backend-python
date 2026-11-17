"""Acceso a datos de la tabla ``similar_game`` (SQLAlchemy Async)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.similar_game import SimilarGame


class SimilarGamesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_game_id(self, id_game: int) -> SimilarGame | None:
        """Fila de similares del juego indicado (``id_game`` es la PK)."""
        query = select(SimilarGame).where(SimilarGame.id_game == id_game)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()
