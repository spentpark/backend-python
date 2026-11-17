"""Modelo ORM de la tabla ``similar_game``."""
from sqlalchemy import Column, Integer, Text

from app.database import Base


class SimilarGame(Base):
    """Similares precalculados de un juego.

    ``id_game`` es la PK del juego de referencia y ``json`` guarda el array
    ``[{ id, title, similarity }]`` que produce el motor de recomendación.
    """

    __tablename__ = "similar_game"

    id_game = Column(Integer, primary_key=True)
    json = Column(Text, nullable=True)
