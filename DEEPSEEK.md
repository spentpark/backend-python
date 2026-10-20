# GEMINI.md — backend-python

Contexto instructivo para agentes de IA que trabajen en este repositorio.

## 1. Resumen del proyecto

**backend-python** es una API REST para la gestión de **videojuegos**, **plataformas** y
**reseñas**. Está construida con **FastAPI** y persiste datos en **MySQL/MariaDB** usando
**SQLAlchemy en modo asíncrono** (`aiomysql`).

- Título de la API (OpenAPI): `Games API` — versión `1.0.0`.
- Documentación interactiva disponible en `/docs` (Swagger UI) al ejecutar el servidor.
- Todos los endpoints son **públicos** (no hay autenticación ni autorización).
- El código y la documentación de diseño están redactados en **español**; mantén ese idioma
  en comentarios, `detail` de excepciones y mensajes nuevos.

## 2. Stack tecnológico

| Componente        | Tecnología                                   |
| ----------------- | -------------------------------------------- |
| Lenguaje          | Python 3.14                                  |
| Framework web     | FastAPI >= 0.142.2                           |
| Servidor ASGI     | Uvicorn >= 0.54.0                            |
| ORM               | SQLAlchemy >= 2.1.3 (async)                  |
| Driver DB         | aiomysql >= 0.3.2                            |
| Validación/schemas| Pydantic >= 2.13.5                           |
| Configuración     | python-dotenv >= 1.2.4                       |
| Criptografía      | cryptography >= 50.0.2                       |
| Base de datos     | MySQL / MariaDB                              |
| Testing           | pytest + pytest-asyncio + httpx + aiosqlite  |
| Calidad           | SonarQube / sonar-scanner                    |
| CI/CD             | Jenkins (Jenkinsfile) + Nexus (PyPI repo)    |
| Empaquetado       | setuptools / `python -m build` (wheel)       |

## 3. Arquitectura (capas)

El proyecto sigue una **arquitectura en capas**. Cada petición fluye en una sola dirección:

```
Routes → Controllers → Services → Repositories → Models (ORM) → DB
                          ↕
                     Schemas (Pydantic)  ← contratos de entrada/salida JSON
```

- **Routes** (`app/routes/`): definen endpoints REST, `APIRouter` con `prefix` y `tags`, y la
  inyección de dependencias mediante una factory `get_controller(db = Depends(get_db))` que
  construye `Repository → Service → Controller`. Las dependencias y los query params se
  declaran con `Annotated` (p. ej. `Annotated[int, Query(ge=1)]`).
- **Controllers** (`app/controllers/`): orquestan el servicio y aplican validaciones básicas
  (lanzan `HTTPException` 404/400). No contienen lógica de negocio ni acceso a datos.
- **Services** (`app/services/`): lógica de negocio. La construcción de la respuesta paginada
  se centraliza en `app/utils/pagination.py` (`build_paginated_response`).
- **Repositories** (`app/repositories/`): acceso a datos con **SQLAlchemy Async**
  (`select`, `update`, `delete`, `func.count`). Hacen `commit` y `execute`. Para conteos usa
  `select(func.count()).select_from(Model)` (genera `COUNT(*)`).
- **Models** (`app/models/`): mapeo ORM (`declarative_base` de `app/database.py`).
- **Schemas** (`app/schemas/`): contratos **Pydantic** de entrada/salida. Se usa
  `model_config = ConfigDict(from_attributes=True)` para serializar modelos ORM y
  `populate_by_name = True` para aceptar alias (p. ej. campos que empiezan por número:
  `3djuegos_url`). `PaginationInfo` es compartido (`app/schemas/pagination.py`).

### Flujo de una petición (ejemplo `GET /games/{id}`)

`Cliente → Route → Controller → Service → Repository → DB` y de vuelta, serializando con
Pydantic. Si no existe el recurso, el **Controller** lanza `HTTPException(404)`.

## 4. Estructura de directorios

