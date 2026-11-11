# MOSQGUARD AI

**Mosquito breeding detection and disease prevention.**
Residents photograph stagnant water, AI checks the photo, the system ranks each site by risk using rainfall and dengue data, and health officers send field workers to clean it, with before/after photo proof.

AI Hackathon 2026 · Slot II · Climate, Disease Prediction and Public Health · Sector 2 (MOSQGUARD AI).

---

## What it does

| Role | What they can do |
|---|---|
| **Resident** | Take a photo, mark the place (GPS or tap the map), send. See the AI result, risk score and cleanup progress. |
| **Officer** | Hotspot map with colour-coded pins, reports ranked by risk, 7-day ward outlook, assign to a worker, verify cleanup and close. |
| **Field worker** | See assigned spots with directions, upload an "after" photo, mark as cleaned. |

AI and smart features:

- **Breeding-site detection:** YOLOv8 finds water-holding objects in the photo (see [How the AI works](#how-the-ai-works)).
- **Duplicate check:** a report within 50 m of an open report, with a similar photo, is merged instead of creating a new task.
- **Explainable risk score (0–100):** combines AI confidence, rain in the last 7 days, dengue cases in the ward, repeat reports and visible larvae. Every score lists its reasons.
- **7-day hotspot outlook:** ranks wards by forecast rain, recent cases and report activity.
- **PWA:** installs on any phone from the browser ("Add to Home screen"). No Play Store needed.

The AI only flags *suspected* sites. A field worker always confirms on the spot.

---

## Quick start

### Option A: Docker (one command)

```bash
docker compose up --build
```

Open http://localhost:8000. The first build takes a few minutes because it installs YOLOv8. For a faster build without YOLOv8, set `INSTALL_ML: "false"` in `docker-compose.yml`.

### Option B: Run without Docker

You need **Python 3.11+** and **Node.js 18+**.

**1. Backend** (terminal 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend dev server forwards `/api` calls to the backend on port 8000.

**3. Optional: real YOLOv8 detection**

```bash
cd backend
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-ml.txt
```

Restart the backend. `http://localhost:8000/api/health` shows which detector is running.

### Demo accounts

The login page has one-tap buttons for these.

| Role | Username | Password |
|---|---|---|
| Resident | `resident1` | `resident123` |
| Officer | `officer1` | `officer123` |
| Field worker | `worker1` (Murugan), `worker2` (Selvi), `worker3` (Karthik) | `worker123` |

New residents can also create their own account.

### Try the full flow (2 minutes)

1. Log in as **Resident**, add a photo of water in a bucket or a puddle, tap the map, send.
2. Log out, log in as **Officer**, open the new report, assign it to **Murugan**.
3. Log in as **Field worker** (`worker1`), add an after photo, mark as cleaned.
4. Log in as **Officer** again, compare the photos, **Verify and close**.

---

## Run the tests

```bash
cd backend
python -m pytest -q
```

The tests cover login, roles, photo upload, AI detection, duplicate merging, risk scoring and the full assign → clean → verify workflow. GitHub Actions runs them on every push (`.github/workflows/ci.yml`), along with a frontend build.

API documentation (interactive): http://localhost:8000/docs

---

## Use it on a phone

- **Same Wi-Fi:** run `npm run dev`, then open `http://<your-computer-ip>:5173` on the phone.
- **Install as an app:** phones only allow installing, camera and GPS on **HTTPS**. Deploy the Docker image to any host with HTTPS (Render, Railway, a VM with Caddy), or share your laptop with a tunnel such as `cloudflared tunnel --url http://localhost:8000`. Then open the link and choose **Add to Home screen**.

---

## Project structure

```
mosqguard-ai/
├── backend/                 FastAPI + SQLite
│   ├── app/
│   │   ├── main.py          app setup, serves the built frontend
│   │   ├── config.py        settings (all overridable by env variables)
│   │   ├── models.py        database tables: User, Ward, Report
│   │   ├── auth.py          password hashing, JWT login, role checks
│   │   ├── seed.py          demo wards, users and sample reports
│   │   ├── routers/         API endpoints (auth, reports, wards/forecast/analytics)
│   │   └── services/
│   │       ├── detector.py  AI detection (YOLOv8 or heuristic fallback)
│   │       ├── risk.py      explainable risk score
│   │       ├── geo.py       ward lookup, distance, duplicate check
│   │       └── weather.py   optional OpenWeather integration
│   └── tests/               pytest end-to-end tests
├── frontend/                React + Vite PWA
│   └── src/
│       ├── pages/           Login, Report, MyReports, Officer, Worker
│       ├── components/      MapView (Leaflet), shared UI pieces
│       ├── api.js           fetch wrapper with login token
│       └── styles.css       all styling (colour tokens at the top)
├── ml/                      YOLOv8 training and prediction scripts
├── Dockerfile               builds frontend + backend into one image
└── docker-compose.yml
```

---

## How the AI works

`backend/app/services/detector.py` picks the best available engine automatically:

| Engine | When it is used | What it detects |
|---|---|---|
| **Custom YOLOv8** | `ml/weights/mosqguard.pt` exists | stagnant water, containers, tyres, drains, larvae (whatever you train) |
| **Pretrained YOLOv8n** | `ultralytics` is installed | water-holding objects from COCO (bottle, cup, bowl, pot, sink…) plus a water check |
| **Basic heuristic** | no ML packages installed | smooth dark or reflective regions that look like standing water |

The heuristic keeps the app running on any laptop, but it is much less accurate. For a real deployment, train the custom model:

```bash
cp ml/data.yaml.example ml/data.yaml     # point it at your labelled images
python ml/train.py --data ml/data.yaml --epochs 50
```

Training prints mAP@0.5, precision and recall and saves `ml/weights/mosqguard.pt`; restart the backend to use it. Test one photo from the command line with `cd backend && python ../ml/predict.py photo.jpg`.

**Risk score** (`backend/app/services/risk.py`):

| Factor | Max points |
|---|---|
| AI confidence | 45 |
| Rain in last 7 days (full at 170 mm) | 25 |
| Dengue cases in ward (full at 6) | 20 |
| Extra people reporting the same spot | 10 |
| Possible larvae visible | 8 |

65+ is **High**, 40–64 **Medium**, below 40 **Low**.

---

## How to modify

Common changes and where to make them. After a backend change, `--reload` restarts the server automatically; after a frontend change, the page reloads by itself.

| I want to… | Change this |
|---|---|
| Change risk weights or High/Medium thresholds | `WEIGHTS`, `HIGH`, `MEDIUM` in `backend/app/services/risk.py` |
| Use my own town on the map | env `MAP_LAT`, `MAP_LON` (or defaults in `backend/app/config.py`), then delete `backend/mosqguard.db` |
| Rename wards or change their rain / dengue numbers | `WARDS` in `backend/app/seed.py`, then delete `backend/mosqguard.db` |
| Add field workers or change demo passwords | `USERS` in `backend/app/seed.py`, then delete `backend/mosqguard.db` |
| Change the duplicate distance | env `DUPLICATE_RADIUS_M` (default 50) |
| Use live weather | set env `OPENWEATHER_API_KEY` (free key from openweathermap.org) |
| Add a new detectable class | train it (see above) and add its name to `CUSTOM_RISK_CLASSES` in `detector.py` |
| Change colours or fonts | tokens at the top of `frontend/src/styles.css` |
| Change any screen | `frontend/src/pages/*.jsx` |
| Add an API endpoint | add a function to a file in `backend/app/routers/`, call it with `api('/api/...')` from the frontend |
| Start with an empty database (no sample reports) | env `SEED_DEMO_REPORTS=false`, delete `backend/mosqguard.db` |

The database is a single SQLite file (`backend/mosqguard.db`). Delete it to reset everything; it is recreated with demo data on the next start. With Docker: `docker compose down -v`.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | signs login tokens; set your own when deploying |
| `DATABASE_URL` | `sqlite:///backend/mosqguard.db` | any SQLAlchemy URL (PostgreSQL works too) |
| `DETECTOR` | `auto` | `auto`, `yolo` or `heuristic` |
| `MODEL_PATH` | `ml/weights/mosqguard.pt` | custom YOLOv8 weights |
| `MAP_LAT`, `MAP_LON` | Coimbatore | centre of the demo wards |
| `OPENWEATHER_API_KEY` | empty | live weather; empty uses sample data |
| `DUPLICATE_RADIUS_M` | `50` | duplicate-report distance |
| `SEED_DEMO_REPORTS` | `true` | add 3 sample reports on first start |

---

## Data and limits

- Ward rainfall and dengue case numbers are **sample data**. In a real deployment they come from a weather API and health department records.
- Sample reports use drawn illustrations, marked "SAMPLE PHOTO".
- The 7-day outlook is a simple, explainable trend model, not a trained forecast.
- Photos and reporter names are visible to officers only; residents see their own reports and the anonymous hotspot map.

## Tech stack

React 18, Vite, vite-plugin-pwa, Leaflet + OpenStreetMap · FastAPI, SQLAlchemy, SQLite, JWT · YOLOv8 (Ultralytics), Pillow, NumPy · Docker, GitHub Actions.
