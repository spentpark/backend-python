# Especificación de Requerimientos de Software (SRS)

## Games API — `backend-python`

| Campo              | Valor                                                                 |
| ------------------ | --------------------------------------------------------------------- |
| Proyecto           | `backend-python`                                                      |
| Producto           | Games API                                                             |
| Versión del producto | 1.0.0 (OpenAPI)                                                     |
| Versión del documento | 1.0                                                                |
| Fecha              | 6 de octubre de 2026                                                  |
| Estado             | Derivado del código en su estado actual                               |

> **Método de obtención:** este documento se elaboró por ingeniería inversa del repositorio
> (`app/`, `tests/`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `Jenkinsfile`,
> `sonar-project.properties`). Cada requisito incluye su **trazabilidad** al artefacto que lo
> implementa. Los requisitos no implementados se marcan explícitamente como **❌ No
> implementado** para no documentar comportamiento inexistente.

---

## 1. Introducción

### 1.1 Propósito

Definir de forma verificable los requisitos funcionales y no funcionales del servicio
**Games API**, de manera que sirva como base para desarrollo, pruebas, auditoría y aceptación.

### 1.2 Alcance

El sistema es una **API REST** que gestiona tres entidades —**juegos**, **plataformas** y
**reseñas**— sobre una base de datos **MySQL/MariaDB**. El alcance incluye:

- Exposición de endpoints HTTP/JSON y su documentación OpenAPI.
- Persistencia asíncrona mediante SQLAlchemy (`aiomysql`).
- Empaquetado como wheel, contenerización Docker y análisis de calidad en CI.

Queda **fuera del alcance** actual: autenticación/autorización, interfaz de usuario, CRUD de
reseñas, y cualquier integración con sistemas externos (scrapers, colas, etc.).

### 1.3 Audiencia

Equipo de desarrollo, QA, responsables de despliegue (DevOps) y evaluadores de calidad
(SonarQube / auditoría técnica).

### 1.4 Definiciones y abreviaturas

| Término    | Definición                                                                    |
| ---------- | ----------------------------------------------------------------------------- |
| RF         | Requisito Funcional                                                           |
| RNF        | Requisito No Funcional                                                        |
| PK / FK    | Primary Key / Foreign Key                                                     |
| ORM        | Object-Relational Mapping (SQLAlchemy)                                        |
| DTO/Schema | Contrato Pydantic de entrada o salida                                          |
| Prefijo    | Coincidencia de título que **empieza por** el texto buscado (`LIKE 'x%'`)     |

### 1.5 Referencias

- `DEEPSEEK.md` — contexto instructivo para agentes/desarrolladores.
- `DISEÑO.md` — diagramas de clases, secuencia y diseño de base de datos.
- `DIAGRAMAS_VISUALES.md` — diagramas Mermaid consolidados.
- `README.md` — instalación y ejemplos de respuesta reales.
- Documentación interactiva en `/docs` (Swagger UI) y `/redoc`.

### 1.6 Convenciones de prioridad

| Prioridad | Significado                                        |
| --------- | -------------------------------------------------- |
| **Alta**  | Necesario para el funcionamiento del producto      |
| **Media** | Mejora relevante, no bloqueante                    |
| **Baja**  | Deseable a futuro                                  |

---

## 2. Descripción general

### 2.1 Perspectiva del producto

Servicio backend autónomo, sin estado en el servidor (stateless), consumible por cualquier
cliente HTTP. No requiere autenticación: **todos los endpoints son públicos**.

### 2.2 Arquitectura

Arquitectura en capas con flujo unidireccional:

```
Routes → Controllers → Services → Repositories → Models (ORM) → DB
                          ↕
                     Schemas (Pydantic)  ← contratos JSON
```

La construcción de dependencias se realiza en las rutas mediante una *factory*
(`Repository → Service → Controller`) y se inyecta con `Depends`.

### 2.3 Funciones principales

1. Consulta y búsqueda de juegos (con paginación y filtro por plataforma).
2. Consulta de plataformas (con paginación).
3. Consulta de reseñas asociadas a un juego.
4. Alta, modificación y baja de juegos y plataformas (**especificadas, no implementadas**).
5. Documentación OpenAPI autogenerada.

### 2.4 Usuarios y características

| Usuario                | Uso esperado                                                          |
| ---------------------- | --------------------------------------------------------------------- |
| Cliente HTTP genérico  | Consumo de endpoints JSON                                              |
| Desarrollador / QA     | Consulta de `/docs`, ejecución de pruebas                              |
| Integrador front-end   | Obtención de catálogo de juegos y plataformas                          |
| Pipeline CI/CD         | Ejecución de pruebas, análisis estático, empaquetado y publicación     |

### 2.5 Restricciones

