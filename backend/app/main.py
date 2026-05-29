"""Recce FastAPI app: serves the API and the built frontend from one container."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routes import router

settings = get_settings()

app = FastAPI(
    title="Recce API",
    version="0.1.0",
    description="AI location scouting, from script to shoot day.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

STATIC_DIR = Path(__file__).parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str):
    """Serve the single-page app, or a friendly message before the frontend is built."""
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "message": "Recce API is running. The frontend is not built yet.",
        "try": ["/api/health", "/docs"],
    }
