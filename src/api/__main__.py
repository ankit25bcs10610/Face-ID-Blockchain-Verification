"""Run the API with ``python -m src.api``."""

import uvicorn

from src.config import settings


if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=False)
