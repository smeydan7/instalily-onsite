# Backend — Sales Intelligence API

FastAPI service plus the data pipeline that turns public source records into scored
leads and account-planning insights.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # edit DATABASE_URL if needed
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Layout

```
app/
├── main.py            app factory, middleware, router wiring
├── core/              config, logging (cross-cutting)
├── api/v1/            versioned REST endpoints
├── db/                SQLAlchemy engine, session, declarative base
├── models/            ORM models (persisted domain entities)
├── schemas/           Pydantic request/response models
├── services/          business logic between API and DB
└── pipeline/          ingest → enrich → score → generate insights
    ├── sources/       one adapter per public data source (stubbed)
    ├── enrichment/    fill/augment records
    ├── scoring/       lead scoring
    └── orchestrator.py  runs a full pipeline pass
```

## Migrations

Alembic is configured but no migrations exist yet — generate the first once the
models settle:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Tests

```bash
pytest
```
