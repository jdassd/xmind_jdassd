from __future__ import annotations

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
    return AppConfig(**data)