- **Lenguaje:** Python **3.14** (`requires-python = ">=3.14"`).
- **Base de datos:** MySQL / MariaDB (no hay migraciones versionadas; el esquema se crea con
  `Base.metadata`).
- **Idioma:** comentarios, docstrings, mensajes de error y documentación en **español**.
- **Imports:** absolutos con prefijo `app.` (prohibido import relativo).
- **Sin I/O bloqueante** en la ruta de petición: todo el acceso a datos es `async`.

### 2.6 Supuestos y dependencias

- Existe una instancia MySQL/MariaDB accesible con el esquema y los datos cargados.
- Las variables de entorno de conexión se proveen vía `.env` o variables del sistema.
- No se asume la existencia de relaciones ORM (`relationship`) entre entidades.

---

## 3. Requisitos funcionales

### RF-01 — Mensaje de bienvenida (raíz)

| Aspecto            | Detalle                                                          |
| ------------------ | ---------------------------------------------------------------- |
| Método y ruta      | `GET /`                                                          |
| Autenticación      | No requerida                                                     |
| Entrada            | Ninguna                                                          |
| Salida             | `200` — `{"message": "Bienvenido a la Games API", "docs": "/docs"}` |
| Errores            | Ninguno previsto                                                 |
| Prioridad          | Baja                                                             |
| Estado             | ✅ Implementado                                                  |
| Trazabilidad       | `app/main.py` → `root()`                                         |

**Criterio de aceptación:** una petición `GET /` responde `200` con las claves `message` y
`docs`.

---

### RF-02 — Supresión de ruido de favicon

| Aspecto            | Detalle                                                       |
| ------------------ | ------------------------------------------------------------- |
| Método y ruta      | `GET /favicon.ico`                                            |
| Salida             | `204 No Content` (cuerpo vacío)                               |
| Particularidad     | Excluido del esquema OpenAPI (`include_in_schema=False`)       |
| Prioridad          | Baja                                                          |
| Estado             | ✅ Implementado                                               |
| Trazabilidad       | `app/main.py` → `favicon()`                                   |

**Criterio de aceptación:** `GET /favicon.ico` responde `204` y no aparece en `/openapi.json`.

---

### RF-03 — Listado paginado de juegos (vista resumida)

| Aspecto        | Detalle                                                                        |
| -------------- | ------------------------------------------------------------------------------ |
| Método y ruta  | `GET /games/`                                                                   |
| Parámetros     | `platform` (opcional, `str`), `page` (opcional, default `1`, `>= 0`), `limit` (opcional, default `10`, `>= 1`) |
| Respuesta OK   | `200` — `PaginatedGameSummaryResponse`: `{data: [{id, title, platform}], pagination}` |
| Errores        | `422` si `page < 0` o `limit < 1`                                                |
| Prioridad      | **Alta**                                                                         |
| Estado         | ✅ Implementado                                                                  |
| Trazabilidad   | `app/routes/game_routes.py` → `get_all()`; `GameController.filter_by_platform()`; `GameService.get_by_platform()`; `GameRepository.find_by_platform_paginated()`; `GameSummary` |

**RF-03.1** Cada elemento de `data` expone **únicamente** `id`, `title` y `platform`; el
repositorio selecciona solo esas columnas para no transferir campos de texto pesados.

**RF-03.2** El campo ORM `Platform` se serializa en JSON como `platform` (minúscula).

**RF-03.3** Con `platform` informado, se devuelven los juegos cuyo campo `Platform` coincide
**exactamente** con el valor.

**RF-03.4 — Limitación conocida:** si se omite `platform`, la condición SQL generada es
`Platform IS NULL`, por lo que el listado devuelve únicamente los juegos **sin plataforma**
asignada. Es el comportamiento actual del código (`condition = Game.Platform == platform`).

**Criterio de aceptación:** `GET /games/?platform=<P>&page=0&limit=100` responde `200` con
exactamente las claves `data` y `pagination`, y cada elemento con las claves `id`, `title`,
`platform`. Verificado por `test_get_games_by_platform_campos_resumidos`.

---

### RF-04 — Búsqueda de juegos por prefijo de título

| Aspecto        | Detalle                                                                  |
| -------------- | ------------------------------------------------------------------------ |
| Método y ruta  | `GET /games/search`                                                       |
| Parámetros     | `title` (**requerido**, `str`), `page` (default `1`, `>= 0`), `limit` (default `10`, `>= 1`) |
| Respuesta OK   | `200` — `PaginatedGameResponse`: `{data: [GameResponse], pagination}`     |
| Errores        | `422` si se omite `title`; `400` `"El parámetro 'title' es requerido"` si `title` llega vacío |
| Prioridad      | **Alta**                                                                  |
| Estado         | ✅ Implementado                                                           |
| Trazabilidad   | `game_routes.py` → `search()`; `GameController.search_by_title()`; `GameRepository.find_by_title_paginated()` (`Game.title.like(f"{title}%")`) |

