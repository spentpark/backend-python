"""Endpoints de autenticación (``/api/auth``)."""
from fastapi import APIRouter, Depends, Response

from app.controllers.auth_controller import AuthController
from app.middlewares.authenticate_jwt import CurrentUser, authenticate_jwt
from app.schemas.auth_schema import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])

controller = AuthController()

NO_STORE_HEADERS = {"Cache-Control": "no-store", "Pragma": "no-cache"}


def _set_no_store(response: Response) -> None:
    """Evita que el token quede en cachés intermedias o del navegador."""
    for name, value in NO_STORE_HEADERS.items():
        response.headers[name] = value


@router.post("/login", response_model=LoginResponse)
async def login(response: Response, data: LoginRequest | None = None):
    """Valida usuario y contraseña (hash bcrypt) y emite un JWT HS256."""
    username = data.username if data else None
    password = data.password if data else None

    issued = await controller.login(username, password)
    _set_no_store(response)

    return issued


@router.get("/me", response_model=MeResponse, dependencies=[Depends(authenticate_jwt)])
async def get_me(user: CurrentUser, response: Response):
    """Devuelve ``{username, role}`` a partir del JWT recibido."""
    _set_no_store(response)

    return controller.me(user)
