"""Ward weather. Uses OpenWeather when OPENWEATHER_API_KEY is set, else the sample values in the database."""
import logging
import time

import httpx

from ..config import OPENWEATHER_API_KEY

log = logging.getLogger(__name__)
_cache: dict[int, tuple[float, dict]] = {}
CACHE_SECONDS = 1800


def live_weather(ward) -> dict | None:
    if not OPENWEATHER_API_KEY:
        return None
    hit = _cache.get(ward.id)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    lat, lon = (ward.min_lat + ward.max_lat) / 2, (ward.min_lon + ward.max_lon) / 2
    try:
        r = httpx.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=8,
        )
        r.raise_for_status()
        items = r.json()["list"]
        rain_next = sum(i.get("rain", {}).get("3h", 0) for i in items)
        now = items[0]["main"]
        data = {"temp_c": now["temp"], "humidity_pct": now["humidity"], "rain_forecast_5d_mm": round(rain_next, 1)}
        _cache[ward.id] = (time.time(), data)
        return data
    except Exception as exc:
        log.warning("OpenWeather request failed: %s", exc)
        return None
