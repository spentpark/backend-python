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
