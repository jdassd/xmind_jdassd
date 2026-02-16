from __future__ import annotations

import os

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    port: int = 8080
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "mindmap"
    db_password: str = "mindmap"
    db_name: str = "mindmap"
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
    if os.environ.get("MYSQL_HOST"):
        data["db_host"] = os.environ["MYSQL_HOST"]
    if os.environ.get("MYSQL_PORT"):
        data["db_port"] = int(os.environ["MYSQL_PORT"])
    if os.environ.get("MYSQL_USER"):
        data["db_user"] = os.environ["MYSQL_USER"]
    if os.environ.get("MYSQL_PASSWORD"):
        data["db_password"] = os.environ["MYSQL_PASSWORD"]
    if os.environ.get("MYSQL_DATABASE"):
        data["db_name"] = os.environ["MYSQL_DATABASE"]
    if os.environ.get("MINDMAP_JWT_SECRET"):
        data["jwt_secret"] = os.environ["MINDMAP_JWT_SECRET"]

    return AppConfig(**data)
