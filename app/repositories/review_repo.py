from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.review import Review

class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_game_id(self, game_id: int):
        # Tal cual tu query: SELECT * FROM review WHERE id_game = ?
        result = await self.db.execute(select(Review).where(Review.id_game == game_id))
        return result.scalars().all()