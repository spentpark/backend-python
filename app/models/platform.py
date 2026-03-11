from sqlalchemy import Column, Integer, String
from app.database import Base

class Platform(Base):
    __tablename__ = "platform"
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(100), nullable=False)
    url = Column(String(100), nullable=True)