"""Contratos Pydantic de entrada/salida para la entidad Platform."""
from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginationInfo


class PlatformBase(BaseModel):
    description: str
    url: str | None = None


class PlatformCreate(PlatformBase):
    pass


class PlatformResponse(PlatformBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PaginatedPlatformResponse(BaseModel):
    data: list[PlatformResponse]
    pagination: PaginationInfo


class TopGameItem(BaseModel):
    """Juego del top 10 de una plataforma (``GET /api/platforms/{id}/top-games``).

    Conserva los nombres de columna reales de la tabla ``games``, igual que el
    backend Node.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    Platform: str | None = None
    genre: str | None = None
    releasedate: str | None = None
    image_Original: str | None = None
    metacritic_score: str | None = None
