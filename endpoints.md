# Contrato de endpoints — backend-python

Réplica funcional de `backend-node20`: mismos nombres de endpoint bajo `/api`, mismo
esquema de seguridad (JWT HS256 compartido con `backend-node20`/`rss-game-node`) y puerto
**7000**. Este documento es la fuente de verdad del contrato HTTP de la app Python; si
cambias rutas, métodos, parámetros o auth, actualízalo.

Formato de error uniforme: `{ "error": "<mensaje en español>" }`.

## 1. Inventario

| # | Método | Ruta | Auth |
|---|--------|------|------|
| 1 | GET | `/api/saludo` | pública |
| 2 | GET | `/api/hello` | pública |
| 3 | POST | `/api/auth/login` | pública |
| 4 | GET | `/api/auth/me` | JWT |
| 5 | GET | `/api/games` | JWT |
| 6 | GET | `/api/games/search` | JWT |
| 7 | GET | `/api/games/random` | JWT |
| 8 | GET | `/api/games/{id}` | JWT |
| 9 | GET | `/api/games/{id}/similar` | JWT |
| 10 | POST | `/api/games` | JWT admin |
| 11 | PUT | `/api/games/{id}` | JWT admin |
| 12 | DELETE | `/api/games/{id}` | JWT admin |
| 13 | GET | `/api/platforms` | JWT |
| 14 | GET | `/api/platforms/{id}` | JWT |
| 15 | GET | `/api/platforms/{id}/top-games` | JWT |
| 16 | POST | `/api/platforms` | JWT admin |
| 17 | PUT | `/api/platforms/{id}` | JWT admin |
| 18 | DELETE | `/api/platforms/{id}` | JWT admin |
| 19 | GET | `/api/reviews/{id}` | JWT |
| 20 | GET | `/api/stats` | JWT |
| 21 | GET | `/api-docs` | pública (por entorno) |
| 22 | GET | `/api-docs.json` | pública (por entorno) |

Notas de registro:

- Las rutas se montan en `app/main.py` con `include_router(..., prefix="/api")`.
- En `app/routes/game_routes.py` el orden es: `/search`, `/random`, `/` (GET), `/{id}` (GET),
  `/` (POST), `/{id}` (PUT), `/{id}` (DELETE). En `platform_routes.py`: `/`,
  `/{id}/top-games`, `/{id}` (GET), `/` (POST), `/{id}` (PUT), `/{id}` (DELETE); en
  `similar_routes.py`: `/{id}/similar` bajo `/api/games`.
- Node tolera la barra final: cada endpoint de colección acepta `/api/games` y
  `/api/games/` (la forma sin barra es la documentada en OpenAPI).

## 2. Autenticación

- `POST /api/auth/login`
  - Body `{ "username": "...", "password": "..." }`.
  - 200 → `{ "token": "<JWT HS256>", "tokenType": "Bearer", "expiresAt": "<ISO-8601>" }`
    con `Cache-Control: no-store` y `Pragma: no-cache`.
  - 400 → `{ "error": "Usuario y contraseña son obligatorios" }` (ausentes o no string) o
    `{ "error": "Credenciales inválidas" }` (longitud > 100/200).
  - 401 → `{ "error": "Credenciales inválidas" }` (usuario/contraseña incorrectos o
    `AUTH_PASSWORD_HASH` sin configurar).
  - 500 → `{ "error": "Error al iniciar sesión" }`.
- `GET /api/auth/me` (JWT)
  - 200 → `{ "username": "<sub>", "role": "<claim role>" }` con `Cache-Control: no-store`.
  - 401 → `{ "error": "No autorizado" }` + `WWW-Authenticate: Bearer`.
- Verificación: HS256, `issuer`/`audience`/`exp` y claims `sub`/`role` obligatorios.
- Los tokens se emiten y verifican con las mismas variables que Node (`JWT_SECRET`,
  `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXPIRES_IN`).
- Rutas de negocio sin token o con token inválido → 401 `{"error": "No autorizado"}`;
  escrituras con rol distinto de `admin` → 403 `{"error": "Acceso denegado"}`.

## 3. Contratos

### 3.1 `GET /api/saludo`
200 → `{ "mensaje": "¡Hola desde Python con FastAPI!" }`.

### 3.2 `GET /api/hello`
200 → `{ "mensaje": "¡Conectado a MariaDB!", "fecha": "<ISO-8601 UTC>" }`.
500 → `{ "error": "Error en la base de datos" }`.

### 3.3 `GET /api/games`
Query: `platform?`, `genre?`, `year?`, `decade?`, `players?`, `sort?`, `page?` (default 1),
`limit?` (default 10).
- Sin filtros avanzados: `WHERE Platform = ?`; sin `platform` responde `data: []` y
  `totalRecords: 0`.
- Con filtros avanzados: `platform =`, `genre =`, `year` → `releasedate LIKE 'YYYY%'`,
  `decade` → `releasedate LIKE 'YYY%'`, `players` → `players LIKE 'valor%'`; `sort` es una
  whitelist: `id_asc` (default), `id_desc`, `title_asc`, `title_desc`, `year_asc`,
  `year_desc`, `score_desc`. Un valor desconocido cae a `id_asc`.
- 200 →
  `{ "data": [ { "id", "title", "platform" } ], "pagination": { "currentPage", "perPage", "totalRecords", "totalPages" } }`.
- Validación inválida (p. ej. `limit=0`) → 400 `{ "error": "Petición inválida" }`.

