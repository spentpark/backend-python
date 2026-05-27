# Documento de Requerimientos

## 📌 Visión general
Esta API REST construida con **FastAPI** provee operaciones para gestionar **juegos**, **plataformas** y **reseñas**. Utiliza **SQLAlchemy (AsyncIO)** para persistencia en una base de datos **MySQL/MariaDB**.

---

## 🧩 Entidades principales

### 🎮 Juego (`Game`)
- Almacena información de juegos (título, descripción, plataforma, fecha de lanzamiento, imágenes, enlaces a reseñas, puntajes, etc).
- Tabla en base de datos: `games`.

#### Atributos relevantes
- `id` (PK)
- `title`, `description`
- `Platform` (nombre de la plataforma)
- `GameDBId`, `releasedate`, `genre`, `publisher`
- URLs relacionadas: `youtube_*`, `wiki_*`, `metacritic_*`, `3djuegos_*`, etc.

### 🕹 Plataforma (`Platform`)
- Lista de plataformas con descripción y URL asociada.
- Tabla: `platform`

#### Atributos
- `id` (PK)
- `description` (texto obligatorio)
- `url` (opcional)

### ⭐ Reseña (`Review`)
- Reseñas asociadas a un juego.
- Tabla: `review`

#### Atributos
- `id` (PK)
- `name`, `date`, `score`, `source`
- `review` (texto obligatorio)
- `id_game` (FK a `games.id`)

---

## 🚀 Endpoints (Funcionalidades expuestas)

### 🏠 Root
- `GET /` → Mensaje de bienvenida con referencia a `/docs`.
- `GET /favicon.ico` → Devuelve 204 para evitar logs de error por favicon.

### 🎮 Juegos (Games)
- `GET /games` → Lista de juegos paginada (por plataforma opcional):
  - Query params: `platform` (filtro opcional), `page` (default 1), `limit` (default 10)
  - Respuesta: objeto con `data` (lista de juegos) y `pagination` (info de paginación)

- `GET /games/{id}` → Obtiene un juego por su ID.
  - Retorna 404 si no existe.

- `GET /games/search` → Busca juegos por título (prefijo) con paginación:
  - Query params: `title` (requerido), `page`, `limit`
  - Retorna 400 si falta `title`

- `POST /games` → Crea un nuevo juego
  - Requiere payload JSON según `GameCreate`.
  - Responde 201 con el juego creado.

- `PUT /games/{id}` → Actualiza un juego existente (todos los campos descritos en `GameCreate`)

- `DELETE /games/{id}` → Elimina un juego por ID.

### 🕹 Plataformas (Platforms)
- `GET /platforms` → Lista todas las plataformas (filtro: `url IS NOT NULL` en la consulta).
- `GET /platforms/{id}` → Obtiene plataforma por ID (404 si no existe).
- `POST /platforms` → Crea plataforma.
- `PUT /platforms/{id}` → Modifica plataforma.
- `DELETE /platforms/{id}` → Elimina plataforma.

### ⭐ Reseñas (Reviews)
- `GET /reviews/{id}` → Obtiene todas las reseñas del juego con ID `id`.
  - Responde 404 si no hay reseñas para ese juego.

---

## ⚙️ Infraestructura y configuración

### Base de datos
- Conexión almacenada en `app/database.py`.
- Variables de entorno usadas (pueden definirse en `.env`):
  - `DB_USER` (default: `admin`)
  - `DB_PASSWORD` (default: `password`)
  - `DB_HOST` (default: `192.168.1.13`)
  - `DB_NAME` (default: `game`)

### ORM y sesiones
- SQLAlchemy Async (`AsyncSession`) con `mysql+aiomysql`.
- Dependencia `get_db()` usada para inyectar sesiones en controladores.

---

## ✅ Validaciones y comportamiento esperado

- 404 en recursos no encontrados (`Game`, `Platform`, reseñas vacías).
- 400 cuando `title` no es provisto en `GET /games/search`.
- Paginación con cálculo de `totalPages` basado en `totalRecords` y `limit`.

---

## 📌 Áreas no implementadas en el código actual (para futuros requerimientos)

- Autenticación / autorización (no hay JWT ni roles).
- Control de acceso (todos los endpoints son públicos).
- Validación adicional (por ejemplo, esquema de entrada más estricto, longitudes mínimas/máximas).
- Endpoints para crear/editar/eliminar reseñas (solo lectura implementada).
- Relaciones entre entidades (ORM no define `relationship`).
- Manejo de errores genéricos o logging centralizado.

---

## 🧪 Pruebas
- Existe un archivo de pruebas en `tests/test_api.py`.

---

*Este documento se generó a partir de la estructura de código existente y refleja las rutas y comportamientos implementados en el proyecto.*
