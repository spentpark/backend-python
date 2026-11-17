"""Contratos Pydantic de autenticación."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credenciales de ``POST /api/auth/login``.

    Los campos son opcionales para que la validación (mensaje en español) la
    haga el controlador y no FastAPI/Pydantic.
    """

    username: str | None = None
    password: str | None = None


class LoginResponse(BaseModel):
    """Token emitido por el login."""

    token: str
    tokenType: str = "Bearer"
    expiresAt: str


class MeResponse(BaseModel):
    """Usuario y rol del token (``GET /api/auth/me``)."""

    username: str
    role: str
