from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import load_config
from backend.db import init_db, set_db_path, close_db
from backend.routers import maps, nodes, auth, teams
from backend.ws import handler as ws_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config("config.yaml")
    os.makedirs(os.path.dirname(config.database) or ".", exist_ok=True)
    set_db_path(config.database)
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title="MindMap", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(maps.router)
    app.include_router(nodes.router)
    app.include_router(teams.router)
    app.include_router(ws_handler.router)

    # Serve frontend build if it exists
    dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    return app
