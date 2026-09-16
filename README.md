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
                 public data sources (TBD)
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

## Domain model

| Entity     | Meaning                                                              |
|------------|---------------------------------------------------------------------|
| `Account`  | A prospect company (contractor, builder) the rep may sell to.        |
| `Contact`  | A person at an account — the decision maker to engage.              |
| `Lead`     | A scored, actionable opportunity tied to an account.                |
| `Insight`  | A generated recommendation/finding for account planning.           |
| `DataSource` | A registered public source and its ingestion run metadata.        |

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
