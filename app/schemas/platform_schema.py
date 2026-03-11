from pydantic import BaseModel
from typing import Optional

class PlatformBase(BaseModel):
    description: str
    url: Optional[str] = None

class PlatformCreate(PlatformBase):
    pass

class PlatformResponse(PlatformBase):
    id: int
    class Config:
        from_attributes = True