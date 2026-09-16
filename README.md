# Roofing Sales Intelligence Platform

A B2B sales intelligence platform that generates actionable leads and account-planning
insights for the sales team at a roofing distributor. It ingests public data sources,
enriches and scores prospect accounts, and surfaces recommendations that help reps
identify, understand, and engage decision makers.

> **Status:** Skeleton. The data-source-specific ingestion and enrichment logic is
> intentionally stubbed until the concrete public data source(s) are chosen.

## Objectives

- **Intuitive UI** — an account-planning workspace for reviewing pre-generated insights.
- **Robust data management** — store, organize, and retrieve accounts, contacts, leads,
  insights, and the raw records they derive from.
- **Scalable pipeline** — a modular ingest → enrich → score → generate flow that new data
  sources plug into without reworking the core.

## Architecture

```
              GAF contractor directory (Coveo)
                          │
        ┌─────────────────┴──────────────────┐
        │            Pipeline                 │
        │  sources → enrichment → scoring →   │
        │            insight generation       │
        └─────────────────┬──────────────────┘
                          │
                    PostgreSQL
                          │
                    FastAPI (REST)
                          │
                    React SPA (Vite)
```

- **Backend** — FastAPI, SQLAlchemy, Alembic, Pydantic. See `backend/README.md`.
- **Frontend** — React + TypeScript + Vite. See `frontend/README.md`.
- **DB** — PostgreSQL.
- **Data source** — GAF certified-contractor directory via its Coveo search API.
  Live endpoint: `GET /api/v1/gaf-contractors?zip_code=90210`. See `docs/PLAN.md` §4.

## Domain model

| Entity     | Meaning                                                              |
|------------|---------------------------------------------------------------------|
| `Account`  | A prospect company — a GAF-certified roofing contractor.            |
| `Contact`  | A person/channel at an account — the decision maker to engage.      |
| `Lead`     | A scored, actionable opportunity tied to an account.                |
| `Insight`  | A generated recommendation/finding for account planning.           |
| `DataSource` | A registered public source and its ingestion run metadata.        |

## Docs

- [`docs/SETUP.md`](docs/SETUP.md) — set up and run (whole stack, or backend/frontend separately).
- [`docs/PLAN.md`](docs/PLAN.md) — detailed implementation plan (UI, data management, scalable pipeline).
- [`docs/PRESENTATION.md`](docs/PRESENTATION.md) — panel presentation speaker guide.

## Quick start

```bash
# whole stack
docker compose up --build

# or run pieces individually — see backend/README.md and frontend/README.md
```

- API: http://localhost:8000  (docs at `/docs`)
- UI:  http://localhost:5173

## Layout

```
.
├── backend/     FastAPI service + data pipeline
├── frontend/    React SPA
└── docker-compose.yml
```
