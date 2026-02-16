from __future__ import annotations

import os

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    port: int = 8080
    database: str = "./data/mindmap.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "CHANGE-ME-IN-PRODUCTION"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30


def load_config(path: str = "config.yaml") -> AppConfig:
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}

    # Environment variables override config file
    if os.environ.get("MINDMAP_PORT"):
        data["port"] = int(os.environ["MINDMAP_PORT"])
    if os.environ.get("MINDMAP_DATABASE"):
        data["database"] = os.environ["MINDMAP_DATABASE"]
    if os.environ.get("MINDMAP_JWT_SECRET"):
        data["jwt_secret"] = os.environ["MINDMAP_JWT_SECRET"]

    return AppConfig(**data)