```
backend-python/
├── app/
│   ├── main.py            # Instancia FastAPI, routers, /favicon.ico y ruta raíz "/"
│   ├── database.py        # Engine async, AsyncSessionLocal, Base, dependencia get_db()
│   ├── controllers/       # game_controller, platform_controller, review_controller
│   ├── models/            # game, platform, review (ORM)
│   ├── repositories/      # game_repo, platform_repo, review_repo
│   ├── routes/            # game_routes, platform_routes, review_routes
│   ├── schemas/           # game_schema, platform_schema, review_schema, pagination (Pydantic)
│   ├── services/          # game_service, platform_service, review_service
│   └── utils/             # pagination (build_paginated_response)
├── tests/
│   └── test_api.py        # Pruebas de integración con SQLite en memoria
├── Dockerfile             # Build multi-stage (python:3.14-slim)
├── Jenkinsfile            # Pipeline CI/CD
├── sonar-project.properties
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── DISEÑO.md              # Documento de diseño (diagramas, DB lógica/física)
├── REQUERIMIENTOS.md      # Requerimientos y endpoints
└── DIAGRAMAS_VISUALES.md  # Diagramas adicionales
```

## 5. Modelo de datos

- **`games`** (clase `Game`): `id` (PK), `title`, `description`, `GameDBId`, campos `image_*`,
  `Platform`, `Publisher`, `releasedate`, `players`, `genre`, múltiples `youtube_*`, `wiki_*`,
  `spotify_ost`, `ign_url`, `metacritic_*`, `3djuegos_*`, `areajugones_url`, `meristation_url`,
  `opencritic_url`, `esrb_letter`, `esbr_message`.
  - Nota: `Platform` se usa como valor de filtro y está indexado. `title` también está indexado.
  - Los campos `3djuegos_url` / `3djuegos_score` se mapean con **alias** porque un identificador
    de Python no puede empezar por número.
- **`platform`** (clase `Platform`): `id` (PK), `description` (NOT NULL), `url` (nullable).
  - `find_all()` filtra por `url IS NOT NULL`.
- **`review`** (clase `Review`): `id` (PK), `name`, `date`, `review` (NOT NULL), `score`,
  `source` (NOT NULL), `id_game` (FK → `games.id`, `ON DELETE SET NULL`, `ON UPDATE CASCADE`).
- **No hay relaciones ORM** (`relationship`) declaradas; solo la FK a nivel de base de datos.

## 6. Endpoints expuestos

### Root
- `GET /` → mensaje de bienvenida con referencia a `/docs`.
- `GET /favicon.ico` → `204 No Content` (para evitar ruido 404 en logs).

### Games (`/games`)
- `GET /games/` → lista paginada filtrable por plataforma; query params `platform` (opcional),
  `page` (default 1), `limit` (default 10). Respuesta `PaginatedGameSummaryResponse`
  (`data` + `pagination`) donde cada registro expone **solo** `id`, `title` y `platform`.
  El repositorio selecciona únicamente esas columnas (no carga las columnas `Text` pesadas).
- `GET /games/search?title=...&page=&limit=` → búsqueda por prefijo de título (400 si falta `title`).
- `GET /games/{id}` → juego por ID (404 si no existe).
- `GET /games/random` → juego al azar con tráiler para la pantalla de inicio del SPA.
  Respuesta `RandomGameResponse` con `id`, `title`, `platform`, `publisher`, `releasedate`,
  `players`, `genre`, `imageOriginal` y `youtubeTrailer` (camelCase). Solo considera juegos
  con `youtube_Trailer` no nulo ni vacío; si no hay ninguno responde 404 con
  `"No hay juegos con tráiler disponible"`. El repositorio cuenta primero y elige un
  `OFFSET` aleatorio en Python (portable entre MySQL y SQLite). La ruta se declara **antes**
  de `/games/{id}` o FastAPI intentaría parsear `"random"` como entero.
- `POST /games/` → crea juego (`GameCreate`, responde 201).
- `PUT /games/{id}` → actualiza juego.
- `DELETE /games/{id}` → elimina juego.

### Platforms (`/platforms`)
- `GET /platforms/` → lista paginada de plataformas con `url` no nulo; query params
  `page` (default 1), `limit` (default 10). Respuesta `PaginatedPlatformResponse`
  (`data` + `pagination`).
- `GET /platforms/{id}` → plataforma por ID (404 si no existe).
- `POST /platforms/`, `PUT /platforms/{id}`, `DELETE /platforms/{id}`.

