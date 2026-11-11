"""App settings. Every value can be overridden with an environment variable."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


DATABASE_URL = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'mosqguard.db'}")
UPLOAD_DIR = Path(_env("UPLOAD_DIR", str(BASE_DIR / "uploads")))
STATIC_DIR = Path(_env("STATIC_DIR", str(BASE_DIR.parent / "frontend" / "dist")))

SECRET_KEY = _env("SECRET_KEY", "change-me-in-production")
TOKEN_HOURS = int(_env("TOKEN_HOURS", "24"))

# Detector: "auto" uses YOLOv8 when ultralytics is installed, else the basic heuristic.
DETECTOR = _env("DETECTOR", "auto")
# Path to custom fine-tuned weights (see ml/train.py). Falls back to COCO yolov8n.pt.
MODEL_PATH = _env("MODEL_PATH", str(BASE_DIR.parent / "ml" / "weights" / "mosqguard.pt"))

# Town the demo wards are laid out around (default: Coimbatore, Tamil Nadu).
MAP_LAT = float(_env("MAP_LAT", "11.0168"))
MAP_LON = float(_env("MAP_LON", "76.9558"))

# Optional live weather. Without a key the app uses the sample ward data.
OPENWEATHER_API_KEY = _env("OPENWEATHER_API_KEY", "")

# Duplicate check: reports closer than this (metres) to an open report may be merged.
DUPLICATE_RADIUS_M = float(_env("DUPLICATE_RADIUS_M", "50"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
