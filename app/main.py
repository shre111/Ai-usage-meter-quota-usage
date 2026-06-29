from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import generation, usage, users
from app.config import get_settings
from app.db import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(users.router)
    app.include_router(generation.router)
    app.include_router(usage.router)
    app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
    return app


app = create_app()
