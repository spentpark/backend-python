from fastapi import HTTPException
from app.services.game_service import GameService

class GameController:
    def __init__(self, service: GameService):
        self.service = service

    async def get_all_games(self):
        return await self.service.get_all()

    async def get_game_by_id(self, id: int):
        game = await self.service.get_by_id(id)
        if not game:
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        return game


    async def search_by_title(self, title: str, page: int, limit: int):
        if not title:
            raise HTTPException(status_code=400, detail="El parámetro 'title' es requerido")
        return await self.service.get_by_title(title, page, limit)

    async def filter_by_platform(self, platform: str, page: int, limit: int):
        return await self.service.get_by_platform(platform, page, limit)