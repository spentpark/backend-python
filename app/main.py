"""Punto de entrada de la Games API (FastAPI).

Réplica del backend Node: endpoints bajo ``/api``, JWT HS256 compartido con
``rss-game-node``, cabeceras de seguridad tipo ``helmet``, CORS con allowlist,
límite de cuerpo de 10 kb, rate limiting y documentación en ``/api-docs``.

La aplicación escucha en el puerto **7000**.
"""
import logging
import os

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import auth as auth_config
from app.errors import install_exception_handlers
from app.middlewares.security import (
    BodyLimitMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    api_rate_limit_options,
    login_rate_limit_options,
)
from app.routes.auth_routes import router as auth_router
from app.routes.game_routes import router as game_router
from app.routes.main_routes import router as main_router
from app.routes.platform_routes import router as platform_router
from app.routes.review_routes import router as review_router
from app.routes.similar_routes import router as similar_router
from app.routes.stats_routes import router as stats_router

logger = logging.getLogger(__name__)

APP_PORT = 7000

# Allowlist de CORS. Se puede sobreescribir con `CORS_ORIGINS` (separados por
# comas) sin tocar el código; sin la variable se usa la lista por defecto.
DEFAULT_ORIGINS = [
    # Frontend React 19: Vite dev (5173), `vite preview` (4173) y Nginx (8065).
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8065",
    "http://127.0.0.1:8065",
    # Frontend Angular legacy (4200/4300) y otros orígenes locales.
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:4300",
    "http://127.0.0.1:4300",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost",
    # Frontends desplegados en la LAN / IP pública del servidor.
    "http://192.168.1.82:4200",
    "http://192.168.1.82:4300",
    "http://192.168.1.82:8065",
    "http://200.83.105.123:4200",
    "http://200.83.105.123:4300",
    "http://200.83.105.123:8065",
    "https://tudominio.com",
]

# En desarrollo se acepta cualquier puerto local (Vite, `vite preview`, Nginx).
LOCAL_ORIGIN_PATTERN = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"


def _is_docs_enabled() -> bool:
    """Swagger en ``/api-docs``: apagado en producción salvo ``API_DOCS_ENABLED=true``."""
    configured = (os.getenv("API_DOCS_ENABLED") or "").strip().lower()

    if configured == "false":
        return False

    if auth_config.is_production():
        return configured == "true"

    return True


def _allowed_origins() -> list[str]:
    """Allowlist de CORS (``CORS_ORIGINS`` la sobreescribe)."""
    raw = os.getenv("CORS_ORIGINS")

    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    return DEFAULT_ORIGINS


def create_app() -> FastAPI:
    """Construye la aplicación FastAPI (sin abrir puerto, para poder testearla)."""
    # Falla cerrado en producción si falta la configuración JWT; en desarrollo avisa.
    auth_config.validate_auth_configuration()

    docs_enabled = _is_docs_enabled()
    application = FastAPI(
        title="Games API",
        description="API para gestión de juegos, plataformas y reseñas",
        version="1.0.0",
        docs_url="/api-docs" if docs_enabled else None,
        openapi_url="/api-docs.json" if docs_enabled else None,
        redoc_url=None,
    )

    # Orden de ejecución (de fuera hacia dentro): CORS → cabeceras de seguridad →
    # rate limiting → límite de cuerpo → rutas. Es el equivalente al orden de
    # middlewares de Express en el backend Node. CORS se registra al final
    # (queda como el middleware más externo) para que el navegador pueda leer
    # también las respuestas de error del resto de middlewares (403/413/429/500).
    application.add_middleware(BodyLimitMiddleware)
    application.add_middleware(RateLimitMiddleware, **login_rate_limit_options())
    application.add_middleware(RateLimitMiddleware, **api_rate_limit_options())
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_origin_regex=None if auth_config.is_production() else LOCAL_ORIGIN_PATTERN,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        # `apikey` es la cabecera que añade el frontend: sin incluirla el
        # navegador bloquea el preflight de CORS.
        allow_headers=["Content-Type", "Authorization", "apikey"],
    )

    install_exception_handlers(application)

    # Rutas públicas: utilidades y autenticación.
    application.include_router(main_router, prefix="/api")
    application.include_router(auth_router, prefix="/api")

    # Catálogo protegido con JWT (mismo esquema y secreto que rss-game-node).
    application.include_router(game_router, prefix="/api")
    application.include_router(similar_router, prefix="/api")
    application.include_router(platform_router, prefix="/api")
    application.include_router(review_router, prefix="/api")
    application.include_router(stats_router, prefix="/api")

    @application.get("/", tags=["Root"], include_in_schema=False)
    async def root():
        """Mensaje de bienvenida con la ruta de la documentación."""
        return {
            "mensaje": "Bienvenido a la Games API",
            "docs": "/api-docs" if docs_enabled else None,
        }

    @application.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Evita el 404 de favicon en los logs."""
        return Response(status_code=204)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    # La interfaz de escucha se toma del entorno (`HOST`). Por defecto se usa
    # localhost para no exponer el servicio en todas las interfaces; en Docker
    # o en la LAN se define `HOST=0.0.0.0` explícitamente en el entorno.
    # Nota: cuando se usa reload=True hay que pasar el string "app.main:app".
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST") or "127.0.0.1",
        port=int(os.getenv("PORT") or APP_PORT),
        reload=True,
        server_header=False,
    )
