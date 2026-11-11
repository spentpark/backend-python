"""Servicio de autenticación: login contra bcrypt y emisión/verificación de JWT.

Réplica del ``auth.service.js`` de ``backend-node20``: HS256 con el mismo
secreto, ``issuer``, ``audience`` y claim ``role``, para que el token sea válido
tanto en el servicio de noticias como en el catálogo.
"""
import hmac
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import auth as auth_config

# Patrón sin cuantificadores solapados: clases de caracteres disjuntas y
# ``\A``/``\Z`` en lugar de ``\s`` y ``$`` para evitar backtracking super-lineal
# (los saltos de línea hacen ambigua la posición de ``$``).
BEARER_PATTERN = re.compile(r"\ABearer[ \t]+(\S+)[ \t]*\Z", re.IGNORECASE)
_UNIT_SECONDS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
DEFAULT_TOKEN_SECONDS = 3600


class AuthError(Exception):
    """Error de autenticación: token ausente, inválido o expirado."""


def extract_bearer_token(header: str | None) -> str | None:
    """Extrae el token de una cabecera ``Authorization: Bearer <jwt>``."""
    if not isinstance(header, str):
        return None

    match = BEARER_PATTERN.match(header)

    return match.group(1).strip() if match else None


def _parse_expires_in(value: str | None) -> int:
    """Convierte ``1h``/``30m``/``3600`` a segundos (por defecto una hora).

    Se parsea a mano (sin expresión regular) para no exponerse a un patrón con
    backtracking super-lineal: solo se aceptan dígitos y un sufijo de unidad.
    """
    if not value:
        return DEFAULT_TOKEN_SECONDS

    raw = str(value).strip().lower()
    unit = raw[-1] if raw and raw[-1] in _UNIT_SECONDS else ""
    amount_text = raw[:-1].rstrip() if unit else raw

    if not amount_text.isdigit():
        return DEFAULT_TOKEN_SECONDS

    amount = int(amount_text)

    if amount <= 0:
        return DEFAULT_TOKEN_SECONDS

    return amount * _UNIT_SECONDS[unit]


def _iso_z(moment: datetime) -> str:
    """Serializa una fecha UTC como ISO-8601 con sufijo ``Z`` (como Node)."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def login(username: str, password: str) -> dict[str, str] | None:
    """Valida usuario y contraseña contra el usuario configurado por entorno.

    Devuelve ``{username, role}`` o ``None``. Se compara el hash bcrypt incluso
    si el usuario no coincide, para no filtrar por tiempos de respuesta.
    """
    user = auth_config.get_configured_user()
    configured_hash = user["password_hash"]

    if not configured_hash:
        return None

    provided_password = (password or "").encode("utf-8")

    try:
        password_matches = bcrypt.checkpw(provided_password, configured_hash.encode("utf-8"))
    except (ValueError, TypeError):
        password_matches = False

    username_matches = hmac.compare_digest(username or "", user["username"])

    if not (password_matches and username_matches):
        return None

    return {"username": user["username"], "role": user["role"]}


def issue_token(user: dict[str, str]) -> dict[str, str]:
    """Firma un JWT HS256 con ``sub`` = usuario y claim ``role``.

    Devuelve también la fecha de expiración para que el cliente pueda renovar
    a tiempo.
    """
    now = datetime.now(timezone.utc)
    options = auth_config.get_sign_options()
    expires = now + timedelta(seconds=_parse_expires_in(options["expires_in"]))
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "iss": options["issuer"],
        "aud": options["audience"],
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    token = jwt.encode(payload, auth_config.get_jwt_secret_or_raise(), algorithm="HS256")

    return {"token": token, "expiresAt": _iso_z(expires)}


def verify_token(token: str) -> dict[str, str]:
    """Verifica firma, algoritmo, issuer, audience y expiración.

    Lanza :class:`AuthError` si el token no es válido; el middleware lo traduce
    a un 401 sin exponer detalles internos.
    """
    secret = auth_config.get_jwt_secret_or_raise()
    options = auth_config.get_verify_options()

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=options["issuer"],
            audience=options["audience"],
            options={"require": ["exp", "iss", "aud", "sub", "role"]},
        )
    except jwt.PyJWTError as error:
        raise AuthError("Token inválido") from error

    subject = payload.get("sub")
    role = payload.get("role")

    if not isinstance(subject, str) or not isinstance(role, str):
        raise AuthError("Payload del token incompleto")

    return {"username": subject, "role": role}
