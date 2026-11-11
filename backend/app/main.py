"""MOSQGUARD AI backend: FastAPI app, API routes and the built frontend."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR, UPLOAD_DIR
from .db import Base, SessionLocal, engine
from .routers import auth, reports, wards
from .seed import seed
from .services.detector import get_detector

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MOSQGUARD AI", version="1.0.0",
              description="Mosquito breeding-site reporting, AI detection and cleanup tracking")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(engine)
with SessionLocal() as _db:
    seed(_db)

app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(wards.router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "detector": get_detector().name}


# Serve the built React PWA (npm run build) from the same server
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = STATIC_DIR / path
        if path and file.is_file() and STATIC_DIR in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
