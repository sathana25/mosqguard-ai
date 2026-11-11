"""Explainable risk score (0-100) for a reported site.

Each factor adds points and a plain-language reason, so officers can see
*why* a site is High priority. The weights are a transparent baseline; the
final build can swap this for the XGBoost + SHAP model in ml/ while keeping
the same output shape.
"""

WEIGHTS = {
    "ai": 45,          # detection confidence
    "rain": 25,        # rainfall in last 7 days (full points at RAIN_FULL_MM)
    "cases": 20,       # dengue cases in ward (full points at CASES_FULL)
    "reports": 10,     # extra people reporting the same spot (5 each, max 2)
    "larvae": 8,       # possible larvae seen
}
RAIN_FULL_MM = 170
CASES_FULL = 6
HIGH, MEDIUM = 65, 40


def level_for(score: int) -> str:
    return "High" if score >= HIGH else "Medium" if score >= MEDIUM else "Low"


def score_report(detection: dict, ward, confirmations: int = 1) -> dict:
    reasons: list[str] = []
    conf = float(detection.get("confidence", 0))

    if not detection.get("suspected"):
        score = round(conf * 15)
        reasons.append("AI did not find a clear breeding site in the photo")
        return {"score": score, "level": level_for(score), "reasons": reasons}

    pts = conf * WEIGHTS["ai"]
    reasons.append(f"AI is {round(conf * 100)}% sure this can breed mosquitoes")

    rain = ward.rain_7d_mm
    pts += min(rain / RAIN_FULL_MM, 1) * WEIGHTS["rain"]
    reasons.append(f"{'Heavy rain' if rain >= 120 else 'Rain'} in {ward.name}: {rain:.0f} mm in the last 7 days")

    cases = ward.dengue_cases_30d
    pts += min(cases, CASES_FULL) / CASES_FULL * WEIGHTS["cases"]
    if cases:
        reasons.append(f"{cases} dengue case{'s' if cases > 1 else ''} reported in this ward this month")

    extra = min(max(confirmations - 1, 0), 2)
    pts += extra * WEIGHTS["reports"] / 2
    if extra:
        reasons.append(f"Reported by {confirmations} different people")

    if detection.get("larvae_visible"):
        pts += WEIGHTS["larvae"]
        reasons.append("Possible larvae visible in the water")

    score = min(100, round(pts))
    return {"score": score, "level": level_for(score), "reasons": reasons}
