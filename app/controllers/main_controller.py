"""Controlador HTTP de utilidades (saludo y health-check de la base de datos)."""
import logging

from fastapi import HTTPException

from app.repositories.main_repo import MainRepository

logger = logging.getLogger(__name__)


class MainController:
    def __init__(self, repository: MainRepository):
        self.repository = repository

    def saludo(self) -> dict[str, str]:
        """Mensaje de bienvenida fijo, sin consultar la base de datos."""
        return {"mensaje": "¡Hola desde Python con FastAPI!"}

    async def hello(self) -> dict[str, str]:
        """Health-check de la base de datos: devuelve la fecha del servidor."""
        try:
            fecha = await self.repository.find_current_date()
        except Exception as error:
            logger.exception("Error al conectar con la base de datos: %s", error)
            raise HTTPException(status_code=500, detail="Error en la base de datos") from error

        return {"mensaje": "¡Conectado a MariaDB!", "fecha": fecha}
