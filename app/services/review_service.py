from app.repositories.review_repo import ReviewRepository

class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def get_reviews_by_game(self, game_id: int):
        return await self.repository.find_by_game_id(game_id)