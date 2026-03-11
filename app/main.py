from fastapi import FastAPI
from routes.platform_routes import router as platform_router
from routes.game_routes import router as game_router
from routes.review_routes import router as review_router

app = FastAPI()

app.include_router(platform_router)
app.include_router(game_router)
app.include_router(review_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)