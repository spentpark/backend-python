from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repositories.platform_repo import PlatformRepository
from services.platform_service import PlatformService
from controllers.platform_controller import PlatformController
from schemas.platform_schema import PlatformCreate, PlatformResponse
from typing import List

router = APIRouter(prefix="/platforms", tags=["Platforms"])

# Inyección de dependencias para obtener el controlador configurado
async def get_controller(db: AsyncSession = Depends(get_db)):
    repo = PlatformRepository(db)
    service = PlatformService(repo)
    return PlatformController(service)

@router.get("/", response_model=List[PlatformResponse])
async def get_all(ctrl: PlatformController = Depends(get_controller)):
    return await ctrl.get_all_platforms()

@router.get("/{id}", response_model=PlatformResponse)
async def get_by_id(id: int, ctrl: PlatformController = Depends(get_controller)):
    return await ctrl.get_platform_by_id(id)

@router.post("/", response_model=PlatformResponse)
async def create(data: PlatformCreate, ctrl: PlatformController = Depends(get_controller)):
    return await ctrl.create_platform(data)

@router.put("/{id}")
async def update(id: int, data: PlatformCreate, ctrl: PlatformController = Depends(get_controller)):
    return await ctrl.update_platform(id, data)

@router.delete("/{id}")
async def delete(id: int, ctrl: PlatformController = Depends(get_controller)):
    return await ctrl.delete_platform(id)