**RF-04.1** La coincidencia es por **prefijo** (`LIKE 'texto%'`), no por subcadena.

**RF-04.2** A diferencia de RF-03, esta respuesta devuelve el **objeto completo** del juego
(`GameResponse`, 34 campos), no la vista resumida.

**Criterio de aceptación:** `GET /games/search?title=Elden` devuelve `200` e incluye el juego
cuyo título empieza por «Elden». Verificado por `test_search_game_by_title`.

---

### RF-05 — Consulta de un juego por identificador

| Aspecto        | Detalle                                                            |
| -------------- | ------------------------------------------------------------------ |
| Método y ruta  | `GET /games/{id}`                                                  |
| Parámetros     | `id` (path, entero)                                                |
| Respuesta OK   | `200` — `GameResponse` (todos los campos del juego)                |
| Errores        | `404` `"Juego no encontrado"`                                      |
| Prioridad      | **Alta**                                                           |
| Estado         | ✅ Implementado                                                    |
| Trazabilidad   | `game_routes.py` → `get_by_id()`; `GameController.get_game_by_id()`; `GameRepository.find_by_id()` |

**Criterio de aceptación:** un `id` existente devuelve `200` con el juego; uno inexistente
devuelve `404` con `detail = "Juego no encontrado"`.

---

### RF-06 — Alta de juego

| Aspecto        | Detalle                                                        |
| -------------- | -------------------------------------------------------------- |
| Método y ruta  | `POST /games/`                                                 |
| Cuerpo         | `GameCreate` (JSON)                                            |
| Respuesta OK   | `201` — `GameResponse` con el juego creado                     |
| Prioridad      | **Alta**                                                       |
| Estado         | ❌ **No implementado** — `GameController.create_game` no existe |
| Trazabilidad   | `game_routes.py` → `create()`; falta en `app/controllers/game_controller.py`. La persistencia sí existe: `GameRepository.create()` |

**Criterio de aceptación (pendiente):** `POST /games/` con un `GameCreate` válido responde
`201` con el recurso creado, incluido su `id` autogenerado.

> **Observación:** al invocar un método inexistente del controlador, la petición actual
> finaliza con `AttributeError` → `500 Internal Server Error`.

---

### RF-07 — Actualización de juego

| Aspecto        | Detalle                                                          |
| -------------- | ---------------------------------------------------------------- |
| Método y ruta  | `PUT /games/{id}`                                                |
| Cuerpo         | `GameCreate` (JSON)                                              |
| Respuesta OK   | `200`                                                            |
| Prioridad      | **Alta**                                                         |
| Estado         | ❌ **No implementado** — `GameController.update_game` no existe   |
| Trazabilidad   | `game_routes.py` → `update()`; `GameRepository.update()`         |

**Criterio de aceptación (pendiente):** actualizar un juego existente devuelve `200` y los
cambios quedan persistidos; un `id` inexistente debería informarse con un `404`.

---

### RF-08 — Baja de juego

| Aspecto        | Detalle                                                        |
| -------------- | -------------------------------------------------------------- |
| Método y ruta  | `DELETE /games/{id}`                                           |
| Respuesta OK   | `200`                                                          |
| Prioridad      | **Alta**                                                       |
| Estado         | ❌ **No implementado** — `GameController.delete_game` no existe |
| Trazabilidad   | `game_routes.py` → `delete()`; `GameRepository.delete()`       |

**Criterio de aceptación (pendiente):** eliminar un juego existente devuelve `200` y el
recurso deja de estar disponible. Las reseñas asociadas deben quedar con `id_game = NULL`
(ver RF-14.2).

---

### RF-09 — Listado paginado de plataformas

| Aspecto        | Detalle                                                                 |
| -------------- | ----------------------------------------------------------------------- |
| Método y ruta  | `GET /platforms/`                                                        |
| Parámetros     | `page` (default `1`, `>= 0`), `limit` (default `10`, `>= 1`)             |
| Respuesta OK   | `200` — `PaginatedPlatformResponse`: `{data: [PlatformResponse], pagination}` |
| Errores        | `422` si `page < 0` o `limit < 1`                                        |
| Prioridad      | **Alta**                                                                 |
| Estado         | ✅ Implementado                                                          |
| Trazabilidad   | `platform_routes.py` → `get_all()`; `PlatformController.get_all_platforms_paginated()`; `PlatformRepository.find_all_paginated()` |

**RF-09.1** Solo se listan plataformas con `url` **no nulo** (`url IS NOT NULL`). Es una regla
de negocio heredada del repositorio.

**RF-09.2** Cada elemento expone `id`, `description` y `url`.

**Criterio de aceptación:** `GET /platforms/` responde `200` con `data` y `pagination`;
`GET /platforms/?limit=0` responde `422`. Verificado por `test_get_platforms`,
`test_get_platforms_paginated_params` y `test_limit_invalido_devuelve_422`.

