"""Run the same detector the app uses on one photo, from the command line.

    cd backend && python ../ml/predict.py path/to/photo.jpg
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.detector import detect, get_detector  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python ml/predict.py photo.jpg")
    print("Engine:", get_detector().name)
    print(json.dumps(detect(sys.argv[1]), indent=2))
