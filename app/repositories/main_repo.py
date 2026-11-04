"""Acceso a datos de utilidades (health-check de la base de datos)."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def _iso_z(moment: datetime) -> str:
    """Serializa una fecha UTC como ISO-8601 con sufijo ``Z`` (como Node)."""
    normalized = (
        moment.replace(tzinfo=timezone.utc)
        if moment.tzinfo is None
        else moment.astimezone(timezone.utc)
    )

    return normalized.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class MainRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_current_date(self) -> str:
        """Devuelve la fecha actual del servidor de base de datos en ISO-8601."""
        result = await self.db.execute(select(func.now()))
        value = result.scalar_one()

        if isinstance(value, datetime):
            return _iso_z(value)

        return str(value)
