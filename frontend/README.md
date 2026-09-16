# Frontend — Sales Intelligence UI

React + TypeScript + Vite SPA. The account-planning workspace where reps review
pre-generated leads and insights.

## Run locally

```bash
cd frontend
npm install
cp .env.example .env        # point VITE_API_BASE_URL at the backend
npm run dev
```

App: http://localhost:5173  (expects the API at `VITE_API_BASE_URL`)

## Layout

```
src/
├── main.tsx            app bootstrap (router + react-query providers)
├── App.tsx             shell + routes
├── api/                typed API client + shared types
├── pages/              route screens: Leads (list), LeadDetail, Accounts, Insights
└── components/         ui.tsx (score/status/rating/state), IngestPanel
```

The Leads page is the centerpiece: ranked leads with filters (status, score, rating,
state, search), a row → lead detail, inline status changes, and an **ingest panel** that
pulls a territory of GAF contractors into the pipeline.

State/data fetching uses `@tanstack/react-query`. Keep API types in `src/api/types.ts`
in sync with the backend Pydantic schemas.
