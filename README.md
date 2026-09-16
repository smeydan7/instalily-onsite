# InstaLILY Roofing Sales Intelligence

An AI-powered B2B sales intelligence platform that generates ranked, explained leads for a
roofing distributor's sales team. It pulls GAF-certified roofing contractors (the
distributor's prospects) from GAF's public directory, scores each as a lead, and — when a
rep opens one — uses an LLM to write concrete talking points to **identify, understand, and
engage** the decision maker.

> **Status:** Built and verified end-to-end. Search a ZIP → ranked leads in GAF's exact
> order; open a lead → AI-written insights. The GAF data source, pipeline, database, LLM
> insights, and UI are all working.

## Objectives (all met)

- **Intuitive UI** — a focused rep workspace: search a ZIP, see the ranked lead list, open
  a lead for its detail + AI insights.
- **Robust data management** — PostgreSQL stores accounts, contacts, leads, insights, and
  ingestion runs; upsert/dedup on the contractor's GAF id, per-ZIP reconciliation,
  provenance, Alembic migrations. (Production-evolution path in `docs/PLAN.md`.)
- **Scalable pipeline** — a modular ingest → enrich → score → store flow, source-agnostic
  and queue-ready. Heavy work is pre-computed so the rep-facing API just reads ready rows.

## Architecture

```
              GAF contractor directory (Coveo)
                          │
        ┌─────────────────┴──────────────────┐
        │   Pipeline: ingest · enrich ·       │
        │             score · store (leads)   │
        └─────────────────┬──────────────────┘
                          │
                    PostgreSQL ──────── OpenAI LLM
                          │             (writes insights
                    FastAPI (REST)       when a rep opens a lead)
                          │
                    React SPA (Vite)
```

- **Backend** — FastAPI, SQLAlchemy, Alembic, Pydantic. See `backend/README.md`.
- **Frontend** — React + TypeScript + Vite. See `frontend/README.md`.
- **DB** — PostgreSQL.
- **Data source** — GAF certified-contractor directory via its Coveo search API. We
  replicate GAF's exact query + geocoding, so counts and order match the public site
  (10013: 25 mi → 83, 50 → 173, 100 → 361). Live endpoint:
  `GET /api/v1/gaf-contractors?zip_code=90210`. See `docs/PLAN.md` §4.
- **AI insights** — OpenAI writes the per-lead sales insights, generated lazily on first
  lead-detail view and cached. Reads `OPENAI_API_KEY` (from the repo-root `.env`).

## Domain model

| Entity         | Meaning                                                              |
|----------------|---------------------------------------------------------------------|
| `Account`      | A prospect company — a GAF-certified roofing contractor.            |
| `Contact`      | A way to reach an account (company phone today; named decision maker is future enrichment). |
| `Lead`         | A scored (0–100), actionable opportunity tied to an account.        |
| `Insight`      | A per-lead recommendation ("why this lead") — AI-written, rule-based fallback. |
| `DataSource`   | A registered source the pipeline pulls from (e.g. GAF).             |
| `IngestionRun` | History of one pipeline run (status, records, errors).             |

## Docs

- [`docs/SETUP.md`](docs/SETUP.md) — set up and run (whole stack, or backend/frontend separately).
- [`docs/PLAN.md`](docs/PLAN.md) — detailed implementation plan (UI, data management, scalable pipeline).
- [`docs/PRESENTATION.md`](docs/PRESENTATION.md) — panel presentation speaker guide.

## Quick start

```bash
docker compose up --build
```

- UI:  http://localhost:5173  (opens on New York / ZIP 10013)
- API: http://localhost:8000  (docs at `/docs`)

> No `docker compose` plugin, or want to run pieces individually? See `docs/SETUP.md` —
> it covers a no-Compose path and running backend/frontend separately. For AI insights,
> put `OPENAI_API_KEY` in the repo-root `.env`.

## Layout

```
.
├── backend/     FastAPI service + data pipeline + integrations (GAF/Coveo, OpenAI)
├── frontend/    React SPA (Leads list + Lead detail)
├── docs/        SETUP · PLAN · PRESENTATION
└── docker-compose.yml
```
