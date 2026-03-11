from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base

class Review(Base):
    __tablename__ = "review"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=True)
    date = Column(String(30), nullable=True)
    review = Column(Text, nullable=False)
    score = Column(String(8), nullable=True)
    source = Column(String(100), nullable=False)
    id_game = Column(Integer, ForeignKey("games.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)