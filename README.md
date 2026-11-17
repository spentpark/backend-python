# backend-python

API REST de **juegos, plataformas y reseñas** con **FastAPI** + **SQLAlchemy async**
(MySQL/MariaDB). Es la réplica funcional del backend Node (`../backend-node20`):

- Los endpoints viven bajo **`/api`** con los mismos nombres que Node
  (`/api/games`, `/api/games/search`, `/api/games/random`, `/api/games/{id}/similar`,
  `/api/platforms`, `/api/platforms/{id}/top-games`, `/api/reviews/{id}`, `/api/stats`,
  `/api/auth/login`, `/api/auth/me`, `/api/saludo`, `/api/hello`).
- Aplica la **misma seguridad**: JWT HS256 (secreto/`issuer`/`audience` compartidos con
  `backend-node20` y `rss-game-node`), rol `admin` en las escrituras, cabeceras de
  seguridad tipo Helmet, CORS con allowlist, cuerpo JSON de 10 kb y rate limiting.
- Escucha en el puerto **7000** (el backend Node usa 3000).

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate         # Windows: .\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y ajusta la base de datos y el secreto JWT:

```bash
cp .env.example .env
```

`JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `AUTH_USERNAME`, `AUTH_ROLE` y
`AUTH_PASSWORD_HASH` deben coincidir con `backend-node20` para que un token emitido por
cualquiera de los dos servicios sea válido en el otro. En producción el arranque falla
cerrado si faltan `JWT_SECRET` o `AUTH_PASSWORD_HASH`.

## Ejecutar

```bash
uvicorn app.main:app --reload --port 7000
# Alternativa (usa el puerto 7000 por defecto): python -m app.main
```

- API: <http://localhost:7000/api>
- Swagger UI: <http://localhost:7000/api-docs>
- OpenAPI JSON: <http://localhost:7000/api-docs.json>

## Autenticación

Las rutas de negocio exigen `Authorization: Bearer <jwt>`; las escrituras exigen además
rol `admin`. El login emite el mismo token que `backend-node20`:

```bash
curl -X POST http://localhost:7000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Dev-aekiu4-9mHsG"}'
# → {"token":"<jwt>","tokenType":"Bearer","expiresAt":"..."}

curl http://localhost:7000/api/games?platform=Sony%20Playstation%204 \
  -H "Authorization: Bearer <jwt>"
```

## Endpoints

| Método | Ruta | Auth |
|--------|------|------|
| GET | `/api/saludo` | pública |
| GET | `/api/hello` | pública |
| POST | `/api/auth/login` | pública |
| GET | `/api/auth/me` | JWT |
| GET | `/api/games` (`platform`, `genre`, `year`, `decade`, `players`, `sort`, `page`, `limit`) | JWT |
| GET | `/api/games/search?title=` | JWT |
| GET | `/api/games/random` (`platform`, `genre`) | JWT |
| GET | `/api/games/{id}` | JWT |
| GET | `/api/games/{id}/similar?limit=` | JWT |
| POST / PUT / DELETE | `/api/games[/{id}]` | JWT admin |
| GET | `/api/platforms` | JWT |
| GET | `/api/platforms/{id}` | JWT |
| GET | `/api/platforms/{id}/top-games` | JWT |
| POST / PUT / DELETE | `/api/platforms[/{id}]` | JWT admin |
| GET | `/api/reviews/{id}` | JWT |
| GET | `/api/stats` | JWT |

Contrato detallado: [`endpoints.md`](endpoints.md).

Ejemplo de listado paginado:

```json
{
  "data": [{"id": 16489, "title": "The Witcher 3: Wild Hunt", "platform": "Sony Playstation 4"}],
  "pagination": {"currentPage": 1, "perPage": 10, "totalRecords": 7103, "totalPages": 711}
}
```

## Pruebas

```bash
pytest
pytest -W ignore --cov=app --cov-report=xml:coverage.xml --cov-report=html:htmlcov
```

Las pruebas usan SQLite en memoria y fijan el entorno JWT en `tests/conftest.py`.

## Docker

```bash
docker build -t backend-python .
docker run -p 7000:7000 --env-file .env backend-python
```

La imagen no incluye credenciales: se inyectan en runtime con `--env-file` o variables
del orquestador.
