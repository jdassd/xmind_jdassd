import uvicorn
from backend.config import load_config

config = load_config("config.yaml")
uvicorn.run(
    "backend.app:create_app",
    factory=True,
    host="0.0.0.0",
    port=config.port,
    reload=False,
)
