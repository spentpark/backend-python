"""Endurecimiento HTTP: cabeceras de seguridad, límite de cuerpo y rate limiting.

Replica el comportamiento de ``helmet`` + ``express.json({limit: '10kb'})`` +
``express-rate-limit`` del backend Node:

- Cabeceras de seguridad (CSP, HSTS, ``nosniff``, ``Referrer-Policy``, COOP,
  CORP, etc.). La CSP se omite en ``/api-docs`` porque Swagger UI usa scripts y
  estilos inline.
- Cuerpo JSON limitado a 10 kb → 413 ``{"error": "..."}``.
- Rate limiting en memoria por IP: global de la API (300 / 15 min) y login
  (5 / 15 min), configurables con ``API_RATE_LIMIT_*`` y ``AUTH_RATE_LIMIT_*``.
  Al superar el límite → 429 con las cabeceras ``RateLimit-*`` y ``Retry-After``.
"""
import os
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

MAX_BODY_BYTES = 10 * 1024
BODY_TOO_LARGE_MESSAGE = "El cuerpo de la petición es demasiado grande"

DEFAULT_API_WINDOW_MS = 15 * 60 * 1000
DEFAULT_API_MAX = 300
DEFAULT_AUTH_WINDOW_MS = 15 * 60 * 1000
DEFAULT_AUTH_MAX = 5
MAX_WINDOW_ENTRIES = 10_000

API_RATE_LIMIT_MESSAGE = "Demasiadas solicitudes. Inténtalo más tarde."
LOGIN_RATE_LIMIT_MESSAGE = "Demasiados intentos de inicio de sesión. Inténtalo más tarde."

# Cabeceras equivalentes a las que añade `helmet()` en Express.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Origin-Agent-Cluster": "?1",
    "X-DNS-Prefetch-Control": "off",
    "X-Download-Options": "noopen",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

# CSP por defecto de `helmet`. Swagger UI necesita scripts/estilos inline, por
# eso la documentación se excluye y queda servida sin CSP.
CONTENT_SECURITY_POLICY = (
    "default-src 'self';"
    "base-uri 'self';"
    "font-src 'self' https: data:;"
    "form-action 'self';"
    "frame-ancestors 'self';"
    "img-src 'self' data:;"
    "object-src 'none';"
    "script-src 'self';"
    "script-src-attr 'none';"
    "style-src 'self' https: 'unsafe-inline';"
    "upgrade-insecure-requests"
)


def _env_positive_int(name: str, fallback: int) -> int:
    """Lee un entero positivo de entorno; si no es válido usa el fallback."""
    raw = os.getenv(name)

    if raw is None:
        return fallback

    try:
        parsed = int(str(raw).strip())
    except ValueError:
        return fallback

    return parsed if parsed > 0 else fallback


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade las cabeceras de seguridad de ``helmet`` a todas las respuestas."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)

        if not request.url.path.startswith("/api-docs"):
            response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)

        return response


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """Rechaza cuerpos con ``Content-Length`` mayor de 10 kb (413)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                too_large = int(content_length) > MAX_BODY_BYTES
            except ValueError:
                too_large = False

            if too_large:
                return JSONResponse(
                    status_code=413,
                    content={"error": BODY_TOO_LARGE_MESSAGE},
                )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting en memoria por IP (ventana fija), equivalente a Node."""

    def __init__(
        self,
        app,
        *,
        window_seconds: int,
        limit: int,
        message: str,
        path_prefix: str = "/api",
        method: str | None = None,
    ):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.limit = limit
        self.message = message
        self.path_prefix = path_prefix
        self.method = method.upper() if method else None
        self._requests: dict[str, tuple[float, int]] = {}

    def _client_key(self, request: Request) -> str:
        if os.getenv("TRUST_PROXY", "").strip().lower() == "true":
            forwarded = request.headers.get("x-forwarded-for")

            if forwarded:
                return forwarded.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _prune(self, now: float) -> None:
        if len(self._requests) < MAX_WINDOW_ENTRIES:
            return

        expired = [
            key
            for key, (window_start, _count) in self._requests.items()
            if now - window_start >= self.window_seconds
        ]

        for key in expired:
            self._requests.pop(key, None)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not request.url.path.startswith(self.path_prefix):
            return await call_next(request)

        if self.method and request.method != self.method:
            return await call_next(request)

        now = time.monotonic()
        self._prune(now)

        key = self._client_key(request)
        window_start, count = self._requests.get(key, (now, 0))

        if now - window_start >= self.window_seconds:
            window_start, count = now, 0

        count += 1
        self._requests[key] = (window_start, count)

        remaining = max(self.limit - count, 0)
        reset_seconds = max(int(window_start + self.window_seconds - now), 0)
        headers = {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(remaining),
            "RateLimit-Reset": str(reset_seconds),
            "RateLimit-Policy": f"{self.limit};w={self.window_seconds}",
        }

        if count > self.limit:
            headers["Retry-After"] = str(max(reset_seconds, 1))
            return JSONResponse(
                status_code=429,
                content={"error": self.message},
                headers=headers,
            )

        response = await call_next(request)

        for name, value in headers.items():
            response.headers.setdefault(name, value)

        return response


def api_rate_limit_options() -> dict:
    """Opciones del limitador global de la API (300 peticiones / 15 min)."""
    return {
        "window_seconds": max(
            _env_positive_int("API_RATE_LIMIT_WINDOW_MS", DEFAULT_API_WINDOW_MS) // 1000,
            1,
        ),
        "limit": _env_positive_int("API_RATE_LIMIT_MAX", DEFAULT_API_MAX),
        "message": API_RATE_LIMIT_MESSAGE,
    }


def login_rate_limit_options() -> dict:
    """Opciones del limitador del login (5 intentos / 15 min, solo POST)."""
    return {
        "window_seconds": max(
            _env_positive_int("AUTH_RATE_LIMIT_WINDOW_MS", DEFAULT_AUTH_WINDOW_MS) // 1000,
            1,
        ),
        "limit": _env_positive_int("AUTH_RATE_LIMIT_MAX", DEFAULT_AUTH_MAX),
        "message": LOGIN_RATE_LIMIT_MESSAGE,
        "path_prefix": "/api/auth/login",
        "method": "POST",
    }
