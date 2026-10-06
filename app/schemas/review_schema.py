"""Contratos Pydantic de entrada/salida para la entidad Review."""
from pydantic import BaseModel, ConfigDict


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
