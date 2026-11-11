import os
import sys
import tempfile
from pathlib import Path

# Isolated database and uploads for tests; fast heuristic detector
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["STATIC_DIR"] = f"{_tmp}/no-frontend"
os.environ["DETECTOR"] = "heuristic"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def resident(client):
    return login(client, "resident1", "resident123")


@pytest.fixture
def officer(client):
    return login(client, "officer1", "officer123")


@pytest.fixture
def worker(client):
    return login(client, "worker1", "worker123")
