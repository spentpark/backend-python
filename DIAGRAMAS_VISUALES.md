# Diagramas Visuales - Diseño del Proyecto

Este documento consolida todos los diagramas generados en formato visual para referencia rápida.

---

## 1️⃣ Diagrama de Capas de Arquitectura

**Descripción:** Muestra la estructura de capas jerárquica del sistema, desde el cliente HTTP hasta la base de datos.

- **Capa API & Routing:** Endpoints FastAPI
- **Capa Controllers:** Orquestación de solicitudes
- **Capa Business Logic:** Lógica de negocio y transformaciones
- **Capa Persistencia:** Acceso a datos (Repositories)
- **ORM Async:** SQLAlchemy para operaciones asincrónicas
- **Base de Datos:** MySQL/MariaDB

```mermaid
graph LR
    Client["🌐 Cliente"]
    
    subgraph API["Capa API & Routing"]
        R1["GET /games"]
        R2["POST /games"]
        R3["GET /platforms"]
        R4["GET /reviews/{id}"]
    end
    
    subgraph Controller["Capa de Controllers"]
        GC["GameController"]
        PC["PlatformController"]
        RC["ReviewController"]
    end
    
    subgraph Service["Capa de Business Logic"]
        GS["GameService"]
        PS["PlatformService"]
        RS["ReviewService"]
    end
    
    subgraph Repository["Capa de Persistencia"]
        GR["GameRepository"]
        PR["PlatformRepository"]
        RR["ReviewRepository"]
    end
    
    subgraph ORM["ORM Async"]
        SA["SQLAlchemy<br/>AsyncSession"]
    end
    
    subgraph DB["Base de Datos"]
        DB1["🗄️ MySQL/MariaDB"]
    end
    
    Client -->|HTTP| API
    R1 --> GC
    R2 --> GC
    R3 --> PC
    R4 --> RC
    
    GC --> GS
    PC --> PS
    RC --> RS
    
    GS --> GR
    PS --> PR
    RS --> RR
    
    GR --> SA
    PR --> SA
    RR --> SA
    
    SA --> DB1
    
    style API fill:#e3f2fd
    style Controller fill:#f3e5f5
    style Service fill:#e8f5e9
    style Repository fill:#fff3e0
    style ORM fill:#fce4ec
    style DB fill:#ffe0b2
```

---

## 2️⃣ Diagrama de Clases UML

**Descripción:** Estructura estática de todas las clases del sistema y sus dependencias.

```mermaid
classDiagram
    direction LR

    class GameController {
        +get_all_games()
        +get_game_by_id(id)
        +search_by_title(title,page,limit)
        +filter_by_platform(platform,page,limit)
    }
    class PlatformController {
        +get_all_platforms()
        +get_platform_by_id(id)
    }
    class ReviewController {
        +get_reviews(game_id)
    }

    class GameService {
        +get_all()
        +get_by_id(id)
        +get_by_title(title,page,limit)
        +get_by_platform(platform,page,limit)
    }
    class PlatformService {
        +get_all()
        +get_by_id(id)
    }
    class ReviewService {
        +get_reviews_by_game(game_id)
    }

    class GameRepository {
        +find_all()
        +find_by_id(id)
        +create(data)
        +update(id,data)
        +delete(id)
        +find_by_title_paginated(title,page,limit)
        +find_by_platform_paginated(platform,page,limit)
    }
    class PlatformRepository {
        +find_all()
        +find_by_id(id)
        +create(data)
        +update(id,data)
        +delete(id)
    }
    class ReviewRepository {
        +find_by_game_id(game_id)
    }

    class Game {
        +id
        +title
        +description
        +Platform
        +...otros campos...
    }
    class Platform {
        +id
        +description
        +url
    }
    class Review {
        +id
        +name
        +date
        +review
        +score
        +source
        +id_game
    }

    GameController --> GameService
    PlatformController --> PlatformService
    ReviewController --> ReviewService

    GameService --> GameRepository
    PlatformService --> PlatformRepository
    ReviewService --> ReviewRepository

    GameRepository --> Game
    PlatformRepository --> Platform
    ReviewRepository --> Review
```

---

## 3️⃣ Diagrama de Secuencia - GET /games/{id}

**Descripción:** Flujo de ejecución paso a paso para una solicitud GET de un juego por ID.

```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as Route (/games/{id})
    participant Ctrl as GameController
    participant S as GameService
    participant Repo as GameRepository
    participant DB as Base de Datos

    C->>R: GET /games/123
    R->>Ctrl: ctrl.get_game_by_id(123)
    Ctrl->>S: service.get_by_id(123)
    S->>Repo: repo.find_by_id(123)
    Repo->>DB: SELECT * FROM games WHERE id=123
    DB-->>Repo: registro (o none)
    Repo-->>S: registro
    S-->>Ctrl: registro
    Ctrl-->>R: registro (o 404)
    R-->>C: 200 OK + JSON
```