### Reviews (`/reviews`)
- `GET /reviews/{id}` → reseñas del juego con ese `id`, **paginadas**; query params `page`
  (default 1) y `limit` (default 10). Respuesta `PaginatedReviewResponse` (`data` +
  `pagination`) y orden por `id`, para que la paginación sea estable entre páginas.
  Devuelve 404 solo si el juego no tiene **ninguna** reseña; una página fuera de rango
  responde 200 con `data` vacía y el total real en `pagination`.

> **Paginación:** estructura `{ "data": [...], "pagination": { "currentPage", "perPage",
> "totalRecords", "totalPages" } }`. `totalPages = ceil(total / limit)`. Los query params
> `page` y `limit` se validan con `Query(ge=0)` y `Query(ge=1)` respectivamente.

## 7. Configuración y variables de entorno

La conexión se construye en `app/database.py` a partir de variables de entorno (cargadas con
`python-dotenv` desde un archivo `.env`):

| Variable      | Default          |
| ------------- | ---------------- |
| `DB_USER`     | `admin`          |
| `DB_PASSWORD` | `password`       |
| `DB_HOST`     | `192.168.1.13`   |
| `DB_NAME`     | `game`           |

URL resultante: `mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}`.

El **engine** usa `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True` y `pool_recycle=3600`
(evita reutilizar conexiones cerradas por el `wait_timeout` del servidor). Las sesiones se crean
con `async_sessionmaker` y `expire_on_commit=False`. La dependencia `get_db()` garantiza el cierre
de la sesión tras cada request.

> **Nunca** subas el archivo `.env` ni credenciales reales al repositorio.

## 8. Build, ejecución y pruebas

### Instalación local (entorno de desarrollo)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Ejecutar la aplicación

```bash
uvicorn app.main:app --reload
# Alternativa: python app/main.py
```

Servidor en `http://localhost:8000` — Swagger en `http://localhost:8000/docs`.

### Ejecutar pruebas

```bash
pip install pytest pytest-cov httpx aiosqlite pytest-asyncio
pytest -W ignore --cov=app --cov-report=xml:coverage.xml --cov-report=html:htmlcov
```

- `pytest.ini` define `asyncio_mode = auto` y
  `addopts = --junitxml=reports/junit.xml` con `junit_family = xunit2`, por lo que cada
  ejecución genera el reporte de resultados en `reports/junit.xml`. El directorio `reports/`
  se mantiene versionado mediante `reports/.gitkeep`.
- Reportes generados: `reports/junit.xml` (resultados de los tests, consumido por Jenkins y
  SonarQube), `coverage.xml` (cobertura para SonarQube) y `htmlcov/index.html` (cobertura
  navegable en local).
- Las pruebas usan **SQLite en memoria** (`sqlite+aiosqlite:///:memory:`) con `StaticPool` y
  sobreescriben la dependencia `get_db` mediante `app.dependency_overrides`.
- El fixture `setup_db` crea y destruye las tablas por prueba.

### Empaquetado (wheel)

```bash
pip install build
python -m build          # genera dist/*.whl y dist/*.tar.gz
```

## 9. Docker

`Dockerfile` multi-stage basado en `python:3.14-slim`:

1. **Stage builder:** instala `gcc` y `python3-dev` (por si alguna dependencia no publica
   wheel para Python 3.14) e instala las dependencias Python en `/install`. **No** se instalan
   cabeceras de MariaDB: `aiomysql` usa `PyMySQL`, que es Python puro y no enlaza con
   `libmariadb`.
2. **Stage final:** copia las librerías, crea el usuario no root `appuser`, copia `app/` y
   `.env` con `COPY --chown` (evita una capa extra con `chown -R`), expone el puerto `8000` y
   define un `HEALTHCHECK` contra `GET /`. `PYTHONUNBUFFERED=1` hace que los logs se vean al
   instante en `docker logs`.

Comando de arranque: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

> Requisito: el contexto de build debe ser la **raíz del proyecto** (copia `app/` y `.env`).
> El `.env` queda embebido en la imagen; lo recomendable es inyectarlo en runtime
> (`docker run --env-file .env ...`) para no exponer credenciales.

## 10. CI/CD (Jenkins + Sonar + Nexus)

`Jenkinsfile` (pipeline declarativo) ejecuta:

