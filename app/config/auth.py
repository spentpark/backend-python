"""Configuración de autenticación JWT.

Replica el esquema de ``backend-node20``/``rss-game-node``: mismo secreto,
``issuer``, ``audience`` y claim ``role``, de modo que un token emitido por
cualquiera de los servicios es aceptado por los demás.

Variables de entorno:

- ``JWT_SECRET``: secreto HS256 (obligatorio en producción).
- ``JWT_EXPIRES_IN``: vida del token (por defecto ``1h``).
- ``JWT_ISSUER``: emisor emitido y esperado (por defecto ``rss-game-node``).
- ``JWT_AUDIENCE``: audiencia emitida y esperada (``rss-game-node-api``).
- ``AUTH_USERNAME``: usuario del login (por defecto ``admin``).
- ``AUTH_ROLE``: rol del usuario (por defecto ``admin``).
- ``AUTH_PASSWORD_HASH``: hash bcrypt de la contraseña.
- ``ENVIRONMENT`` / ``NODE_ENV``: ``production`` activa el modo fail-closed.
"""
import logging
import os

MIN_SECRET_LENGTH = 32
DEFAULT_EXPIRES_IN = "1h"
DEFAULT_ISSUER = "rss-game-node"
DEFAULT_AUDIENCE = "rss-game-node-api"
DEFAULT_USERNAME = "admin"
DEFAULT_ROLE = "admin"

logger = logging.getLogger(__name__)


def is_production() -> bool:
    """``True`` si el entorno activo es producción (``ENVIRONMENT`` o ``NODE_ENV``)."""
    environment = os.getenv("ENVIRONMENT") or os.getenv("NODE_ENV") or "development"
    return environment.strip().lower() == "production"


def get_jwt_secret() -> str:
    """Secreto HS256 configurado (cadena vacía si no existe)."""
    return os.getenv("JWT_SECRET") or ""


def get_jwt_secret_or_raise() -> str:
    """Secreto HS256 obligatorio; lanza si no está configurado."""
    secret = get_jwt_secret()

    if not secret:
        raise RuntimeError("JWT_SECRET no está configurado")

    return secret


def get_sign_options() -> dict[str, str]:
    """Opciones de firma del token (vida, emisor y audiencia)."""
    return {
        "expires_in": os.getenv("JWT_EXPIRES_IN") or DEFAULT_EXPIRES_IN,
        "issuer": os.getenv("JWT_ISSUER") or DEFAULT_ISSUER,
        "audience": os.getenv("JWT_AUDIENCE") or DEFAULT_AUDIENCE,
    }


def get_verify_options() -> dict[str, str]:
    """Opciones de verificación del token (emisor y audiencia esperados)."""
    return {
        "issuer": os.getenv("JWT_ISSUER") or DEFAULT_ISSUER,
        "audience": os.getenv("JWT_AUDIENCE") or DEFAULT_AUDIENCE,
    }


def get_configured_user() -> dict[str, str]:
    """Usuario estático configurado por entorno."""
    return {
        "username": os.getenv("AUTH_USERNAME") or DEFAULT_USERNAME,
        "role": os.getenv("AUTH_ROLE") or DEFAULT_ROLE,
        "password_hash": os.getenv("AUTH_PASSWORD_HASH") or "",
    }


def validate_auth_configuration() -> bool:
    """Comprueba la configuración JWT al arrancar.

    En producción falla cerrado si falta el secreto o el hash de la contraseña;
    en desarrollo solo emite un aviso. Devuelve ``True`` si la configuración
    está completa.
    """
    missing = []

    if not get_jwt_secret():
        missing.append("JWT_SECRET")

    if not (os.getenv("AUTH_PASSWORD_HASH") or ""):
        missing.append("AUTH_PASSWORD_HASH")

    if missing:
        if is_production():
            raise RuntimeError(
                "Configuración de autenticación incompleta: " + ", ".join(missing)
            )

        logger.warning(
            "Autenticación incompleta (%s): el login fallará hasta configurarla",
            ", ".join(missing),
        )
        return False

    if len(get_jwt_secret()) < MIN_SECRET_LENGTH:
        if is_production():
            raise RuntimeError(
                f"JWT_SECRET debe tener al menos {MIN_SECRET_LENGTH} caracteres"
            )

        logger.warning(
            "JWT_SECRET es demasiado corto: usa al menos %s caracteres",
            MIN_SECRET_LENGTH,
        )

    return True