---

## 4️⃣ Diagrama Entidad-Relación (ER)

**Descripción:** Modelo de datos relacional de la base de datos MySQL/MariaDB con todas las tablas y sus campos.

```mermaid
erDiagram
    GAMES ||--o{ REVIEW : "tiene"
    
    GAMES {
        int id PK
        string title
        text description
        int GameDBId
        string image_Large
        string image_Medium
        string image_Original
        string image_Front
        string Platform
        string Publisher
        string releasedate
        string players
        string genre
        string youtube_Trailer
        string youtube_Walk
        string wiki_url
        text wiki_page
        string youtube_ending
        string youtube_secrets
        string youtube_ost
        string youtube_speedrun
        string youtube_review
        string spotify_ost
        string ign_url
        string metacritic_url
        string metacritic_score
        string metacritic_scoreu
        string "3djuegos_url"
        string areajugones_url
        string meristation_url
        string "3djuegos_score"
        string opencritic_url
        string esrb_letter
        string esbr_message
    }

    PLATFORM {
        int id PK
        string description
        string url
    }

    REVIEW {
        int id PK
        string name
        string date
        text review
        string score
        string source
        int id_game FK
    }
```

---

## 5️⃣ Diagrama de Flujo HTTP

**Descripción:** Camino completo de una solicitud HTTP desde el cliente hasta la respuesta, mostrando cada capa involucrada.

```mermaid
graph TD
    A["Cliente HTTP"]
    B["FastAPI Router"]
    C["Dependencia: get_db()"]
    D["Dependencia: get_controller()"]
    E["GameController<br/>PlatformController<br/>ReviewController"]
    F["GameService<br/>PlatformService<br/>ReviewService"]
    G["GameRepository<br/>PlatformRepository<br/>ReviewRepository"]
    H["SQLAlchemy Async"]
    I["MySQL/MariaDB"]
    J["Respuesta JSON<br/>Pydantic Schema"]
    
    A -->|Request| B
    B -->|Resolve| C
    B -->|Resolve| D
    C -->|Inyecta Session| D
    D -->|Inyecta Controller| E
    E -->|Lógica negocio| F
    F -->|Consultas| G
    G -->|SQL| H
    H -->|Query| I
    I -->|Resultados| H
    H -->|ORM| G
    G -->|Datos| F
    F -->|Formato| E
    E -->|Serializa| J
    J -->|Response| A
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#e8f5e9
    style G fill:#fce4ec
    style I fill:#ffe0b2
```

---

## 6️⃣ Pipeline CI/CD de Jenkins

**Descripción:** Flujo completo desde un commit en Git hasta la publicación del artefacto en Nexus.

```mermaid
graph TD
    A["📝 Git Commit<br/>a main/dev"]
    B["🏃 Trigger Jenkins<br/>Pipeline"]
    C["🧹 Stage: Clean Install<br/>venv + pip install"]
    D["✅ Stage: Test & Sonar<br/>pytest + coverage<br/>sonar-scanner"]
    E["📦 Stage: Package<br/>python3 -m build<br/>Wheel file"]
    F["🔼 Stage: Publish Nexus<br/>twine upload<br/>PyPI Repository"]
    G["✨ Artefacto creado<br/>en Nexus"]
    H["🐳 Build Docker<br/>con Wheel"]
    I["🚀 Deploy a<br/>Producción"]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    
    style A fill:#bbf7d0
    style B fill:#c7d2fe
    style C fill:#fecaca
    style D fill:#fca5a5
    style E fill:#fbbf24
    style F fill:#a78bfa
    style G fill:#7dd3fc
    style H fill:#34d399
    style I fill:#10b981
```

---

## 7️⃣ Etapas Detalladas del Pipeline

**Descripción:** Desglose de cada etapa con los comandos ejecutados y condiciones de éxito/fallo.

```mermaid
graph TB
    A["1️⃣ Clean Install"]
    B["2️⃣ Test & Sonar"]
    C["3️⃣ Package"]
    D["4️⃣ Publish"]
    
    A -->|Success| B
    B -->|Tests Pass<br/>Sonar OK| C
    B -->|Tests Fail| E["❌ Pipeline Aborted<br/>Notification sent"]
    C -->|Build Success| D
    C -->|Package Error| E
    D -->|Published| F["✅ Ready for Deploy<br/>Artifact in Nexus"]
    
    A --> A1["rm -rf venv<br/>python3 -m venv<br/>pip install -r requirements.txt<br/>pip install pytest pytest-cov"]
    
    B --> B1["pytest --cov=app<br/>coverage.xml"]
    B --> B2["sonar-scanner<br/>-Dsonar.projectKey=backend-python<br/>-Dsonar.sources=app<br/>-Dsonar.tests=tests"]
    
    C --> C1["python3 -m build<br/>dist/ = Wheel"]
    
    D --> D1["twine upload<br/>--repository-url Nexus<br/>credentials from Jenkins"]
    
    style A fill:#ffe0b2
    style B fill:#ffccbc
    style C fill:#ffab91
    style D fill:#ff8a65
    style F fill:#4db6ac
    style E fill:#ef5350
```

