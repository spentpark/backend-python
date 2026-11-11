"""Acceso a datos de la entidad Game (SQLAlchemy Async)."""
import secrets
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Integer, and_, cast, delete, func, select, update
from sqlalchemy.engine import CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game

# Intentos de búsqueda de un id al azar con tráiler antes de rendirse. La tabla
# `games` no tiene índice sobre `youtube_Trailer`, así que se evita cualquier
# filtro o `COUNT(*)`: con ~1,4 GB, escanearla completa tarda más de un minuto.
_RANDOM_ATTEMPTS = 6

# Whitelist de ordenaciones del catálogo: el valor llega del query string, pero
# las cláusulas SQL son siempre constantes de este mapa (nunca input).
SORT_CLAUSES = {
    "id_asc": (Game.id.asc(),),
    "id_desc": (Game.id.desc(),),
    "title_asc": (Game.title.asc(),),
    "title_desc": (Game.title.desc(),),
    "year_asc": (Game.releasedate.asc(), Game.id.asc()),
    "year_desc": (Game.releasedate.desc(), Game.id.desc()),
    "score_desc": (
        cast(func.nullif(Game.metacritic_score, ""), Integer).desc(),
        Game.id.asc(),
    ),
}

DEFAULT_SORT = "id_asc"

# Filtros que activan el camino "avanzado" del listado, igual que en Node.
ADVANCED_FILTER_KEYS = ("genre", "year", "decade", "players", "sort")


def _random_id(low: int, high: int) -> int:
    """Entero aleatorio en ``[low, high]`` con CSPRNG (``secrets``).

    Se usa ``secrets`` en lugar de ``random`` para que el generador sea
    criptográficamente seguro aunque hoy solo sirva para elegir un juego.
    """
    return low + secrets.randbelow(high - low + 1)


def has_advanced_filters(filters: dict[str, Any]) -> bool:
    """``True`` si hay algún filtro además de la plataforma."""
    return any(filters.get(key) for key in ADVANCED_FILTER_KEYS)


def build_filter_conditions(filters: dict[str, Any]) -> list[Any]:
    """Normaliza los filtros del catálogo a una lista de condiciones parametrizadas.

    Los nombres de columna son constantes internas; el input del usuario viaja
    siempre como parámetro ligado.
    """
    conditions: list[Any] = []

    if filters.get("platform"):
        conditions.append(Game.Platform == filters["platform"])

    if filters.get("genre"):
        conditions.append(Game.genre == filters["genre"])

    if filters.get("year"):
        # `releasedate` es VARCHAR 'YYYY-MM-DD' en la BD de producción.
        conditions.append(Game.releasedate.like(f"{str(filters['year'])[:4]}%"))

    if filters.get("players"):
        # `players` es VARCHAR ('1', '1-4', '2-4'...): se filtra por prefijo.
        conditions.append(Game.players.like(f"{str(filters['players'])}%"))

    if filters.get("decade"):
        conditions.append(Game.releasedate.like(f"{str(filters['decade'])[:3]}%"))

    return conditions


