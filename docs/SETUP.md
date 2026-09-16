# Setup & Run Guide

How to set up and run the Roofing Sales Intelligence Platform — the whole stack at
once, or the backend and frontend separately.

---

## 1. Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend (developed on 3.13) |
| Node.js | 18+ | Frontend |
| npm | 9+ | Ships with Node |
| Docker + Docker Compose | recent | Only for the "whole app" path |
| PostgreSQL | 16 | Provided by Docker; or install locally |

Check what you have:

```bash
python3 --version
node --version
docker --version
```

---

## 2. Run the whole app (Docker — easiest)

Starts Postgres, the backend API, and the frontend together.

```bash
# from the repo root
docker compose up --build
```

Then open:

- **UI** — http://localhost:5173
- **API** — http://localhost:8000 (interactive docs at http://localhost:8000/docs)
- **Postgres** — localhost:5432 (user `sales`, password `sales`, db `sales_intel`)

Stop it:

```bash
docker compose down          # keep data
docker compose down -v       # also wipe the Postgres volume
```

> The first `--build` is slow (installs everything). Later runs are fast.

---

## 3. Run the backend on its own

Use this when working on the API or pipeline.

### 3a. Create a virtual environment and install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # app + dev tools (pytest, ruff, mypy)
```

### 3b. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed. The default `DATABASE_URL` points at the Docker Postgres:

```
DATABASE_URL=postgresql+psycopg://sales:sales@localhost:5432/sales_intel
```

You still need a Postgres running. Quickest option — start just the DB container:

```bash
# from repo root
docker compose up -d db
```

(Or install Postgres locally and create the `sales_intel` database yourself.)

### 3c. Create the database schema

Once models are stable, generate and apply migrations:

```bash
cd backend
alembic revision --autogenerate -m "init"   # first time only
alembic upgrade head
```

### 3d. Run the API

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health → `{"status":"ok"}`

### 3f. Try the GAF data source

The live contractor search needs no keys or config — the Coveo tokens ship with
sensible defaults. Just hit the endpoint:

```bash
# nearest certified contractors to a ZIP (defaults: zip 10013, radius 25 mi)
curl "http://localhost:8000/api/gaf-contractors?zip_code=90210&distance=25"
```

Returns `{ zip_searched, coordinates, total_found, results[] }`. See the
data-source section of `PLAN.md` for what each field means.

> **First call is slower:** `pgeocode` downloads a US postal-code database on first
> use and caches it locally (`~/.cache` / `~/.local`). Needs one-time internet access.
> This endpoint also calls GAF's public Coveo API, so the backend needs outbound
> internet at request time.

### 3e. Backend tests

```bash
pytest              # run the suite
ruff check .        # lint
mypy app            # type-check
```

---

## 4. Run the frontend on its own

Use this when working on the UI. It expects the backend to be reachable.

```bash
cd frontend
npm install
cp .env.example .env         # set VITE_API_BASE_URL to your API (default http://localhost:8000)
npm run dev
```

- App: http://localhost:5173

Other commands:

```bash
npm run build       # production build
npm run preview     # preview the production build
```

---

## 5. Typical local dev loop (backend + frontend separately)

Three terminals:

```bash
# terminal 1 — database
docker compose up -d db

# terminal 2 — backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# terminal 3 — frontend
cd frontend && npm run dev
```

Edit code; both the API (`--reload`) and the UI (Vite HMR) hot-reload.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| UI shows "Failed to load… Is the API running?" | Backend down or wrong `VITE_API_BASE_URL` | Start backend; check `.env` |
| `connection refused` on port 5432 | Postgres not running | `docker compose up -d db` |
| `ModuleNotFoundError: app` | venv not active / not installed | `source .venv/bin/activate && pip install -e ".[dev]"` |
| Alembic "target database is not up to date" | Missing migration | `alembic upgrade head` |
| CORS error in browser console | Origin not allowed | Add UI origin to `BACKEND_CORS_ORIGINS` in backend `.env` |
| Port already in use | Another process on 8000/5173 | Stop it, or change the port flag |
| `/api/gaf-contractors` hangs or errors | No outbound internet, or Coveo/pgeocode unreachable | Ensure the backend host has internet; retry |
| "Invalid or unrecognized ZIP code" | ZIP not in the US postal DB | Use a valid 5-digit US ZIP |

---

## 7. Ports & credentials reference

| Service | URL / Port | Credentials |
|---------|-----------|-------------|
| Frontend | http://localhost:5173 | — |
| Backend API | http://localhost:8000 | — |
| API docs | http://localhost:8000/docs | — |
| GAF data source | http://localhost:8000/api/gaf-contractors | — (no client auth) |
| Postgres | localhost:5432 | `sales` / `sales` / db `sales_intel` |

> These are local development defaults only. Production uses managed secrets — see
> the data-management section of `PLAN.md`.