---

### RF-10 — Consulta de una plataforma por identificador

| Aspecto        | Detalle                                                       |
| -------------- | ------------------------------------------------------------- |
| Método y ruta  | `GET /platforms/{id}`                                         |
| Respuesta OK   | `200` — `PlatformResponse`                                    |
| Errores        | `404` `"Plataforma no encontrada"`                            |
| Prioridad      | **Alta**                                                      |
| Estado         | ✅ Implementado                                               |
| Trazabilidad   | `platform_routes.py` → `get_by_id()`; `PlatformController.get_platform_by_id()`; `PlatformRepository.find_by_id()` |

**Criterio de aceptación:** un `id` existente devuelve `200`; uno inexistente devuelve `404`
con `detail = "Plataforma no encontrada"`.

---

### RF-11 — Alta de plataforma

| Aspecto        | Detalle                                                             |
| -------------- | ------------------------------------------------------------------- |
| Método y ruta  | `POST /platforms/`                                                  |
| Cuerpo         | `PlatformCreate` (JSON)                                             |
| Respuesta OK   | `200` — `PlatformResponse`                                          |
| Prioridad      | **Alta**                                                            |
| Estado         | ❌ **No implementado** — `PlatformController.create_platform` no existe |
| Trazabilidad   | `platform_routes.py` → `create()`; `PlatformRepository.create()`    |

**Criterio de aceptación (pendiente):** `POST /platforms/` con `description` presente responde
`200` con la plataforma creada y su `id`.

---

### RF-12 — Actualización de plataforma

| Aspecto        | Detalle                                                             |
| -------------- | ------------------------------------------------------------------- |
| Método y ruta  | `PUT /platforms/{id}`                                               |
| Cuerpo         | `PlatformCreate` (JSON)                                             |
| Respuesta OK   | `200`                                                               |
| Prioridad      | **Alta**                                                            |
| Estado         | ❌ **No implementado** — `PlatformController.update_platform` no existe |
| Trazabilidad   | `platform_routes.py` → `update()`; `PlatformRepository.update()`    |

**Criterio de aceptación (pendiente):** modificar una plataforma existente devuelve `200` y
persiste los cambios.

---

### RF-13 — Baja de plataforma

| Aspecto        | Detalle                                                             |
| -------------- | ------------------------------------------------------------------- |
| Método y ruta  | `DELETE /platforms/{id}`                                            |
| Respuesta OK   | `200`                                                               |
| Prioridad      | **Alta**                                                            |
| Estado         | ❌ **No implementado** — `PlatformController.delete_platform` no existe |
| Trazabilidad   | `platform_routes.py` → `delete()`; `PlatformRepository.delete()`    |

**Criterio de aceptación (pendiente):** eliminar una plataforma existente devuelve `200` y el
recurso deja de estar disponible.

---

### RF-14 — Consulta de reseñas por juego

| Aspecto        | Detalle                                                                       |
| -------------- | ----------------------------------------------------------------------------- |
| Método y ruta  | `GET /reviews/{id}`                                                           |
| Parámetros     | `id` (path, entero) — identificador del **juego**, no de la reseña             |
| Respuesta OK   | `200` — `list[ReviewResponse]` (lista, no objeto paginado)                     |
| Errores        | `404` `"Reseñas no encontradas para este juego"`                               |
| Prioridad      | **Alta**                                                                       |
| Estado         | ✅ Implementado                                                                |
| Trazabilidad   | `review_routes.py` → `get_by_game_id()`; `ReviewController.get_reviews()`; `ReviewRepository.find_by_game_id()` (`Review.id_game == game_id`) |

**RF-14.1** La respuesta es un **array JSON plano**, sin envoltorio `data`/`pagination`.

**RF-14.2** La relación `review.id_game → games.id` usa `ON DELETE SET NULL` y
`ON UPDATE CASCADE` a nivel de base de datos.

**Criterio de aceptación:** un juego sin reseñas devuelve `404`; uno con reseñas devuelve
`200` con la lista completa. Verificado por `test_get_reviews_not_found`.

---

### RF-15 — Estructura estándar de paginación

| Aspecto        | Detalle                                                             |
| -------------- | ------------------------------------------------------------------- |
| Aplica a       | RF-03, RF-04, RF-09                                                 |
| Estructura     | `{"data": [...], "pagination": {"currentPage", "perPage", "totalRecords", "totalPages"}}` |
| Cálculo        | `totalPages = ceil(totalRecords / perPage)`, con `0` si `totalRecords = 0` |
| Prioridad      | **Alta**                                                            |
| Estado         | ✅ Implementado                                                     |
| Trazabilidad   | `app/utils/pagination.py` → `build_paginated_response()`; `app/schemas/pagination.py` → `PaginationInfo` |

