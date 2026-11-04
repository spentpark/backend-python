"""Endpoints REST de la entidad Platform (bajo ``/api/platforms``)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.platform_controller import PlatformController
from app.database import get_db
from app.middlewares.authenticate_jwt import authenticate_jwt, require_admin
from app.repositories.platform_repo import PlatformRepository
from app.schemas.platform_schema import (
    PaginatedPlatformResponse,
    PlatformCreate,
    PlatformResponse,
    TopGameItem,
)
from app.services.platform_service import PlatformService

router = APIRouter(
    prefix="/platforms",
    tags=["Platforms"],
    dependencies=[Depends(authenticate_jwt)],
)


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> PlatformController:
    """Factory de dependencias: construye Repository → Service → Controller."""
    return PlatformController(PlatformService(PlatformRepository(db)))


ControllerDep = Annotated[PlatformController, Depends(get_controller)]


@router.get("", response_model=PaginatedPlatformResponse)
# Alias con barra final: Node tolera `/api/platforms/` y `/api/platforms`.
@router.get("/", response_model=PaginatedPlatformResponse, include_in_schema=False)
async def get_all(
    ctrl: ControllerDep,
    page: Annotated[int, Query(ge=0)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await ctrl.get_all_platforms_paginated(page, limit)


@router.get("/{id}/top-games", response_model=list[TopGameItem])
async def get_top_games(id: int, ctrl: ControllerDep):
    """Top 10 juegos de la plataforma por nota Metacritic."""
    return await ctrl.get_top_games(id)


@router.get("/{id}", response_model=PlatformResponse)
async def get_by_id(id: int, ctrl: ControllerDep):
    return await ctrl.get_platform_by_id(id)


@router.post(
    "",
    response_model=PlatformResponse,
    dependencies=[Depends(require_admin)],
)
# Alias con barra final: Node tolera `/api/platforms/` y `/api/platforms`.
@router.post(
    "/",
    response_model=PlatformResponse,
    dependencies=[Depends(require_admin)],
    include_in_schema=False,
)
async def create(data: PlatformCreate, ctrl: ControllerDep):
    return await ctrl.create_platform(data)


@router.put("/{id}", dependencies=[Depends(require_admin)])
async def update(id: int, data: PlatformCreate, ctrl: ControllerDep):
    return await ctrl.update_platform(id, data)


@router.delete("/{id}", dependencies=[Depends(require_admin)])
async def delete(id: int, ctrl: ControllerDep):
    return await ctrl.delete_platform(id)
