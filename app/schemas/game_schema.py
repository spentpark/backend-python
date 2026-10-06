"""Contratos Pydantic de entrada/salida para la entidad Game."""
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination import PaginationInfo


class GameBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str
    GameDBId: int | None = None
    image_Large: str | None = None
    image_Medium: str | None = None
    image_Original: str | None = None
    image_Front: str | None = None
    Platform: str | None = None
    Publisher: str | None = None
    releasedate: str | None = None
    players: str | None = None
    genre: str | None = None
    youtube_Trailer: str | None = None
    youtube_Walk: str | None = None
    wiki_url: str | None = None
    wiki_page: str | None = None
    youtube_ending: str | None = None
    youtube_secrets: str | None = None
    youtube_ost: str | None = None
    youtube_speedrun: str | None = None
    youtube_review: str | None = None
    spotify_ost: str | None = None
    ign_url: str | None = None
    metacritic_url: str | None = None
    metacritic_score: str | None = None
    metacritic_scoreu: str | None = None
    three_d_juegos_url: str | None = Field(None, alias="3djuegos_url")
    areajugones_url: str | None = None
    meristation_url: str | None = None
    three_d_juegos_score: str | None = Field(None, alias="3djuegos_score")
    opencritic_url: str | None = None
    esrb_letter: str | None = None
    esbr_message: str | None = None


class GameCreate(GameBase):
    pass


class GameResponse(GameBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int


class PaginatedGameResponse(BaseModel):
    data: list[GameResponse]
    pagination: PaginationInfo


class GameSummary(BaseModel):
    """Vista reducida de un juego para el listado paginado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    # El modelo ORM expone el atributo como `Platform`; la salida JSON es `platform`.
    platform: str | None = Field(None, validation_alias="Platform")


class PaginatedGameSummaryResponse(BaseModel):
    data: list[GameSummary]
    pagination: PaginationInfo
