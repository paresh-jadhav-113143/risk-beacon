from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, auth, suppliers, system
from app.config.settings import settings
from app.db.schema import initialize_database


def create_app() -> FastAPI:
    app = FastAPI(title="Risk Beacon API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(suppliers.router)

    @app.on_event("startup")
    def startup() -> None:
        initialize_database()

    return app


app = create_app()
