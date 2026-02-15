from __future__ import annotations

import os

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    port: int = 8080
    database: str = "./data/mindmap.db"


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

    return AppConfig(**data)
