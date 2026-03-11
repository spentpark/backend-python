import math
from app.repositories.game_repo import GameRepository

class GameService:
    def __init__(self, repository: GameRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.find_all()

    async def get_by_id(self, id: int):
        return await self.repository.find_by_id(id)

    async def get_by_title(self, title: str, page: int, limit: int):
        rows, total = await self.repository.find_by_title_paginated(title, page, limit)
        return self._format_paginated_response(rows, total, page, limit)

    async def get_by_platform(self, platform: str, page: int, limit: int):
        rows, total = await self.repository.find_by_platform_paginated(platform, page, limit)
        return self._format_paginated_response(rows, total, page, limit)

    def _format_paginated_response(self, rows, total, page, limit):
        return {
            "data": rows,
            "pagination": {
                "currentPage": page,
                "perPage": limit,
                "totalRecords": total,
                "totalPages": math.ceil(total / limit) if total > 0 else 0
            }
        }