1. **Clean Install:** crea venv (`--without-pip`), instala pip vía bootstrap y las dependencias.
2. **Test & Sonar Analysis:** instala `pytest`, `pytest-cov`, `httpx>=0.28.1`, `aiosqlite`,
   `pytest-asyncio`; ejecuta pytest con cobertura XML (`coverage.xml`), cobertura HTML
   (`htmlcov/`) y reporte JUnit de resultados (`reports/junit.xml`); después lanza
   `sonar-scanner` con `sonar.python.coverage.reportPaths` y `sonar.python.xunit.reportPath`
   contra SonarQube (`http://172.17.0.1:9000`).
3. **Package (Wheel):** `python -m build` (versión `1.0.${BUILD_NUMBER}`).
4. **Publish to Nexus:** sube el wheel con `twine` al repositorio PyPI de Nexus.

El bloque `post { always }` publica `reports/junit.xml` con el step `junit`
(`allowEmptyResults: true`) para que los resultados de los tests aparezcan en la vista del
build, y archiva `coverage.xml`, `reports/junit.xml` y `htmlcov/**` como artefactos.

`sonar-project.properties`: `sonar.sources=app`, `sonar.tests=tests`, versión Python 3.14,
cobertura en `coverage.xml`, resultados de tests en `reports/junit.xml`, exclusiones de
`venv/`, `dist/`, `build/`, etc.

## 11. Convenciones de desarrollo

- **Imports absolutos con prefijo `app.`** (p. ej. `from app.database import get_db`). El
  proyecto no usa imports relativos.
- **Mantener el flujo de capas:** una nueva funcionalidad requiere tocar
  `schema → model (si aplica) → repository → service → controller → route`. No accedas a la
  base de datos desde controllers/services; todo el SQL va en los repositorios.
- **Errores HTTP:** usa `HTTPException` con `detail` en español (p. ej. `"Juego no encontrado"`).
- **Serialización:** define los contratos con Pydantic; usa
  `model_config = ConfigDict(from_attributes=True)` en los schemas de respuesta para mapear
  modelos ORM (no uses el `class Config` de Pydantic v1, está deprecado).
- **Alias de campos:** usa `Field(alias=...)` + `populate_by_name = True` cuando el nombre del
  campo no sea válido como identificador Python.
- **Estilo moderno de tipos:** `X | None` en lugar de `Optional[X]`, `list[...]`/`dict[...]` en
  lugar de `List[...]`/`Dict[...]`, y `Annotated[T, Depends(...)]` / `Annotated[int, Query(...)]`
  en las rutas de FastAPI.
- **Type hints y docstrings:** anota y documenta repositorios, servicios y controladores
  (docstrings en **español**).
- **Todo es `async`:** repositorios, servicios, controllers y endpoints. No introduzcas I/O
  bloqueante en la ruta de request.
- **Tests:** añade o actualiza pruebas en `tests/test_api.py` (o nuevos `tests/test_*.py`) para
  cualquier cambio de comportamiento; usa SQLite en memoria y sobreescribe `get_db`.

## 12. Áreas no implementadas / deuda técnica conocida

- **Sin autenticación/autorización** (endpoints públicos, sin JWT ni roles).
- **CRUD completo de `games` y `platform`:** `POST`/`PUT`/`DELETE` responden 404 con
  `detail` en español cuando el id no existe, y `{"deleted": true}` al borrar.
- **Reviews** solo implementa lectura (`GET /reviews/{id}`); no hay create/update/delete.
- **Sin `relationship` ORM** entre entidades.
- **Manejo de errores y logging** no centralizados.
- **Validación de esquema** mínima (no hay longitudes mínimas/máximas estrictas).
- El repositorio de plataformas filtra `url IS NOT NULL` en `find_all()`, por lo que plataformas
  sin URL no se listan.
- `GET /games/` sin filtro de plataforma compara `Game.Platform == None`, por lo que solo
  devuelve juegos con `Platform` nulo.

## 13. Referencias

- `README.md` — comandos de instalación y ejemplos de respuesta de la API.
- `DISEÑO.md` — diagramas de clases, secuencia, flujo y diseño de base de datos.
- `REQUERIMIENTOS.md` — entidades, endpoints y comportamiento esperado.
- `DIAGRAMAS_VISUALES.md` — diagramas adicionales.
