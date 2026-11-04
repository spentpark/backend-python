"""Controlador HTTP de autenticación (login y datos del token)."""
import logging

from fastapi import HTTPException

from app.middlewares.authenticate_jwt import AuthUser
from app.services import auth_service

logger = logging.getLogger(__name__)

MAX_USERNAME_LENGTH = 100
MAX_PASSWORD_LENGTH = 200

MISSING_CREDENTIALS_MESSAGE = "Usuario y contraseña son obligatorios"
INVALID_CREDENTIALS_MESSAGE = "Credenciales inválidas"
LOGIN_ERROR_MESSAGE = "Error al iniciar sesión"


class AuthController:
    async def login(self, username: str | None, password: str | None) -> dict[str, str]:
        """Valida las credenciales y devuelve el JWT emitido."""
        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or not username
            or not password
        ):
            raise HTTPException(status_code=400, detail=MISSING_CREDENTIALS_MESSAGE)

        if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            raise HTTPException(status_code=400, detail=INVALID_CREDENTIALS_MESSAGE)

        try:
            user = auth_service.login(username, password)
        except Exception as error:
            logger.exception("Error al validar las credenciales: %s", error)
            raise HTTPException(status_code=500, detail=LOGIN_ERROR_MESSAGE) from error

        if user is None:
            raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)

        try:
            return auth_service.issue_token(user)
        except RuntimeError as error:
            logger.exception("Configuración JWT inválida: %s", error)
            raise HTTPException(status_code=500, detail=LOGIN_ERROR_MESSAGE) from error

    def me(self, user: AuthUser) -> dict[str, str]:
        """Devuelve el usuario y rol del token autenticado."""
        return {"username": user.username, "role": user.role}