**RF-15.1** `currentPage` refleja el valor solicitado tal cual (si `page=0`, `currentPage` es
`0`).

**RF-15.2** `totalPages` se calcula con aritmética entera `(total + limit - 1) // limit`,
evitando `math.ceil` y el punto flotante.

**RF-15.3** El desplazamiento SQL se calcula como `max(page - 1, 0) * limit`, por lo que
`page = 0` no genera un `OFFSET` negativo.

**Criterio de aceptación:** con `totalRecords = 9` y `perPage = 10`, `totalPages = 1`;
`page=0` es aceptado sin error. Verificado por `test_get_games_page_zero` y
`test_get_platforms_paginated_params`.

---

### RF-16 — Documentación interactiva y esquema OpenAPI

| Aspecto        | Detalle                                                          |
| -------------- | ---------------------------------------------------------------- |
| Rutas          | `/docs` (Swagger UI), `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` |
| Título/versión | `Games API` / `1.0.0`                                            |
| Descripción    | «API para gestión de juegos, plataformas y reseñas»              |
| Prioridad      | **Media**                                                        |
| Estado         | ✅ Implementado (autogenerado por FastAPI)                        |
| Trazabilidad   | `app/main.py` → `FastAPI(...)`                                   |

**Criterio de aceptación:** `/docs` responde `200` y el esquema declara los 7 *paths* del
sistema (`/`, `/games/`, `/games/search`, `/games/{id}`, `/platforms/`, `/platforms/{id}`,
`/reviews/{id}`).

---

### RF-17 — Empaquetado distribuible

| Aspecto        | Detalle                                                    |
| -------------- | ---------------------------------------------------------- |
| Artefacto      | Wheel (`dist/*.whl`) y sdist generados con `python -m build` |
| Nombre/versión | `backend-python` — versión sobrescrita por el pipeline      |
| Prioridad      | **Media**                                                   |
| Estado         | ✅ Implementado                                             |
| Trazabilidad   | `pyproject.toml` (setuptools), `Jenkinsfile` (etapa *Package*) |

**Criterio de aceptación:** `python -m build` produce el wheel sin errores y el pipeline lo
publica en el repositorio PyPI de Nexus.

---

## 4. Requisitos no funcionales

### RNF-01 — Plataforma tecnológica

| Aspecto     | Detalle                                                                     |
| ----------- | --------------------------------------------------------------------------- |
| Prioridad   | **Alta**                                                                    |
| Requisito   | Ejecutar sobre Python **3.14** con las dependencias declaradas: `fastapi >= 0.142.2`, `uvicorn >= 0.54.0`, `sqlalchemy >= 2.1.3`, `aiomysql >= 0.3.2`, `python-dotenv >= 1.2.4`, `cryptography >= 50.0.2`, `pydantic >= 2.13.5` |
| Trazabilidad | `requirements.txt`, `pyproject.toml` (`requires-python = ">=3.14"`), `sonar-project.properties` |

### RNF-02 — Arquitectura en capas

| Aspecto     | Detalle                                                                      |
| ----------- | ---------------------------------------------------------------------------- |
| Prioridad   | **Alta**                                                                     |
| Requisito   | Toda funcionalidad debe respetar el flujo `schema → model → repository → service → controller → route`. El SQL reside **exclusivamente** en `app/repositories/`; ni controllers ni services acceden a la sesión de base de datos. |
| Trazabilidad | Estructura de `app/`; factorías `get_controller()` en cada módulo de rutas    |

### RNF-03 — Ejecución asíncrona

| Aspecto     | Detalle                                                                        |
| ----------- | ------------------------------------------------------------------------------ |
| Prioridad   | **Alta**                                                                       |
| Requisito   | Repositorios, servicios, controladores y endpoints son `async`; no se introduce I/O bloqueante en la ruta de petición. El motor usa `mysql+aiomysql`. |
| Trazabilidad | `app/database.py`; firmas `async def` en todas las capas                        |

### RNF-04 — Rendimiento y eficiencia de consultas

| Aspecto     | Detalle                                                                         |
| ----------- | ------------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                        |
| Requisito   | El listado de juegos (RF-03) selecciona solo las columnas expuestas; los conteos usan `COUNT(*)` con `select_from`; el pool de conexiones se configura con `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True` y `pool_recycle=3600`; no se ejecuta `refresh()` tras `commit()`. |
| Trazabilidad | `app/repositories/game_repo.py`, `app/repositories/platform_repo.py`, `app/database.py` |

### RNF-05 — Seguridad

| Aspecto     | Detalle                                                                          |
| ----------- | -------------------------------------------------------------------------------- |
| Prioridad   | **Alta**                                                                          |
| Requisito   | (a) Los endpoints son públicos: **no existe autenticación ni autorización**. (b) Las credenciales de base de datos nunca deben versionarse en el repositorio. (c) El contenedor se ejecuta con un **usuario no root** (`appuser`). |
| Trazabilidad | `app/main.py` (sin middleware de seguridad); `.gitignore`/`.dockerignore`; `Dockerfile` (`USER appuser`) |