class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self) -> Sequence[Game]:
        result = await self.db.execute(select(Game))
        return result.scalars().all()

    async def find_by_id(self, id: int) -> Game | None:
        result = await self.db.execute(select(Game).where(Game.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> Game:
        new_game = Game(**data)
        self.db.add(new_game)
        # El commit hace flush del INSERT y ya rellena la PK autoincremental,
        # por lo que un refresh() posterior sería un SELECT innecesario.
        await self.db.commit()
        return new_game

    async def update(self, id: int, data: dict[str, Any]) -> CursorResult:
        query = update(Game).where(Game.id == id).values(**data)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def delete(self, id: int) -> CursorResult:
        query = delete(Game).where(Game.id == id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result

    async def find_by_title_paginated(
        self, title: str, page: int, limit: int
    ) -> tuple[Sequence[Row], int]:
        """Busca por prefijo de título y devuelve la página junto al total.

        Solo se seleccionan ``id``, ``title`` y ``Platform`` para no transferir
        las columnas ``Text`` pesadas (contrato del listado de Node). El
        backslash se duplica para que ``LIKE`` lo interprete como literal.
        """
        search_term = f"{title.replace('\\', '\\\\')}%"
        return await self._find_summary_paginated([Game.title.like(search_term)], page, limit)

    async def find_by_platform_paginated(
        self, platform: str | None, page: int, limit: int
    ) -> tuple[Sequence[Row], int]:
        """Filtra por plataforma exacta y devuelve la página junto al total.

        Igual que Node, sin ``platform`` se envía ``NULL`` a la comparación, que
        nunca coincide: la respuesta es una página vacía con total 0.
        """
        if platform is None:
            return [], 0

        return await self._find_summary_paginated([Game.Platform == platform], page, limit)

    async def find_filtered_paginated(
        self, filters: dict[str, Any], page: int, limit: int
    ) -> tuple[Sequence[Row], int]:
        """Catálogo paginado con filtros avanzados y orden (whitelist)."""
        conditions = build_filter_conditions(filters)
        sort_key = filters.get("sort") if filters.get("sort") in SORT_CLAUSES else DEFAULT_SORT

        return await self._find_summary_paginated(
            conditions, page, limit, sort_key=sort_key
        )

    async def _find_summary_paginated(
        self,
        conditions: Sequence[Any],
        page: int,
        limit: int,
        sort_key: str | None = None,
    ) -> tuple[Sequence[Row], int]:
        """Listado resumido (id, title, Platform) con paginación y total."""
        offset = max(page - 1, 0) * limit
        where_clause = and_(*conditions) if conditions else None

        query = select(Game.id, Game.title, Game.Platform)

        if where_clause is not None:
            query = query.where(where_clause)

        if sort_key is not None:
            query = query.order_by(*SORT_CLAUSES[sort_key])

        query = query.limit(limit).offset(offset)
        rows = (await self.db.execute(query)).all()

        # COUNT(*) es más rápido que COUNT(columna): no evalúa la columna.
        total_query = select(func.count()).select_from(Game)

        if where_clause is not None:
            total_query = total_query.where(where_clause)

        total = (await self.db.execute(total_query)).scalar_one()

        return rows, total

    async def find_random_with_trailer(
        self, filters: dict[str, Any] | None = None
    ) -> Game | None:
        """Devuelve un juego al azar que tenga tráiler, o None si no hay ninguno.

        No se usa `COUNT(*)` ni `ORDER BY RAND()`: la tabla `games` es muy grande
        (~1,4 GB y sin índice sobre `youtube_Trailer`) y cualquier consulta que
        la recorra completa tarda más de un minuto. En su lugar se elige un id al
        azar dentro del rango de la clave primaria y se consulta por PK; si el id
        no existe o el juego no tiene tráiler, se reintenta.

        Con filtros de plataforma o género se replica el algoritmo de Node: se
        obtiene el ``MAX(id)`` del subconjunto filtrado y se sortea dentro de ese
        rango, con un fallback al primer juego que cumpla el filtro.
        """
        filters = filters or {}

        if filters.get("platform") or filters.get("genre"):
            return await self._find_random_with_trailer_filtered(filters)

        bounds = await self._id_bounds()

        if bounds is None:
            return None

        min_id, max_id = bounds

        for _ in range(_RANDOM_ATTEMPTS):
            candidate = _random_id(min_id, max_id)

            result = await self.db.execute(select(Game).where(Game.id == candidate))
            game = result.scalar_one_or_none()

            if game and game.youtube_Trailer:
                return game

        return None

    async def _find_random_with_trailer_filtered(
        self, filters: dict[str, Any]
    ) -> Game | None:
        """Juego al azar con tráiler aplicando filtros de plataforma/género."""
        conditions = [
            Game.youtube_Trailer.isnot(None),
            Game.youtube_Trailer != "",
            *build_filter_conditions(
                {"platform": filters.get("platform"), "genre": filters.get("genre")}
            ),
        ]
        where_clause = and_(*conditions)

        max_id = (
            await self.db.execute(select(func.max(Game.id)).where(where_clause))
        ).scalar_one()

        if not max_id:
            return None

        for _ in range(_RANDOM_ATTEMPTS):
            candidate = _random_id(1, max_id)

            result = await self.db.execute(
                select(Game).where(Game.id == candidate, where_clause)
            )
            game = result.scalar_one_or_none()

            if game:
                return game

        fallback = await self.db.execute(
            select(Game).where(where_clause).order_by(Game.id).limit(1)
        )

        return fallback.scalar_one_or_none()

    async def _id_bounds(self) -> tuple[int, int] | None:
        """Rango de ids usando el índice de la PK (MIN/MAX tardan segundos aquí)."""
        first = await self.db.execute(select(Game.id).order_by(Game.id).limit(1))
        last = await self.db.execute(select(Game.id).order_by(Game.id.desc()).limit(1))

        min_id = first.scalar_one_or_none()
        max_id = last.scalar_one_or_none()

        if min_id is None or max_id is None:
            return None

        return min_id, max_id
