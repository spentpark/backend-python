"""Configuración de la base de datos: engine async, sesiones y dependencia get_db."""
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

load_dotenv()

# Credenciales desde .env o valores por defecto
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "192.168.1.82")
DB_NAME = os.getenv("DB_NAME", "game")

# URL para MariaDB/MySQL asíncrono
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Configuración del Motor (Engine)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    # Recicla las conexiones antes del wait_timeout de MySQL/MariaDB para evitar
    # reutilizar conexiones ya cerradas por el servidor.
    pool_recycle=3600,
)

# Constructor de sesiones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI que entrega una sesión y garantiza su cierre."""
    async with AsyncSessionLocal() as session:
        yield session