> **Riesgo identificado:** el `Dockerfile` copia el archivo `.env` dentro de la imagen, por lo
> que las credenciales quedan embebidas en ella. Se recomienda inyectarlas en tiempo de
> ejecución (`docker run --env-file .env ...`).

### RNF-06 — Observabilidad

| Aspecto     | Detalle                                                                    |
| ----------- | -------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                   |
| Requisito   | El contenedor debe emitir logs sin *buffering* (`PYTHONUNBUFFERED=1`) y exponer un `HEALTHCHECK` contra `GET /`. No existe logging centralizado ni *middleware* de correlación. |
| Trazabilidad | `Dockerfile` (`ENV`, `HEALTHCHECK`)                                        |

### RNF-07 — Mantenibilidad y estilo

| Aspecto     | Detalle                                                                     |
| ----------- | --------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                    |
| Requisito   | Imports absolutos con prefijo `app.`; tipado con sintaxis moderna (`X \| None`, `list[...]`, `Annotated[...]`); schemas Pydantic v2 con `model_config = ConfigDict(...)`; docstrings y mensajes en **español**. |
| Trazabilidad | Todo `app/`; `DEEPSEEK.md` §11                                               |

### RNF-08 — Pruebas automatizadas

| Aspecto     | Detalle                                                                          |
| ----------- | -------------------------------------------------------------------------------- |
| Prioridad   | **Alta**                                                                          |
| Requisito   | La suite debe ejecutarse con `pytest` (modo `asyncio_mode = auto`) usando **SQLite en memoria** (`sqlite+aiosqlite:///:memory:` con `StaticPool`) y sobreescribiendo la dependencia `get_db`. Debe generar cobertura en `coverage.xml`. |
| Trazabilidad | `tests/test_api.py`, `pytest.ini`, `Jenkinsfile`                                  |

### RNF-09 — Portabilidad y despliegue

| Aspecto     | Detalle                                                                         |
| ----------- | ------------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                        |
| Requisito   | La aplicación debe contenerizarse mediante un `Dockerfile` *multi-stage* sobre `python:3.14-slim`, exponer el puerto `8000` y arrancar con `uvicorn app.main:app --host 0.0.0.0 --port 8000`. El contexto de build es la raíz del proyecto. |
| Trazabilidad | `Dockerfile`                                                                     |

### RNF-10 — Integración continua y calidad

| Aspecto     | Detalle                                                                          |
| ----------- | -------------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                          |
| Requisito   | Un pipeline declarativo (Jenkins) debe ejecutar: instalación limpia en `venv`, pruebas con cobertura, análisis con `sonar-scanner` (SonarQube en `http://172.17.0.1:9000`), construcción del wheel y publicación con `twine` en Nexus. |
| Trazabilidad | `Jenkinsfile`, `sonar-project.properties`                                          |

### RNF-11 — Compatibilidad de datos

| Aspecto     | Detalle                                                                       |
| ----------- | ----------------------------------------------------------------------------- |
| Prioridad   | **Media**                                                                      |
| Requisito   | El esquema debe ser compatible con MySQL/MariaDB; los identificadores que no son válidos en Python (`3djuegos_url`, `3djuegos_score`) se mapean mediante alias. |
| Trazabilidad | `app/models/game.py`, `app/schemas/game_schema.py`                              |

---

### RNF-12 — Configuración por variables de entorno

| Aspecto      | Detalle                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------- |
| Prioridad    | **Alta**                                                                                     |
| Requisito    | La conexión se construye desde variables de entorno, cargadas con `python-dotenv` desde `.env`. URL resultante: `mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}`. |
| Trazabilidad | `app/database.py`                                                                            |

| Variable      | Valor por defecto | Descripción                    |
| ------------- | ----------------- | ------------------------------ |
| `DB_USER`     | `admin`           | Usuario de la base de datos     |
| `DB_PASSWORD` | `password`        | Contraseña de la base de datos  |
| `DB_HOST`     | `192.168.1.82`    | Host de MySQL/MariaDB           |
| `DB_NAME`     | `game`            | Nombre del esquema              |

**RNF-12.1** Las sesiones se crean con `async_sessionmaker` y `expire_on_commit=False`; la
dependencia `get_db()` garantiza el cierre de la sesión tras cada petición.

> **Inconsistencia detectada:** `DEEPSEEK.md` documenta
> `DB_HOST = 192.168.1.13`, mientras que el código usa `192.168.1.82`. **Prevalece el código.**

---

## 5. Modelo de datos

### 5.1 Tabla `games` (clase `Game`)

