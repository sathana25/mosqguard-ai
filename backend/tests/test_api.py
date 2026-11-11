"""End-to-end flow: report -> detect -> duplicate check -> assign -> clean -> verify."""
from io import BytesIO

from PIL import Image, ImageDraw

from app.models import Ward
from app.services.risk import score_report


def puddle_jpeg(seed: int = 0) -> bytes:
    img = Image.new("RGB", (400, 300), (130, 110, 85))
    d = ImageDraw.Draw(img)
    d.ellipse([60 + seed, 120, 340, 280], fill=(50, 66, 62))  # dark, smooth water
    buf = BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def submit(client, headers, lat, lon, seed=0):
    return client.post(
        "/api/reports",
        headers=headers,
        data={"lat": str(lat), "lon": str(lon), "note": "test"},
        files={"photo": ("p.jpg", puddle_jpeg(seed), "image/jpeg")},
    )


def test_health(client):
    r = client.get("/api/health")
    assert r.json()["status"] == "ok"


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "officer1", "password": "nope"})
    assert r.status_code == 401


def test_register_resident(client):
    r = client.post("/api/auth/register", json={"username": "newuser", "name": "New", "password": "secret1"})
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "resident"


def test_full_workflow(client, resident, officer, worker):
    # 1. Resident reports a puddle
    r = submit(client, resident, 11.03, 76.99)
    assert r.status_code == 200, r.text
    body = r.json()
    rep = body["report"]
    assert body["duplicate"] is False
    assert rep["detection"]["suspected"] is True
    assert rep["risk"]["level"] in ("High", "Medium", "Low")
    assert rep["risk"]["reasons"]

    # 2. Same spot reported again -> merged
    r2 = submit(client, resident, 11.03001, 76.99001, seed=4)
    assert r2.json()["duplicate"] is True
    assert r2.json()["report"]["id"] == rep["id"]
    assert r2.json()["report"]["confirmations"] == 2

    # 3. Officer assigns it
    workers = client.get("/api/workers", headers=officer).json()
    w1 = next(w for w in workers if w["username"] == "worker1")
    r = client.post(f"/api/reports/{rep['id']}/assign", headers=officer, json={"worker_id": w1["id"]})
    assert r.json()["status"] == "assigned"

    # Residents cannot assign
    assert client.post(f"/api/reports/{rep['id']}/assign", headers=resident, json={"worker_id": w1["id"]}).status_code == 403

    # 4. Worker sees the task and uploads an after photo
    tasks = client.get("/api/reports", headers=worker).json()
    assert any(t["id"] == rep["id"] for t in tasks)
    r = client.post(f"/api/reports/{rep['id']}/clean", headers=worker,
                    files={"photo": ("after.jpg", puddle_jpeg(9), "image/jpeg")})
    assert r.json()["status"] == "cleaned"
    assert r.json()["after_photo_url"]

    # 5. Officer verifies and closes
    r = client.post(f"/api/reports/{rep['id']}/verify", headers=officer, json={"approve": True})
    assert r.json()["status"] == "closed"


def test_bad_file_rejected(client, resident):
    r = client.post("/api/reports", headers=resident, data={"lat": "11", "lon": "77"},
                    files={"photo": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_officer_dashboards(client, officer):
    assert len(client.get("/api/wards", headers=officer).json()) == 6
    assert client.get("/api/forecast", headers=officer).status_code == 200
    assert "by_status" in client.get("/api/analytics", headers=officer).json()


def test_risk_rises_with_rain_and_reports():
    dry = Ward(name="Dry", rain_7d_mm=0, dengue_cases_30d=0)
    wet = Ward(name="Wet", rain_7d_mm=170, dengue_cases_30d=6)
    det = {"suspected": True, "confidence": 0.8}
    assert score_report(det, wet, 3)["score"] > score_report(det, dry, 1)["score"]
    assert score_report({"suspected": False, "confidence": 0.9}, wet)["level"] == "Low"
