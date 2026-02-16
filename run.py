import logging
import uvicorn
from backend.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

config = load_config("config.yaml")
uvicorn.run(
    "backend.app:create_app",
    factory=True,
    host="0.0.0.0",
    port=config.port,
    reload=False,
    log_level="info",
)