| Columna            | Tipo           | Nulable | Notas                                   |
| ------------------ | -------------- | ------- | --------------------------------------- |
| `id`               | Integer        | No      | PK, autoincremental                      |
| `title`            | String(200)    | No      | **Indexado**                             |
| `description`      | Text           | No      |                                          |
| `GameDBId`         | Integer        | Sí      |                                          |
| `image_Large`      | String(255)    | Sí      |                                          |
| `image_Medium`     | String(255)    | Sí      |                                          |
| `image_Original`   | String(255)    | Sí      |                                          |
| `image_Front`      | String(255)    | Sí      |                                          |
| `Platform`         | String(200)    | Sí      | **Indexado**; usado como filtro          |
| `Publisher`        | String(300)    | Sí      |                                          |
| `releasedate`      | String(12)     | Sí      |                                          |
| `players`          | String(10)     | Sí      |                                          |
| `genre`            | String(100)    | Sí      |                                          |
| `youtube_Trailer`  | String(255)    | Sí      |                                          |
| `youtube_Walk`     | String(255)    | Sí      |                                          |
| `wiki_url`         | String(500)    | Sí      |                                          |
| `wiki_page`        | Text           | Sí      |                                          |
| `youtube_ending`   | String(255)    | Sí      |                                          |
| `youtube_secrets`  | String(255)    | Sí      |                                          |
| `youtube_ost`      | String(255)    | Sí      |                                          |
| `youtube_speedrun` | String(200)    | Sí      |                                          |
| `youtube_review`   | String(200)    | Sí      |                                          |
| `spotify_ost`      | String(200)    | Sí      |                                          |
| `ign_url`          | String(200)    | Sí      |                                          |
| `metacritic_url`   | String(200)    | Sí      |                                          |
| `metacritic_score` | String(30)     | Sí      |                                          |
| `metacritic_scoreu`| String(30)     | Sí      |                                          |
| `3djuegos_url`     | String(200)    | Sí      | Alias ORM: `three_d_juegos_url`          |
| `areajugones_url`  | String(200)    | Sí      |                                          |
| `meristation_url`  | String(200)    | Sí      |                                          |
| `3djuegos_score`   | String(30)     | Sí      | Alias ORM: `three_d_juegos_score`        |
| `opencritic_url`   | String(200)    | Sí      |                                          |
| `esrb_letter`      | String(5)      | Sí      |                                          |
| `esbr_message`     | String(50)     | Sí      | (nombre heredado, con la errata `esbr`)  |

### 5.2 Tabla `platform` (clase `Platform`)

| Columna       | Tipo        | Nulable | Notas |
| ------------- | ----------- | ------- | ----- |
| `id`          | Integer     | No      | PK, autoincremental |
| `description` | String(100) | No      |       |
| `url`         | String(100) | Sí      | Solo se listan registros con `url` no nulo (RF-09.1) |

### 5.3 Tabla `review` (clase `Review`)

| Columna   | Tipo        | Nulable | Notas                                                    |
| --------- | ----------- | ------- | -------------------------------------------------------- |
| `id`      | Integer     | No      | PK, autoincremental                                       |
| `name`    | String(200) | Sí      |                                                          |
| `date`    | String(30)  | Sí      |                                                          |
| `review`  | Text        | No      |                                                          |
| `score`   | String(8)   | Sí      |                                                          |
| `source`  | String(100) | No      |                                                          |
| `id_game` | Integer     | Sí      | FK → `games.id`, `ON DELETE SET NULL`, `ON UPDATE CASCADE` |

### 5.4 Integridad y relaciones

- **RF-14.2:** al eliminar un juego, las reseñas asociadas conservan la fila con `id_game = NULL`.
- **No hay `relationship` ORM** declaradas: la navegación entre entidades se hace por consultas
  explícitas.
- No existen migraciones versionadas (Alembic u otro); el esquema se genera con `Base.metadata`.

---

## 6. Contratos de la API

### 6.1 Esquemas Pydantic

| Esquema                        | Uso                     | Campos requeridos                            |
| ------------------------------ | ----------------------- | -------------------------------------------- |
| `GameBase` / `GameCreate`      | Entrada (RF-06, RF-07)  | `title`, `description` (resto opcional)      |
| `GameResponse`                 | Salida (RF-04, RF-05)   | `GameBase` + `id`                            |
| `GameSummary`                  | Salida (RF-03)          | `id`, `title`, `platform`                    |
| `PaginatedGameResponse`        | Envoltorio (RF-04)      | `data: [GameResponse]`, `pagination`         |
| `PaginatedGameSummaryResponse` | Envoltorio (RF-03)      | `data: [GameSummary]`, `pagination`          |
| `PlatformCreate`               | Entrada (RF-11, RF-12)  | `description` (`url` opcional)               |
| `PlatformResponse`             | Salida (RF-09, RF-10)   | `PlatformCreate` + `id`                      |
| `PaginatedPlatformResponse`    | Envoltorio (RF-09)      | `data: [PlatformResponse]`, `pagination`     |
| `ReviewResponse`               | Salida (RF-14)          | `review`, `source`, `id` (resto opcional)    |
| `PaginationInfo`               | Envoltorio (RF-15)      | `currentPage`, `perPage`, `totalRecords`, `totalPages` |