### 3.4 `GET /api/games/search`
Query: `title` (**obligatorio**), `page?`, `limit?`.
- Sin `title` → 400 `{ "error": "El parámetro \"title\" es requerido" }`.
- 200 → paginado igual que 3.3 (solo `id`, `title`, `platform`), `title LIKE 'term%'` con el
  backslash escapado.

### 3.5 `GET /api/games/random`
Query: `platform?`, `genre?`.
- 200 → `{ id, title, description, platform, publisher, releasedate, players, genre,
  imageMedium, imageLarge, imageOriginal, imageFront, youtubeTrailer }` (camelCase).
- 404 → `{ "error": "No hay ningún juego con tráiler disponible" }`.
- Algoritmo sin filtros: rango de ids por PK + sorteo + consulta por PK (sin `ORDER BY RAND()`).
  Con filtros: `MAX(id)` del subconjunto, sorteo, reintentos y fallback al primer juego
  filtrado ordenado por id.

### 3.6 `GET /api/games/{id}`
200 → fila completa de `games` con los nombres de columna reales (`Platform`, `releasedate`,
`metacritic_score`, `image_*`, `youtube_Trailer`...).
404 → `{ "error": "Juego no encontrado" }`.

### 3.7 `GET /api/games/{id}/similar`
Query: `limit?` (entero positivo; si no es válido se devuelven todos).
- 200 →
  `{ "gameId": n, "total": n, "similarGames": [ { "id", "title", "similarity", "similarityPercentage" } ] }`
  ordenado por similitud descendente y excluyendo el propio juego.
- 404 → `{ "error": "No se encontraron juegos similares para el juego indicado" }`.
- 500 → `{ "error": "Error al obtener juegos similares" }` (JSON inválido en `similar_game`).

### 3.8 `POST /api/games` (admin)
Body `GameCreate` (contrato Pydantic con `title`/`description` y el resto de columnas
opcionales).
201 → entidad creada, con `id`.

### 3.9 `PUT /api/games/{id}` (admin)
200 → entidad actualizada; 404 → `{ "error": "Juego no encontrado" }`.

### 3.10 `DELETE /api/games/{id}` (admin)
200 → `{ "deleted": true }`; 404 → `{ "error": "Juego no encontrado" }`.

### 3.11 `GET /api/platforms`
Query: `page?`, `limit?`.
200 → `{ "data": [fila platform], "pagination": {...} }` (solo `url IS NOT NULL`).

### 3.12 `GET /api/platforms/{id}/top-games`
200 → array de hasta 10 juegos (`id`, `title`, `Platform`, `genre`, `releasedate`,
`image_Original`, `metacritic_score`) ordenados por `CAST(metacritic_score AS INTEGER) DESC`;
`[]` si no hay juegos con nota.

### 3.13 `GET /api/platforms/{id}`
200 → fila `platform`; 404 → `{ "error": "Plataforma no encontrada" }`.

### 3.14 `POST/PUT/DELETE /api/platforms[/{id}]` (admin)
201/200 con la entidad o `{ "deleted": true }`; 404 si el id no existe.

### 3.15 `GET /api/reviews/{id}`
`:id` es el `id_game`; query `page?`, `limit?`.
- 200 →
  `{ "data": [filas review], "pagination": {...} }` (`ORDER BY id`).
- 404 cuando `totalRecords === 0` → `{ "error": "Reseñas no encontradas para este juego" }`.
- Una página fuera de rango responde 200 con `data` vacía y el total real.

### 3.16 `GET /api/stats`
200 →
`{ "summary": { "totalGames", "scoredGames", "totalPlatforms", "totalGenres" },
  "platforms": [{label,total}], "genres": [...], "decades": [...] }`.
Caché en memoria de 10 minutos (las peticiones concurrentes comparten el cálculo).
500 → `{ "error": "Error al obtener las estadísticas del catálogo" }`.

### 3.17 Documentación
- `GET /api-docs` → Swagger UI (HTML).
- `GET /api-docs.json` → documento OpenAPI 3.1.
- En producción quedan apagadas salvo `API_DOCS_ENABLED=true`; `false` las apaga siempre.

## 4. Comportamiento global (seguridad)

- **Cabeceras**: CSP, HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options`,
  `Referrer-Policy`, COOP/CORP, etc. Sin CSP en `/api-docs`.
- **CORS**: allowlist de `app/main.py` (o `CORS_ORIGINS`); en desarrollo cualquier
  `http://localhost[:puerto]` / `http://127.0.0.1[:puerto]`. Métodos
  `GET, POST, PUT, DELETE`; headers `Content-Type, Authorization, apikey`.
- **Cuerpo**: máximo 10 kb → 413
  `{"error": "El cuerpo de la petición es demasiado grande"}`; JSON malformado → 400
  `{"error": "Petición inválida"}`.
- **Rate limiting** en memoria por IP: API 300/15 min y login 5/15 min → 429 con
  `RateLimit-*` y `Retry-After` (`TRUST_PROXY=true` usa `X-Forwarded-For`).
- **404** ruta desconocida → `{ "error": "Ruta no encontrada" }`.
- **500** → `{ "error": "Error interno del servidor" }` sin stack trace.

## 5. Diferencias conocidas con Node

- No se replica el módulo de Telegram (`/api/telegram/*`): es un bot opcional que requiere
  `TELEGRAM_BOT_TOKEN` y no lo consume el frontend.
- Las respuestas de escritura conservan el contrato Python (`{ "deleted": true }` / entidad)
  en lugar del resumen `mysql2` de Node.
- `/api/platforms` sigue siendo paginado (el frontend tolera paginado y array plano).
- La validación de FastAPI/Pydantic se normaliza a **400** `{"error": "Petición inválida"}`
  en lugar del 422 por defecto.
