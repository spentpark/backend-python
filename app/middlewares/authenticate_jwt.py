"""Dependencias de autenticación y autorización para FastAPI.

Réplica del ``authenticate-jwt.js`` de ``backend-node20``:

- ``authenticate_jwt`` exige un JWT HS256 válido y expone ``AuthUser``.
- ``require_role``/``require_admin`` exigen el rol adecuado para escrituras.

Los errores replican el contrato de Node: 401 ``{"error": "No autorizado"}``
con cabecera ``WWW-Authenticate: Bearer`` y 403 ``{"error": "Acceso denegado"}``.
"""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services import auth_service

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT HS256 emitido por POST /api/auth/login",
)


@dataclass(frozen=True)
class AuthUser:
    """Usuario autenticado extraído del token."""

    username: str
    role: str


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="No autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authenticate_jwt(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthUser:
    """Exige ``Authorization: Bearer <jwt>`` y devuelve el usuario del token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    token = credentials.credentials.strip()

    if not token:
        raise _unauthorized()

    try:
        payload = auth_service.verify_token(token)
    except auth_service.AuthError as error:
        raise _unauthorized() from error

    return AuthUser(username=payload["username"], role=payload["role"])


CurrentUser = Annotated[AuthUser, Depends(authenticate_jwt)]


def require_role(*roles: str):
    """Fábrica de dependencias que exige alguno de los roles indicados."""

    async def dependency(user: CurrentUser) -> AuthUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Acceso denegado")

        return user

    return dependency


require_admin = require_role("admin")
