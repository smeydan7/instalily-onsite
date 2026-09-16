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
├── pages/             route-level screens (Accounts, Leads, Insights)
└── components/        reusable UI pieces
```

State/data fetching uses `@tanstack/react-query`. Keep API types in `src/api/types.ts`
in sync with the backend Pydantic schemas.
