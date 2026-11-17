# GEMINI.md — backend-python

Contexto instructivo para agentes de IA que trabajen en este repositorio.

## 1. Resumen del proyecto

**backend-python** es una API REST para la gestión de **videojuegos**, **plataformas** y
**reseñas**. Está construida con **FastAPI** y persiste datos en **MySQL/MariaDB** usando
**SQLAlchemy en modo asíncrono** (`aiomysql`).

- Título de la API (OpenAPI): `Games API` — versión `1.0.0`.
- Documentación interactiva en `/api-docs` (Swagger UI) y OpenAPI en `/api-docs.json`.
- Los endpoints viven bajo **`/api`** con los mismos nombres que `backend-node20`
  (`/api/games`, `/api/platforms`, `/api/reviews/{id}`, `/api/similar`... etc.).
- Las rutas de negocio exigen **JWT HS256** (secreto, `issuer` y `audience` compartidos con
  `backend-node20` y `rss-game-node`); las escrituras exigen además rol `admin`.
- La aplicación escucha en el puerto **7000**.
- El código y la documentación de diseño están redactados en **español**; mantén ese idioma
  en comentarios, `detail` de excepciones y mensajes nuevos.

## 2. Stack tecnológico

| Componente        | Tecnología                                   |
| ----------------- | -------------------------------------------- |
| Lenguaje          | Python 3.14                                  |
| Framework web     | FastAPI >= 0.142.2                           |
| Servidor ASGI     | Uvicorn >= 0.54.0                            |
| ORM               | SQLAlchemy >= 2.1.3 con extra `asyncio` (async; instala `greenlet`) |
| Driver DB         | aiomysql >= 0.3.2                            |
| Validación/schemas| Pydantic >= 2.13.5                           |
| Configuración     | python-dotenv >= 1.2.4                       |
| Criptografía      | cryptography >= 50.0.2                       |
| Autenticación     | PyJWT >= 2.10.1 (HS256) + bcrypt >= 4.2.1    |
| Base de datos     | MySQL / MariaDB                              |
| Testing           | pytest + pytest-asyncio + httpx + aiosqlite  |
| Calidad           | SonarQube / sonar-scanner                    |
| CI/CD             | Jenkins (Jenkinsfile) + Nexus (PyPI repo)    |
| Empaquetado       | setuptools / `python -m build` (wheel)       |

## 3. Arquitectura (capas)

El proyecto sigue una **arquitectura en capas**. Cada petición fluye en una sola dirección:

```
Routes → Middlewares (JWT, cabeceras, rate limiting) → Controllers → Services → Repositories
                              → Models (ORM) → DB
                          ↕
                     Schemas (Pydantic)  ← contratos de entrada/salida JSON
```

- **Middlewares** (`app/middlewares/`): `authenticate_jwt` (dependencia FastAPI que valida el
  JWT y expone `AuthUser`; `require_role`/`require_admin` para escrituras) y `security`
  (cabeceras tipo Helmet, límite de cuerpo de 10 kb y rate limiting por IP).
- **Configuración** (`app/config/auth.py`): secreto/`issuer`/`audience` JWT, usuario estático
  y validación fail-closed en producción.
- **Errores** (`app/errors.py`): normaliza todas las respuestas a `{"error": "<mensaje>"}`
  (400 de validación, 404 de ruta, 500 sin stack trace).
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

### Flujo de una petición (ejemplo `GET /api/games/{id}`)

`Cliente → Route → Controller → Service → Repository → DB` y de vuelta, serializando con
Pydantic. Si no existe el recurso, el **Controller** lanza `HTTPException(404)`.

## 4. Estructura de directorios

