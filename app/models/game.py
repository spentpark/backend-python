from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    GameDBId = Column(Integer, nullable=True)
    image_Large = Column(String(255))
    image_Medium = Column(String(255))
    image_Original = Column(String(255))
    image_Front = Column(String(255))
    Platform = Column(String(200), index=True) # Nombre exacto de tu DDL
    Publisher = Column(String(300))
    releasedate = Column(String(12))
    players = Column(String(10))
    genre = Column(String(100))
    youtube_Trailer = Column(String(255))
    youtube_Walk = Column(String(255))
    wiki_url = Column(String(500))
    wiki_page = Column(Text)
    youtube_ending = Column(String(255))
    youtube_secrets = Column(String(255))
    youtube_ost = Column(String(255))
    youtube_speedrun = Column(String(200))
    youtube_review = Column(String(200))
    spotify_ost = Column(String(200))
    ign_url = Column(String(200))
    metacritic_url = Column(String(200))
    metacritic_score = Column(String(30))
    metacritic_scoreu = Column(String(30))
    three_d_juegos_url = Column("3djuegos_url", String(200)) # Alias porque nombres no pueden empezar con número en Python
    areajugones_url = Column(String(200))
    meristation_url = Column(String(200))
    three_d_juegos_score = Column("3djuegos_score", String(30))
    opencritic_url = Column(String(200))
    esrb_letter = Column(String(5))
    esbr_message = Column(String(50))