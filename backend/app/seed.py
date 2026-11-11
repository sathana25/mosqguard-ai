"""Creates demo wards, users and a few sample reports on first start."""
import os
from datetime import timedelta

from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from .auth import hash_password
from .config import MAP_LAT, MAP_LON, UPLOAD_DIR
from .models import Report, User, Ward, now
from .services.geo import image_hash
from .services.risk import score_report

# Sample ward conditions. Replace with real IMD / health-department data.
WARDS = [
    # name,          rain 7d mm, dengue cases 30d, rain forecast next 7d mm
    ("Anna Nagar", 82, 1, 40),
    ("Gandhi Road", 146, 4, 95),
    ("Market Area", 120, 3, 70),
    ("Riverside", 168, 6, 120),
    ("Bus Stand", 64, 0, 30),
    ("College Road", 95, 2, 55),
]
WARD_SIZE = 0.012  # degrees, about 1.3 km

USERS = [
    # username, name, role, password, ward
    ("resident1", "Ravi Kumar", "resident", "resident123", 4),
    ("officer1", "Ward Health Officer", "officer", "officer123", None),
    ("worker1", "Murugan", "worker", "worker123", None),
    ("worker2", "Selvi", "worker", "worker123", None),
    ("worker3", "Karthik", "worker", "worker123", None),
]


def ward_box(i: int):
    col, row = i % 3, i // 3
    min_lon = MAP_LON + (col - 1.5) * WARD_SIZE
    max_lat = MAP_LAT + (1 - row) * WARD_SIZE
    return max_lat - WARD_SIZE, max_lat, min_lon, min_lon + WARD_SIZE


def _sample_photo(name: str, kind: str) -> str:
    """Draws a simple illustration so sample reports have a picture."""
    path = UPLOAD_DIR / name
    if path.exists():
        return name
    img = Image.new("RGB", (640, 480), (122, 104, 82))
    d = ImageDraw.Draw(img)
    for y in range(0, 480, 24):
        d.line([(0, y), (640, y + 12)], fill=(112, 95, 74), width=3)
    if kind == "tyre":
        d.ellipse([150, 140, 490, 380], fill=(28, 28, 30))
        d.ellipse([230, 205, 410, 315], fill=(58, 72, 70))
    elif kind == "tank":
        d.rectangle([140, 120, 500, 400], fill=(150, 150, 150))
        d.rectangle([165, 145, 475, 375], fill=(48, 70, 66))
    else:
        d.ellipse([90, 220, 560, 420], fill=(62, 78, 74))
        d.ellipse([240, 120, 330, 210], fill=(200, 160, 110))
    d.text((16, 16), "SAMPLE PHOTO", fill=(255, 255, 255))
    img.save(path, "JPEG", quality=85)
    return name


def seed(db: Session) -> None:
    if db.query(Ward).count() == 0:
        for i, (name, rain, cases, fc) in enumerate(WARDS):
            a, b, c, e = ward_box(i)
            db.add(Ward(id=i + 1, name=name, min_lat=a, max_lat=b, min_lon=c, max_lon=e,
                        rain_7d_mm=rain, dengue_cases_30d=cases, rain_forecast_7d_mm=fc))
        db.commit()

    if db.query(User).count() == 0:
        for username, name, role, pw, ward in USERS:
            db.add(User(username=username, name=name, role=role, password_hash=hash_password(pw), ward=ward))
        db.commit()

    if os.getenv("SEED_DEMO_REPORTS", "true").lower() == "true" and db.query(Report).count() == 0:
        resident = db.query(User).filter_by(username="resident1").one()
        worker = db.query(User).filter_by(username="worker1").one()
        samples = [
            (4, 0.4, 0.5, "tyre", "Old tyres dumped near the river bank",
             {"suspected": True, "confidence": 0.91, "objects": [{"label": "tyre", "confidence": 0.91, "box": None}],
              "water_visible": True, "larvae_visible": True}, "open", 2, None),
            (2, 0.6, 0.4, "tank", "Open water tank on a construction site",
             {"suspected": True, "confidence": 0.84, "objects": [{"label": "open tank", "confidence": 0.84, "box": None}],
              "water_visible": True, "larvae_visible": False}, "assigned", 1, worker),
            (5, 0.5, 0.6, "puddle", "Water collecting behind the tea shop",
             {"suspected": True, "confidence": 0.62, "objects": [{"label": "possible standing water", "confidence": 0.62, "box": None}],
              "water_visible": True, "larvae_visible": False}, "open", 1, None),
        ]
        for i, (ward_id, fy, fx, kind, note, det, status, conf, assignee) in enumerate(samples):
            w = db.get(Ward, ward_id)
            photo = _sample_photo(f"sample_{kind}.jpg", kind)
            det = {**det, "engine": "Sample data", "summary": f"Sample report: {note.lower()}."}
            r = Report(
                reporter_id=resident.id,
                lat=w.min_lat + (w.max_lat - w.min_lat) * fy,
                lon=w.min_lon + (w.max_lon - w.min_lon) * fx,
                ward_id=ward_id, note=note, photo=photo,
                image_hash=image_hash(UPLOAD_DIR / photo),
                detection=det, status=status, confirmations=conf,
                created_at=now() - timedelta(hours=6 - i),
            )
            r.risk = score_report(det, w, conf)
            r.risk_score = r.risk["score"]
            if assignee:
                r.assigned_to_id = assignee.id
                r.assigned_at = now() - timedelta(hours=2)
            db.add(r)
        db.commit()