### 6.2 Ejemplo de respuesta paginada resumida (RF-03)

```json
{
  "data": [
    { "id": 16489, "title": "The Witcher 3: Wild Hunt", "platform": "Sony Playstation 4" }
  ],
  "pagination": { "currentPage": 1, "perPage": 10, "totalRecords": 1, "totalPages": 1 }
}
```

### 6.3 Ejemplo de respuesta de reseñas (RF-14)

```json
[
  {
    "name": "Nintendo Power",
    "date": "",
    "review": "A perfect primer for the rest of the Metroid series.",
    "score": "84",
    "source": "Metacritic",
    "id_game": 123,
    "id": 3671
  }
]
```

---

## 7. Trazabilidad requisito ↔ prueba

| Requisito | Prueba automatizada                              | Estado |
| --------- | ------------------------------------------------ | ------ |
| RF-03     | `test_get_games_by_platform_campos_resumidos`     | ✅     |
| RF-03     | `test_get_games_page_zero`                        | ✅     |
| RF-04     | `test_search_game_by_title`                       | ✅     |
| RF-09     | `test_get_platforms`                              | ✅     |
| RF-09     | `test_get_platforms_paginated_params`             | ✅     |
| RF-15     | `test_limit_invalido_devuelve_422`                | ✅     |
| RF-14     | `test_get_reviews_not_found`                      | ✅     |
| RF-05     | *(sin prueba dedicada)*                           | ⚠️     |
| RF-06/07/08, RF-11/12/13 | *(sin prueba — funcionalidad no implementada)* | ❌ |

**Cobertura de pruebas:** 7 pruebas en `tests/test_api.py`, todas con SQLite en memoria y
sobreescritura de `get_db`.

---

## 8. Requisitos pendientes y deuda técnica

| ID    | Descripción                                                                                     | Prioridad | Impacto |
| ----- | ----------------------------------------------------------------------------------------------- | --------- | ------- |
| P-01  | Implementar `create_game`, `update_game` y `delete_game` en `GameController` (RF-06/07/08)       | **Alta**  | Endpoints en `500` |
| P-02  | Implementar `create_platform`, `update_platform` y `delete_platform` en `PlatformController` (RF-11/12/13) | **Alta** | Endpoints en `500` |
| P-03  | Implementar CRUD de reseñas (hoy solo lectura)                                                  | Media     | Funcionalidad ausente |
| P-04  | Corregir RF-03.4: el listado sin `platform` devuelve solo juegos con `Platform IS NULL`         | **Alta**  | Resultado incorrecto |
| P-05  | Añadir autenticación/autorización (todos los endpoints son públicos)                            | Media     | Riesgo de seguridad |
| P-06  | No embeber el `.env` en la imagen Docker; inyectar credenciales en runtime                      | **Alta**  | Riesgo de seguridad |
| P-07  | Definir un orden determinista (`ORDER BY`) en los listados paginados                            | Media     | Paginación inestable |
| P-08  | Centralizar el manejo de errores y el logging                                                   | Media     | Observabilidad |
| P-09  | Endurecer la validación de esquemas (longitudes, formatos de URL/fecha)                          | Baja      | Calidad de datos |
| P-10  | Declarar relaciones ORM (`relationship`) entre `Game`, `Platform` y `Review`                    | Baja      | Ergonomía del código |
| P-11  | Migrar el cliente de pruebas a `httpx2` para eliminar el aviso de deprecación de Starlette      | Baja      | Ruido en pruebas |
| P-12  | Añadir migraciones versionadas (Alembic) para el esquema de base de datos                        | Media     | Evolución del esquema |

---

## 9. Glosario

| Término              | Definición                                                                       |
| -------------------- | -------------------------------------------------------------------------------- |
| `currentPage`        | Página solicitada por el cliente; se refleja tal cual (puede ser `0`).           |
| `perPage`            | Tamaño de página (`limit`).                                                       |
| `totalRecords`       | Total de registros que cumplen el filtro.                                        |
| `totalPages`         | `ceil(totalRecords / perPage)`; `0` si no hay registros.                          |
| Prefijo              | Coincidencia `LIKE 'texto%'` sobre el título.                                     |
| Healthcheck          | Comprobación periódica de disponibilidad definida en el `Dockerfile`.            |

---

*Documento derivado del código fuente del repositorio `backend-python`. Ante cualquier
discrepancia con el código, prevalece el código.*
