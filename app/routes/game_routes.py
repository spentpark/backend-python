from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.game_repo import GameRepository
from app.services.game_service import GameService
from app.controllers.game_controller import GameController
from app.schemas.game_schema import GameCreate, GameResponse, PaginatedGameResponse
from typing import List, Optional

router = APIRouter(prefix="/games", tags=["Games"])

async def get_controller(db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    service = GameService(repo)
    return GameController(service)

# Rutas específicas primero (como en tu Express router)
@router.get("/search", response_model=PaginatedGameResponse)
async def search(
    title: str, 
    page: int = 1, 
    limit: int = 10, 
    ctrl: GameController = Depends(get_controller)
):
    return await ctrl.search_by_title(title, page, limit)

@router.get("/", response_model=PaginatedGameResponse)
async def get_all(
    platform: Optional[str] = None, 
    page: int = Query(1, alias="page"), 
    limit: int = Query(10, alias="limit"), 
    ctrl: GameController = Depends(get_controller)
):
    # Si no hay plataforma, podrías adaptar para que devuelva todos paginados
    return await ctrl.filter_by_platform(platform, page, limit)

@router.get("/{id}", response_model=GameResponse)
async def get_by_id(id: int, ctrl: GameController = Depends(get_controller)):
    return await ctrl.get_game_by_id(id)

@router.post("/", response_model=GameResponse, status_code=201)
async def create(data: GameCreate, ctrl: GameController = Depends(get_controller)):
    return await ctrl.create_game(data)

@router.put("/{id}")
async def update(id: int, data: GameCreate, ctrl: GameController = Depends(get_controller)):
    return await ctrl.update_game(id, data)

@router.delete("/{id}")
async def delete(id: int, ctrl: GameController = Depends(get_controller)):
    return await ctrl.delete_game(id)