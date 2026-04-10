import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.config import get_settings
from backend.api.qt_bridge import start_qt_thread
from backend.api.routers import (
    analysis,
    arduino,
    auth,
    camera,
    experiment,
    notifications,
    presets,
    recordings,
    settings as settings_router,
)
from backend.api.routers.admin_users import recovery_router, router as users_router
from database.db import init_db

logger = logging.getLogger("zimon.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized for API")
    try:
        start_qt_thread()
        logger.info("Qt camera thread started")
    except Exception as e:
        logger.exception("Qt camera thread failed to start: %s", e)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(recovery_router, prefix="/api")
    app.include_router(presets.router, prefix="/api")
    app.include_router(arduino.router, prefix="/api")
    app.include_router(camera.router, prefix="/api")
    app.include_router(experiment.router, prefix="/api")
    app.include_router(recordings.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    app.include_router(settings_router.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
