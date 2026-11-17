"""Schema compartido para la información de paginación."""
from pydantic import BaseModel


class PaginationInfo(BaseModel):
    """Metadatos de paginación comunes a todas las respuestas paginadas."""

    currentPage: int
    perPage: int
    totalRecords: int
    totalPages: int