---

## 8️⃣ Dockerfile Multi-Stage Build

**Descripción:** Proceso de construcción de la imagen Docker en dos etapas (Builder y Final) para optimizar tamaño.

```mermaid
graph TD
    A["python:3.13-slim"] --> B["STAGE 1: BUILDER"]
    
    B --> C["Instalar<br/>gcc, python3-dev<br/>libmariadb-dev"]
    C --> D["COPY requirements.txt"]
    D --> E["pip install --prefix<br/>en /install"]
    E --> F["/install/<br/>site-packages"]
    
    F --> G["COPY /install<br/>al STAGE 2"]
    
    H["python:3.13-slim"] --> I["STAGE 2: FINAL"]
    
    I --> J["Instalar runtime<br/>libmariadb3"]
    J --> K["COPY /install<br/>from builder"]
    K --> L["COPY app/"]
    L --> M["COPY .env"]
    M --> N["adduser appuser<br/>chown /app"]
    N --> O["EXPOSE 8000"]
    O --> P["CMD: uvicorn<br/>app.main:app<br/>host=0.0.0.0<br/>port=8000"]
    
    P --> Q["🐳 Docker Image<br/>Final"]
    
    style B fill:#fecaca
    style I fill:#bbf7d0
    style Q fill:#34d399
```

---

## 9️⃣ Infraestructura CI/CD Completa

**Descripción:** Ecosistema completo de herramientas: Jenkins, SonarQube, Nexus, Docker y ambiente de despliegue.

```mermaid
graph LR
    A["📚 Git Repository"]
    
    subgraph Jenkins["🔨 Jenkins CI/CD<br/>server"]
        B["Pipeline<br/>Executor"]
        C["Clean Install<br/>+ Venv"]
        D["Test Runner<br/>pytest"]
        E["Sonar Client"]
    end
    
    subgraph Quality["📊 Quality Gates"]
        F["SonarQube<br/>172.17.0.1:9000"]
        G["Coverage Report<br/>coverage.xml"]
    end
    
    subgraph Build["🏗️ Build & Package"]
        H["python -m build<br/>Wheel package"]
        I["twine upload"]
    end
    
    subgraph Registry["📦 Nexus 3<br/>172.17.0.1:8081"]
        J["PyPI Repository<br/>python-nexus-repo"]
    end
    
    subgraph Container["🐳 Container"]
        K["Docker Build<br/>Multi-stage"]
        L["Python:3.13-slim<br/>+ dependencies"]
    end
    
    subgraph Deploy["🚀 Deployment"]
        M["Docker Registry<br/>or Host"]
        N["Production/Test<br/>Environment"]
    end
    
    A -->|Webhook| Jenkins
    B --> C
    C --> D
    D --> E
    E --> F
    D --> G
    F -->|Pass/Fail| Build
    Build --> H
    H --> I
    I --> Registry
    Registry --> J
    J --> Container
    Container --> K
    K --> L
    L --> Deploy
    Deploy --> M
    M --> N
    
    style Jenkins fill:#fff3cd
    style Quality fill:#f8d7da
    style Build fill:#d4edda
    style Registry fill:#cfe2ff
    style Container fill:#e7d4f5
    style Deploy fill:#d1ecf1
```

---

## 📊 Resumen de Componentes

| Componente | Responsabilidad |
|---|---|
| **FastAPI Router** | Mapeo de rutas HTTP y resolución de dependencias |
| **Controller** | Validación inicial y orquestación de servicios |
| **Service** | Lógica de negocio, transformaciones, paginación |
| **Repository** | Acceso a datos con SQLAlchemy Async |
| **Models (ORM)** | Mapeo de tablas de BD a objetos Python |
| **Schemas (Pydantic)** | Validación y serialización JSON |
| **Database** | Configuración de conexión y sesiones MySQL |

---

## 🔄 Patrones de diseño implementados

- **Dependency Injection:** FastAPI `Depends()` para inyectar controladores, servicios y sesiones.
- **Repository Pattern:** Abstracción de acceso a datos.
- **Service Layer:** Separación de lógica de negocio.
- **Async/Await:** Operaciones no bloqueantes con SQLAlchemy Async.
- **Schema Validation:** Pydantic para validar entrada/salida.

---

## 📋 Consideraciones finales

Estos diagramas representan el estado actual de la arquitectura. Para exportarlos a formatos de imagen (PNG, SVG, PDF), se recomienda usar herramientas como:
- **mermaid-cli:** `mmdc -i diagrama.mmd -o diagrama.png`
- **draw.io:** Importar diagrama Mermaid y exportar.
- **Editores online:** mermaid.live, excalidraw.com

