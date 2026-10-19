"""Contratos Pydantic de entrada/salida para la entidad Review."""
from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginationInfo


class ReviewBase(BaseModel):
    name: str | None = None
    date: str | None = None
    review: str
    score: str | None = None
    source: str
    id_game: int | None = None


class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PaginatedReviewResponse(BaseModel):
    """Respuesta paginada con las reseñas de un juego."""

    data: list[ReviewResponse]
    pagination: PaginationInfo
