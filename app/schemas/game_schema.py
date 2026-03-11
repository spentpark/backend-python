from pydantic import BaseModel, Field
from typing import Optional, List

class GameBase(BaseModel):
    title: str
    description: str
    GameDBId: Optional[int] = None
    image_Large: Optional[str] = None
    image_Medium: Optional[str] = None
    image_Original: Optional[str] = None
    image_Front: Optional[str] = None
    Platform: Optional[str] = None
    Publisher: Optional[str] = None
    releasedate: Optional[str] = None
    players: Optional[str] = None
    genre: Optional[str] = None
    youtube_Trailer: Optional[str] = None
    youtube_Walk: Optional[str] = None
    wiki_url: Optional[str] = None
    wiki_page: Optional[str] = None
    youtube_ending: Optional[str] = None
    youtube_secrets: Optional[str] = None
    youtube_ost: Optional[str] = None
    youtube_speedrun: Optional[str] = None
    youtube_review: Optional[str] = None
    spotify_ost: Optional[str] = None
    ign_url: Optional[str] = None
    metacritic_url: Optional[str] = None
    metacritic_score: Optional[str] = None
    metacritic_scoreu: Optional[str] = None
    three_d_juegos_url: Optional[str] = Field(None, alias="3djuegos_url")
    areajugones_url: Optional[str] = None
    meristation_url: Optional[str] = None
    three_d_juegos_score: Optional[str] = Field(None, alias="3djuegos_score")
    opencritic_url: Optional[str] = None
    esrb_letter: Optional[str] = None
    esbr_message: Optional[str] = None

    class Config:
        populate_by_name = True

class GameCreate(GameBase):
    pass

class GameResponse(GameBase):
    id: int
    class Config:
        from_attributes = True

# Para la paginación que ya tenías
class PaginationInfo(BaseModel):
    currentPage: int
    perPage: int
    totalRecords: int
    totalPages: int

class PaginatedGameResponse(BaseModel):
    data: List[GameResponse]
    pagination: PaginationInfo