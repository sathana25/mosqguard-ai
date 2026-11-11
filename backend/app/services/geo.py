"""Location helpers: distance, ward lookup and duplicate detection."""
import math

from PIL import Image
from sqlalchemy.orm import Session

from ..config import DUPLICATE_RADIUS_M
from ..models import Report, Ward


def distance_m(lat1, lon1, lat2, lon2) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def find_ward(db: Session, lat: float, lon: float) -> Ward:
    wards = db.query(Ward).all()
    for w in wards:
        if w.min_lat <= lat <= w.max_lat and w.min_lon <= lon <= w.max_lon:
            return w
    # Outside every ward: use the nearest ward centre
    return min(wards, key=lambda w: distance_m(lat, lon, (w.min_lat + w.max_lat) / 2, (w.min_lon + w.max_lon) / 2))


def image_hash(path) -> str:
    """64-bit difference hash: similar photos give similar hashes."""
    img = Image.open(path).convert("L").resize((9, 8))
    px = list(img.getdata())
    bits = "".join("1" if px[r * 9 + c] > px[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))
    return f"{int(bits, 2):016x}"


def hash_distance(a: str, b: str) -> int:
    if not a or not b:
        return 64
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def find_duplicate(db: Session, lat: float, lon: float, img_hash: str) -> Report | None:
    """An open report nearby is a duplicate if it is very close, or close and the photos look alike."""
    best, best_d = None, None
    for r in db.query(Report).filter(Report.status != "closed").all():
        d = distance_m(lat, lon, r.lat, r.lon)
        if d > DUPLICATE_RADIUS_M:
            continue
        similar = hash_distance(img_hash, r.image_hash) <= 20
        if d <= 15 or similar:
            if best_d is None or d < best_d:
                best, best_d = r, d
    return best
