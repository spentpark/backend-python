from pydantic import BaseModel
from typing import Optional

class ReviewBase(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    review: str
    score: Optional[str] = None
    source: str
    id_game: Optional[int] = None

class ReviewResponse(ReviewBase):
    id: int
    class Config:
        from_attributes = True