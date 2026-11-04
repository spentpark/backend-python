"""Manejadores globales de errores con el contrato JSON del backend Node.

Todas las respuestas de error tienen la forma ``{"error": "<mensaje>"}``:

- ``HTTPException`` → conserva el status y traduce ``detail`` a ``error``.
- Validación de FastAPI/Pydantic → 400 ``Petición inválida`` (Node nunca
  devuelve 422 con un esquema).
- Excepción no controlada → 500 ``Error interno del servidor`` sin stack trace.
- Ruta desconocida → 404 ``Ruta no encontrada``.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

INVALID_REQUEST_MESSAGE = "Petición inválida"
INTERNAL_ERROR_MESSAGE = "Error interno del servidor"
NOT_FOUND_MESSAGE = "Ruta no encontrada"


def install_exception_handlers(application: FastAPI) -> None:
    """Registra los manejadores de errores en la aplicación FastAPI."""

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else INVALID_REQUEST_MESSAGE
        message = NOT_FOUND_MESSAGE if exc.status_code == 404 and detail == "Not Found" else detail

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": message},
            headers=getattr(exc, "headers", None),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": INVALID_REQUEST_MESSAGE},
        )

    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Error interno en %s %s: %s", request.method, request.url.path, exc
        )
        return JSONResponse(
            status_code=500,
            content={"error": INTERNAL_ERROR_MESSAGE},
        )

    application.add_exception_handler(Exception, unexpected_exception_handler)
