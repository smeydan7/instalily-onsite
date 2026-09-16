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
├── main.py            app factory, middleware, router wiring, dev table-create
├── core/              config, logging (cross-cutting)
├── api/
│   ├── datasource.py  live GAF endpoint (/api/v1/gaf-contractors)
│   └── v1/            versioned REST endpoints (leads, accounts, insights, pipeline)
├── integrations/
│   └── gaf_coveo.py   shared Coveo access (geocode + search, sync & async)
├── db/                SQLAlchemy engine, session, declarative base, model registry
├── models/            ORM models (persisted domain entities)
├── schemas/           Pydantic request/response models
├── services/          business logic between API and DB
└── pipeline/          ingest → enrich → score → generate insights
    ├── sources/       adapters: gaf_source (real), example_source (demo)
    ├── enrichment/    fill/augment records
    ├── scoring/       lead scoring
    ├── insights/      recommendation generation
    └── orchestrator.py  runs a full pipeline pass (upsert + run tracking)
```

## Key endpoints

- `GET  /api/v1/leads` — ranked leads (filters: status, min_score, min_rating, state, search).
- `GET  /api/v1/leads/{id}` — lead detail (account + contacts + insights).
- `PATCH /api/v1/leads/{id}` — update lead status.
- `GET  /api/v1/gaf-contractors?zip_code=&distance=` — live GAF search passthrough.
- `POST /api/v1/pipeline/run` — ingest a source (body: `{source_key, config:{zips,radius}}`).
- `GET  /api/v1/pipeline/runs` — ingestion run history.

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
