from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..config import MAP_LAT, MAP_LON
from ..db import get_db
from ..models import Report, User, Ward
from ..services.risk import level_for
from ..services.weather import live_weather

router = APIRouter(prefix="/api", tags=["wards"])


@router.get("/config")
def app_config():
    return {"map_center": [MAP_LAT, MAP_LON], "map_zoom": 14}


@router.get("/wards")
def wards(db: Session = Depends(get_db), _: User = Depends(current_user)):
    open_reports = db.query(Report).filter(Report.status != "closed").all()
    out = []
    for w in db.query(Ward).order_by(Ward.id).all():
        mine = [r for r in open_reports if r.ward_id == w.id]
        top = max((r.risk_score for r in mine), default=0)
        out.append({
            "id": w.id, "name": w.name,
            "bounds": [[w.min_lat, w.min_lon], [w.max_lat, w.max_lon]],
            "rain_7d_mm": w.rain_7d_mm, "dengue_cases_30d": w.dengue_cases_30d,
            "open_reports": len(mine), "top_risk": level_for(top) if mine else None,
            "live_weather": live_weather(w), "data_source": "sample",
        })
    return out


@router.get("/forecast")
def forecast(db: Session = Depends(get_db), _: User = Depends(require_role("officer"))):
    """7-day hotspot outlook per ward.

    Simple, explainable trend model: rain expected in the next 7 days, recent
    dengue cases and how many sites were reported in the ward recently.
    """
    counts = Counter(r.ward_id for r in db.query(Report).all())
    out = []
    for w in db.query(Ward).order_by(Ward.id).all():
        lw = live_weather(w)
        rain_next = lw["rain_forecast_5d_mm"] * 7 / 5 if lw else w.rain_forecast_7d_mm
        score = min(100, round(min(rain_next / 120, 1) * 45 + min(w.dengue_cases_30d, 6) / 6 * 30 + min(counts[w.id], 5) / 5 * 25))
        out.append({
            "ward_id": w.id, "ward_name": w.name, "score": score, "level": level_for(score),
            "rain_next_7d_mm": round(rain_next), "reports": counts[w.id],
        })
    return sorted(out, key=lambda x: -x["score"])


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _: User = Depends(require_role("officer"))):
    rs = db.query(Report).all()
    status = Counter(r.status for r in rs)
    closed = [r for r in rs if r.closed_at and r.created_at]
    hours = [(r.closed_at - r.created_at).total_seconds() / 3600 for r in closed]
    return {
        "total": len(rs),
        "by_status": {s: status.get(s, 0) for s in ("open", "assigned", "cleaned", "closed")},
        "high_risk_open": sum(1 for r in rs if r.status != "closed" and r.risk.get("level") == "High"),
        "avg_hours_to_close": round(sum(hours) / len(hours), 1) if hours else None,
        "by_ward": dict(Counter(r.ward.name for r in rs)),
    }
