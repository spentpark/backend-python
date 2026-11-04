"""Acceso a datos de las estadísticas del catálogo (SQLAlchemy Async).

Las consultas evitan SQL específico de MySQL para que también funcionen con
SQLite en las pruebas (``SUBSTR`` y ``CAST(... AS INTEGER)`` son portables).
"""
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game

DEFAULT_DISTRIBUTION_LIMIT = 20


class StatsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> dict[str, int]:
        """Totales generales del catálogo en una sola pasada."""
        query = select(
            func.count().label("totalGames"),
            func.count(func.nullif(Game.metacritic_score, "")).label("scoredGames"),
            func.count(func.distinct(Game.Platform)).label("totalPlatforms"),
            func.count(func.distinct(Game.genre)).label("totalGenres"),
        )
        row = (await self.db.execute(query)).one()

        return {
            "totalGames": int(row.totalGames or 0),
            "scoredGames": int(row.scoredGames or 0),
            "totalPlatforms": int(row.totalPlatforms or 0),
            "totalGenres": int(row.totalGenres or 0),
        }

    async def get_games_by_platform(
        self, limit: int = DEFAULT_DISTRIBUTION_LIMIT
    ) -> Sequence[dict[str, Any]]:
        """Juegos por plataforma (top N), usando el nombre de ``Platform``."""
        count_column = func.count()
        query = (
            select(Game.Platform.label("label"), count_column.label("total"))
            .where(Game.Platform.isnot(None), Game.Platform != "")
            .group_by(Game.Platform)
            .order_by(count_column.desc(), Game.Platform.asc())
            .limit(limit)
        )

        return self._to_distribution((await self.db.execute(query)).all())

    async def get_games_by_genre(
        self, limit: int = DEFAULT_DISTRIBUTION_LIMIT
    ) -> Sequence[dict[str, Any]]:
        """Juegos por género (top N). Un juego puede tener géneros con ``|``."""
        count_column = func.count()
        query = (
            select(Game.genre.label("label"), count_column.label("total"))
            .where(Game.genre.isnot(None), Game.genre != "")
            .group_by(Game.genre)
            .order_by(count_column.desc(), Game.genre.asc())
            .limit(limit)
        )

        return self._to_distribution((await self.db.execute(query)).all())

    async def get_games_by_decade(
        self, limit: int = DEFAULT_DISTRIBUTION_LIMIT
    ) -> Sequence[dict[str, Any]]:
        """Juegos por década (``releasedate`` es VARCHAR 'YYYY-MM-DD')."""
        decade_prefix = func.substr(Game.releasedate, 1, 3)
        release_year = cast(func.substr(Game.releasedate, 1, 4), Integer)
        query = (
            select(decade_prefix.label("decade"), func.count().label("total"))
            .where(Game.releasedate.isnot(None), Game.releasedate != "")
            # Descarta fechas corruptas (p. ej. '2920-01-01' o '0980-...').
            .where(release_year.between(1950, 2035))
            .group_by(decade_prefix)
        )
        rows = (await self.db.execute(query)).all()

        entries = [
            {"label": f"{row.decade}0", "total": int(row.total)}
            for row in rows
            if row.decade
        ]
        entries.sort(key=lambda item: item["label"], reverse=True)

        return entries[:limit]

    @staticmethod
    def _to_distribution(rows) -> list[dict[str, Any]]:
        return [
            {"label": str(row.label), "total": int(row.total)}
            for row in rows
            if row.label is not None
        ]
