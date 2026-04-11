"""Run the API with: python -m backend.api (from repo root, venv active)."""

import os

import uvicorn

from backend.api.config import API_HOST, API_PORT

if __name__ == "__main__":
    dev = os.environ.get("ZIMON_DEV", "").lower() in ("1", "true", "yes")
    uvicorn.run(
        "backend.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=dev,
    )