```
backend-python/
├── app/
│   ├── main.py            # App FastAPI: CORS, seguridad, routers /api y docs /api-docs
│   ├── database.py        # Engine async, AsyncSessionLocal, Base, dependencia get_db()
│   ├── errors.py          # Manejadores globales de errores (contrato {"error": ...})
│   ├── config/auth.py     # Configuración JWT, usuario estático y validación de arranque
│   ├── middlewares/       # authenticate_jwt (JWT/roles) y security (headers, body, rate limit)
│   ├── controllers/       # game, platform, review, similar_games, stats, auth, main
│   ├── models/            # game, platform, review, similar_game (ORM)
│   ├── repositories/      # game, platform, review, similar_games, stats, main
│   ├── routes/            # main, auth, game, similar, platform, review, stats
│   ├── schemas/           # game, platform, review, similar, stats, auth, pagination (Pydantic)
│   ├── services/          # game, platform, review, similar_games, stats, auth
│   └── utils/             # pagination (build_paginated_response)
├── tests/
│   ├── conftest.py        # Entorno JWT de test + rate limits altos
│   └── test_api.py        # Pruebas de integración con SQLite en memoria
├── Dockerfile             # Build multi-stage (python:3.14-slim), puerto 7000
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
- **`similar_game`** (clase `SimilarGame`): `id_game` (PK, juego de referencia) y `json` (TEXT
  con el array `[{ id, title, similarity }]` precalculado). Lo expone
  `GET /api/games/{id}/similar`, que excluye el propio juego y calcula el porcentaje de
  similitud redondeado a dos decimales.
- **No hay relaciones ORM** (`relationship`) declaradas; solo la FK a nivel de base de datos.

## 6. Endpoints expuestos

### Root y utilidades
- `GET /` → mensaje de bienvenida con referencia a `/api-docs`.
- `GET /favicon.ico` → `204 No Content` (para evitar ruido 404 en logs).
- `GET /api-docs` → Swagger UI y `GET /api-docs.json` → OpenAPI 3.1.
- `GET /api/saludo` → mensaje de bienvenida (pública).
- `GET /api/hello` → health-check de la BD; responde `{ "mensaje": "¡Conectado a MariaDB!",
  "fecha": "<ISO-8601>" }` o 500 `{ "error": "Error en la base de datos" }` (pública).

### Autenticación (`/api/auth`)
- `POST /api/auth/login` con `{ "username", "password" }` → 200
  `{ "token", "tokenType": "Bearer", "expiresAt" }`; 400 si faltan credenciales o la
  longitud excede 100/200; 401 `Credenciales inválidas`; 500 `Error al iniciar sesión`.
  Añade `Cache-Control: no-store` y `Pragma: no-cache`.
- `GET /api/auth/me` (JWT) → `{ "username", "role" }`; 401 `No autorizado` con
  `WWW-Authenticate: Bearer`.

### Games (`/api/games`, todas JWT)
- `GET /api/games` → lista paginada filtrable por `platform`, `genre`, `year`, `decade`,
  `players`, `sort`, `page` (default 1) y `limit` (default 10). Respuesta
  `PaginatedGameSummaryResponse` (`data` + `pagination`) donde cada registro expone **solo**
  `id`, `title` y `platform`. Sin `platform` (y sin filtros avanzados) responde `data: []`,
  igual que Node. `sort` acepta la whitelist `id_asc` (default), `id_desc`, `title_asc`,
  `title_desc`, `year_asc`, `year_desc`, `score_desc`.
- `GET /api/games/search?title=...&page=&limit=` → búsqueda por prefijo de título
  (400 `El parámetro "title" es requerido` si falta `title`).
- `GET /api/games/{id}` → juego por ID (404 si no existe).
- `GET /api/games/random` (`platform`/`genre` opcionales) → juego al azar con tráiler.
  Respuesta `RandomGameResponse` con `id`, `title`, `description`, `platform`, `publisher`,
  `releasedate`, `players`, `genre`, `imageMedium`, `imageLarge`, `imageOriginal`,
  `imageFront` y `youtubeTrailer` (camelCase). Si no hay ninguno responde 404 con
  `"No hay ningún juego con tráiler disponible"`.
  El repositorio **no** usa `COUNT(*)`, `ORDER BY RAND()` ni `OFFSET`: la tabla `games` ocupa
  ~1,4 GB y no tiene índice sobre `youtube_Trailer`. En su lugar obtiene el rango de ids por
  PK (`ORDER BY id LIMIT 1`), elige un id al azar y lo consulta por clave primaria; si el id
  no existe o no tiene tráiler, reintenta (`_RANDOM_ATTEMPTS`). Con filtros replica el
  algoritmo de Node (`MAX(id)` del subconjunto filtrado + sorteo + fallback). La ruta se
  declara **antes** de `/api/games/{id}`.
- `GET /api/games/{id}/similar?limit=` → similares precalculados en `similar_game`
  (`id_game`, `json` TEXT con `[{ id, title, similarity }]`). Excluye el propio juego, ordena
  por similitud descendente, calcula `similarityPercentage` (2 decimales) y responde
  `{ gameId, total, similarGames }`; 404 si no hay fila o no quedan similares; 500 si el JSON
  es inválido.
- `POST /api/games/` → crea juego (`GameCreate`, responde 201). **Rol admin.**
- `PUT /api/games/{id}` → actualiza juego. **Rol admin.**
- `DELETE /api/games/{id}` → elimina juego. **Rol admin.**

### Platforms (`/api/platforms`, todas JWT)
- `GET /api/platforms` → lista paginada de plataformas con `url` no nulo; query params
  `page` (default 1), `limit` (default 10). Respuesta `PaginatedPlatformResponse`.
- `GET /api/platforms/{id}/top-games` → top 10 juegos por `metacritic_score` (join por
  `games.Platform = platform.description`); `[]` si la plataforma no tiene juegos.
- `GET /api/platforms/{id}` → plataforma por ID (404 si no existe).
- `POST/PUT/DELETE` → **rol admin**.

### Reviews (`/api/reviews`, JWT)
- `GET /api/reviews/{id}` → reseñas del juego con ese `id`, **paginadas**; query params `page`
  (default 1) y `limit` (default 10). Respuesta `PaginatedReviewResponse` (`data` +
  `pagination`) y orden por `id`. Devuelve 404 solo si el juego no tiene **ninguna** reseña;
  una página fuera de rango responde 200 con `data` vacía y el total real en `pagination`.

### Stats (`/api/stats`, JWT)
- `GET /api/stats` → `{ summary: { totalGames, scoredGames, totalPlatforms, totalGenres },
  platforms: [{label,total}], genres: [...], decades: [...] }`. Caché en memoria **10
  minutos**; las peticiones concurrentes comparten el cálculo en vuelo y un error no se
  cachea. Los `GROUP BY` sobre la BD remota son costosos (primera llamada lenta).

> **Paginación:** estructura `{ "data": [...], "pagination": { "currentPage", "perPage",
> "totalRecords", "totalPages" } }`. `totalPages = ceil(total / limit)`. Los query params
> `page` y `limit` se validan con `Query(ge=0)` y `Query(ge=1)` respectivamente; un valor
> inválido se normaliza a 400 `{"error": "Petición inválida"}`.

> **Autenticación:** todas las rutas de negocio exigen `Authorization: Bearer <jwt>` HS256
> (mismo secreto, `issuer` y `audience` que Node). Sin token o con token inválido → 401
> `{"error": "No autorizado"}` + `WWW-Authenticate: Bearer`; rol insuficiente → 403
> `{"error": "Acceso denegado"}`. `POST`, `PUT` y `DELETE` de juegos/plataformas exigen rol
> `admin`. El login es público.

## 7. Configuración y variables de entorno

La conexión se construye en `app/database.py` a partir de variables de entorno (cargadas con
`python-dotenv` desde un archivo `.env`):

| Variable      | Default          |
| ------------- | ---------------- |
| `DB_USER`     | `admin`          |
| `DB_PASSWORD` | `password`       |
| `DB_HOST`     | `192.168.1.82`   |
| `DB_PORT`     | `3306`           |
| `DB_NAME`     | `game`           |

URL resultante: `mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`.

Variables de seguridad y servidor (ver `.env.example`):

| Variable | Uso |
| -------- | --- |
| `ENVIRONMENT` / `NODE_ENV` | `production` activa el modo fail-closed (obligatorio `JWT_SECRET` y `AUTH_PASSWORD_HASH`) |
| `JWT_SECRET` / `JWT_EXPIRES_IN` / `JWT_ISSUER` / `JWT_AUDIENCE` | JWT HS256 compartido con Node (`1h`, `rss-game-node`, `rss-game-node-api`) |
| `AUTH_USERNAME` / `AUTH_ROLE` / `AUTH_PASSWORD_HASH` | Usuario estático y hash bcrypt de la contraseña |
| `CORS_ORIGINS` / `TRUST_PROXY` | Allowlist de CORS y confianza en proxy inverso para el rate limiting |
| `API_RATE_LIMIT_WINDOW_MS` / `API_RATE_LIMIT_MAX` | Límite global por IP (300 / 15 min) |
| `AUTH_RATE_LIMIT_WINDOW_MS` / `AUTH_RATE_LIMIT_MAX` | Límite de login por IP (5 / 15 min) |
| `API_DOCS_ENABLED` | Swagger en `/api-docs` (en producción solo si es `true`) |
| `PORT` / `HOST` | Puerto (**7000**) e interfaz del servidor |

El **engine** usa `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True` y `pool_recycle=3600`
(evita reutilizar conexiones cerradas por el `wait_timeout` del servidor). Las sesiones se crean
con `async_sessionmaker` y `expire_on_commit=False`. La dependencia `get_db()` garantiza el cierre
de la sesión tras cada request.

> **Nunca** subas el archivo `.env` ni credenciales reales al repositorio.

### Seguridad HTTP (réplica de backend-node20)

- **JWT HS256** (`app/services/auth_service.py`, `app/middlewares/authenticate_jwt.py`):
  mismo secreto/`issuer`/`audience` que Node; `sub` = usuario y claim `role`. 401
  `{"error": "No autorizado"}` con `WWW-Authenticate: Bearer` y 403 `{"error": "Acceso
  denegado"}` por rol insuficiente.
- **Login** (`POST /api/auth/login`): bcrypt + comparación en tiempo constante del usuario;
  `Cache-Control: no-store` y `Pragma: no-cache`.
- **Cabeceras** (`app/middlewares/security.py`): CSP, HSTS, `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, COOP/CORP...; la CSP se omite en `/api-docs` porque
  Swagger UI usa scripts/estilos inline.
- **CORS**: allowlist explícita (por defecto en `app/main.py`; `CORS_ORIGINS` la
  sobreescribe). Incluye los orígenes del SPA React 19 en Vite (`:5173`), `vite preview`
  (`:4173`) y Nginx (`:8065`) para `localhost` y `127.0.0.1`, sus equivalentes en las IPs
  del servidor (`192.168.1.82`, `200.83.105.123`) y el frontend Angular legacy
  (`:4200`/`:4300`). En desarrollo se aceptan `http://localhost[:puerto]` y
  `http://127.0.0.1[:puerto]`; en producción solo la allowlist. Headers permitidos:
  `Content-Type`, `Authorization`, `apikey`.
- **Cuerpo JSON**: máximo 10 kb → 413
  `{"error": "El cuerpo de la petición es demasiado grande"}`; JSON malformado o validación
  de esquema → 400 `{"error": "Petición inválida"}`.
- **Rate limiting** en memoria por IP: global 300 / 15 min y login 5 / 15 min → 429 con
  `RateLimit-*` y `Retry-After`. `TRUST_PROXY=true` usa `X-Forwarded-For` (solo con proxy
  de confianza).
- **404 y 500** siempre en JSON (`{"error": "Ruta no encontrada"}` / genérico sin stack).
- **Swagger por entorno**: `/api-docs` y `/api-docs.json`; en producción apagado salvo
  `API_DOCS_ENABLED=true`.

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
uvicorn app.main:app --reload --port 7000
# Alternativa (usa el puerto 7000 por defecto): python -m app.main
```

Servidor en `http://localhost:7000` — Swagger en `http://localhost:7000/api-docs` y
OpenAPI en `http://localhost:7000/api-docs.json`.

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
   - **Debe ser `python:3.14-slim` (Debian/glibc), nunca `python:3.14-alpine`**: los paquetes
     compilados se copian al stage final (también Debian), así que builder y runtime tienen
     que compartir la ABI (un builder musl genera binarios incompatibles con la glibc final).
     Además Alpine usa `apk`, así que el `apt-get` del builder falla con `exit code: 127`.
   - Todas las dependencias publican wheels `cp314` manylinux para x86_64 (verificado con
     `pip download --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.14`,
     incluidas `cryptography`, `bcrypt`, `cffi`, `greenlet` y `pydantic-core`), por lo que
     `gcc` es solo una red de seguridad.
2. **Stage final:** copia las librerías, crea el usuario no root `appuser`, copia `app/` con
   `COPY --chown` (evita una capa extra con `chown -R`), expone el puerto `7000` y
   define un `HEALTHCHECK` contra `GET /`. `PYTHONUNBUFFERED=1` hace que los logs se vean al
   instante en `docker logs`.

Comando de arranque: `uvicorn app.main:app --host 0.0.0.0 --port 7000 --no-server-header`.

> **Dependencia crítica:** `requirements.txt` declara `sqlalchemy[asyncio]`, no `sqlalchemy` a
> secas. SQLAlchemy 2.x ya no instala `greenlet` por defecto y el arranque falla con
> `ModuleNotFoundError: No module named 'greenlet'` al importar `sqlalchemy.ext.asyncio`.
> El Dockerfile ejecuta un `python -c "from app.main import app"` en el build para detectar
> este tipo de fallos antes de arrancar el contenedor.

> Requisito: el contexto de build debe ser la **raíz del proyecto** (copia `app/`).
> Las credenciales **no** se hornean en la imagen: se inyectan en runtime con
> `docker run --env-file .env ...` (o variables del orquestador). El `.dockerignore`
> excluye `.env`/`.env.*`; `.env.example` documenta las variables necesarias.

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

- **Autenticación JWT ya implementada** (misma seguridad que `backend-node20`): las rutas de
  negocio exigen token y las escrituras exigen rol `admin`. El login valida contra el hash
  bcrypt de `AUTH_PASSWORD_HASH`.
- **CRUD completo de `games` y `platform`:** `POST`/`PUT`/`DELETE` responden 404 con
  `detail` en español cuando el id no existe, y `{"deleted": true}` al borrar.
- **Reviews** solo implementa lectura (`GET /api/reviews/{id}`); no hay create/update/delete.
- **Sin `relationship` ORM** entre entidades.
- **Validación de esquema** mínima (no hay longitudes mínimas/máximas estrictas en `game` y
  `platform`).
- El repositorio de plataformas filtra `url IS NOT NULL` en `find_all()`, por lo que plataformas
  sin URL no se listan (el endpoint paginado mantiene ese filtro).
- `GET /api/games` sin `platform` y sin filtros avanzados responde `data: []` (paridad con
  Node: la comparación se hace contra `NULL`).
- **Módulo Telegram**: no se replica el bot de `backend-node20` (módulo opcional que requiere
  `TELEGRAM_BOT_TOKEN`); no hay rutas `/api/telegram/*` en Python.
- **Stats**: cuatro consultas secuenciales sobre una sesión async; la primera llamada puede
  tardar (los `GROUP BY` de Node se lanzan en paralelo). Se mitiga con la caché de 10 min.

## 13. Referencias

- `README.md` — comandos de instalación, autenticación y endpoints.
- `endpoints.md` — contrato HTTP detallado (inventario, cuerpos, códigos y auth).
- `DISEÑO.md` — diagramas de clases, secuencia, flujo y diseño de base de datos.
- `REQUERIMIENTOS.md` — entidades, endpoints y comportamiento esperado.
- `DIAGRAMAS_VISUALES.md` — diagramas adicionales.
