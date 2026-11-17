"""Endpoints de utilidades (``/api/saludo`` y ``/api/hello``)."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.main_controller import MainController
from app.database import get_db
from app.repositories.main_repo import MainRepository

router = APIRouter(tags=["Utilidades"])


def get_controller(db: Annotated[AsyncSession, Depends(get_db)]) -> MainController:
    """Factory de dependencias: Repository → Controller."""
    return MainController(MainRepository(db))


ControllerDep = Annotated[MainController, Depends(get_controller)]


@router.get("/saludo")
async def saludo(ctrl: ControllerDep):
    """Mensaje de bienvenida fijo (no consulta la base de datos)."""
    return ctrl.saludo()


@router.get("/hello")
async def hello(ctrl: ControllerDep):
    """Health-check de la base de datos: devuelve la fecha del servidor."""
    return await ctrl.hello()
