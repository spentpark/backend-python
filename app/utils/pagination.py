"""Utilidades compartidas para construir respuestas paginadas."""
from collections.abc import Sequence
from typing import Any


def build_paginated_response(
    rows: Sequence[Any], total: int, page: int, limit: int
) -> dict[str, Any]:
    """Construye la estructura estándar de paginación `{data, pagination}`.

    Args:
        rows: Registros de la página actual.
        total: Total de registros que cumplen el filtro.
        page: Página solicitada (se refleja tal cual en `currentPage`).
        limit: Tamaño de página (debe ser >= 1).

    Returns:
        Diccionario con la lista de datos y la información de paginación.
    """
    # Aritmética entera (evita `math.ceil` y el uso de punto flotante).
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    return {
        "data": rows,
        "pagination": {
            "currentPage": page,
            "perPage": limit,
            "totalRecords": total,
            "totalPages": total_pages,
        },
    }
