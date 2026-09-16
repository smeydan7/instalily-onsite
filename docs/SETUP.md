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

## 2. Run the whole app (Docker)

Starts Postgres, the backend API, and the frontend together.

```bash
# from the repo root
docker compose up --build
```

> **`docker: unknown command: compose`?** Compose V2 is a separate CLI plugin that
> Colima/Docker Engine doesn't bundle. Install it once:
>
> ```bash
> brew install docker-compose
> mkdir -p ~/.docker/cli-plugins
> ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose
> docker compose version   # should now print a version
> ```
>
> Prefer not to install it? Use **Option B** below — no Compose required.

### Option B — no Docker Compose (just a Postgres container)

Run Postgres directly, then run the two apps natively (Sections 3 & 4). This is the
lightest path and needs only the Docker daemon (e.g. `colima start`).

```bash
docker run -d --name sales-pg \
  -e POSTGRES_USER=sales -e POSTGRES_PASSWORD=sales -e POSTGRES_DB=sales_intel \
  -p 5432:5432 postgres:16

# stop / remove later:
#   docker stop sales-pg   (keep data)
#   docker rm -f sales-pg  (wipe it)
```

Then start the backend (Section 3d) and frontend (Section 4). Continue below for the
full Compose path.

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

**Dev default:** the app auto-creates tables on startup (`AUTO_CREATE_TABLES=true`), so
you can skip migrations while iterating locally — just start the API against a running
Postgres.

**Production path:** turn that off and use Alembic migrations:

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
curl "http://localhost:8000/api/v1/gaf-contractors?zip_code=90210&distance=25"
```

Returns `{ zip_searched, coordinates, total_found, results[] }`. See the
data-source section of `PLAN.md` for what each field means.

> **First call is slower:** `pgeocode` downloads a US postal-code database on first
> use and caches it locally (`~/.cache` / `~/.local`). Needs one-time internet access.
> This endpoint also calls GAF's public Coveo API, so the backend needs outbound
> internet at request time.

### 3g. Generate leads (run the pipeline)

The live endpoint above is a raw passthrough. To create **scored, persisted leads** that
show up in the UI, run the ingestion pipeline for one or more territory ZIPs:

```bash
# trigger an ingest (runs in the background; needs Postgres + internet)
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"source_key":"gaf_contractors","config":{"zips":["90210"],"radius":25}}'

# check run status + how many records were ingested
curl http://localhost:8000/api/v1/pipeline/runs

# see the generated leads
curl "http://localhost:8000/api/v1/leads?limit=5"
```

In the UI, this is the main flow: on the **Leads** page, type a ZIP + radius and hit
**Search**. The page opens on **10013 (New York)** by default and self-seeds it on first
run. Searching another ZIP ingests that territory and scopes the list to it (e.g. `30301`
→ Atlanta; `90210` → LA; "show all territories" clears the scope). Re-running is safe —
contractors upsert on their GAF id, so leads aren't duplicated and any status you've set
is preserved.

## Data notes (correctness)

We reproduce GAF's public "find a contractor" search **exactly** — same set, same order:

- **Exact query match.** GAF's site uses its Coveo pipeline with `tab=defaultTab` and
  `context.sortingStrategy=gafrecommended-initial`. Adding those to our payload returns
  the identical result set and ordering. Verified for `10013` + 25 mi: **83 results**, and
  the first ten match the site position-for-position (Allied Brothers Home Corporation,
  Grapevine Pro, Jersey Roofing LLC, American Home Contractors, Donny's Home Improvement,
  John Goess Roofing, Brothers Aluminum, Blue Nail Exteriors, The Great American Roofing,
  American Roofing and Siding).
- **GAF's order is preserved.** We store each contractor's position (`gaf_rank`) from that
  search and sort the lead list by it, so the UI mirrors the site. We also compute a
  **lead score** shown alongside as extra signal — it does not reorder the list.
- **Radius is fixed to 25 / 50 / 100 miles** — the same options GAF's site offers.
  Verified against the source of truth for 10013: **25→83, 50→173, 100→361**, exact.
- **Geocoding matches GAF exactly.** GAF geocodes a ZIP (e.g. 10013 → `40.7217861,
  -74.0094471`) and computes `distanceinmiles` from that point. Free offline geocoders
  (pgeocode/nominatim/census) land ~0.4 mi off, which flips one contractor at the
  100-mile edge (362 vs 361). We resolve ZIPs in this order: a **curated override table**
  (exact GAF coords, seeded with 10013) → **Google Geocoding** if `GOOGLE_MAPS_API_KEY` is
  set (matches GAF for any ZIP) → offline **pgeocode** fallback. So 10013 matches at all
  radii out of the box; set a Google key for exact parity on arbitrary ZIPs.
- **Pagination is kept** for safety (Coveo caps 100/response); dense results page fully.
- **Company name** comes from the record title (`gaf_contractor_dba` is often empty in
  this index; we fall back to the title / navigation title).
- **No lead "status" field.** Removed — it was our own workflow placeholder (every lead
  defaulted to "new"), not GAF data, so it added noise. Leads now reflect source data plus
  the computed score and insights only.

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
| GAF data source | http://localhost:8000/api/v1/gaf-contractors | — (no client auth) |
| Postgres | localhost:5432 | `sales` / `sales` / db `sales_intel` |

> These are local development defaults only. Production uses managed secrets — see
> the data-management section of `PLAN.md`.
