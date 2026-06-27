from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import users
from app.config import get_settings
from app.db import init_db


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
    return app


app = create_app()
