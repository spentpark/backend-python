from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routes.platform_routes import router as platform_router
from app.routes.game_routes import router as game_router
from app.routes.review_routes import router as review_router

app = FastAPI(
    title="Games API",
    description="API para gestión de juegos, plataformas y reseñas",
    version="1.0.0"
)

# --- CORS: el SPA (Vite en 5173, `vite preview` en 4173 y Nginx en 8065)
# consume la API desde otro origen, así que el navegador exige estas cabeceras ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8065",
        "http://127.0.0.1:8065",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ruta para evitar el error 404 del favicon en los logs ---
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# --- Inclusión de Routers ---
app.include_router(platform_router)
app.include_router(game_router)
app.include_router(review_router)

# --- Ruta de bienvenida/salud ---
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Bienvenido a la Games API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    # Nota: Cuando usas reload=True, debes pasar el string "app.main:app"
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)