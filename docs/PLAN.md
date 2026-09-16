# Implementation Plan

A detailed plan for the UI, the backend (data management + scalable pipeline), the
data-source integration, and a phased build order.

**Data source (now known): the GAF certified-contractor directory.** GAF is a major
roofing manufacturer whose public "find a contractor" site lists certified residential
roofing contractors. Those contractors are exactly the distributor's prospects — so
**each GAF contractor becomes an `Account`** in our model. See Section 4 for the full
integration.

Scope note: where a full production build is out of scope for the timeframe, we note the
"good enough now" choice and the "evolve to" target.

---

## 0. Guiding Principles

- **Lead-centric.** The rep's primary job is reviewing generated leads — the whole app
  optimizes for that.
- **Source-agnostic core.** No business logic assumes a specific data source.
- **Pre-compute, then serve.** Heavy work happens in the pipeline offline; the API/UI
  read ready results. This is what makes serving many reps cheap.
- **Traceability.** Every lead and insight records where it came from.
- **Ship the skeleton, evolve the depth.** Build the full shape now; deepen scoring,
  ingestion, and polish incrementally.

---

## 1. Frontend Plan

Goal: a clean, intuitive, visually polished UI whose most important job is letting sales
reps **view the leads the system generates**.

### 1.1 Information architecture

- **Leads (landing page)** — ranked list of generated leads. The core screen.
- **Lead detail** — everything a rep needs to act on one lead.
- **Accounts** — browse prospect companies (secondary).
- **Insights** — cross-account feed of recommendations (secondary).

### 1.2 Leads list — the centerpiece

- Default sort: **score descending** (best-fit leads first).
- Each row shows: score, account name, region, status, a one-line "why" (top insight).
- **Filter bar:** status, score range, region/state, rating, review count.
- **Search:** by account name; and **by ZIP + radius** (natural for GAF — "contractors
  near this branch"), which can drive either a live `/api/gaf-contractors` lookup or a
  filter over pre-computed leads.
- **Sort toggles:** score, rating, review count, distance, recency, name.
- **Status controls:** rep can move a lead through `new → reviewing → qualified →
  engaged → won/lost/dismissed` inline.
- **Pagination / infinite scroll** — server-driven, since lead volume grows.
- **Empty + loading + error states** — first-class, not afterthoughts.

### 1.3 Lead detail — everything in one place

- **Header:** contractor name, score, status control, rating + review count, distance.
- **Why this lead:** the generated insights (opportunity / risk / engagement /
  firmographic), each with its confidence and evidence.
- **Decision makers / contact:** company phone now; named decision makers once enrichment
  lands (see Section 4.5).
- **Account facts:** location, certification type, rating/reviews, GAF profile link,
  source-provided attributes.
- **Rep actions:** change status, (future) add notes, (future) mark outreach.

### 1.4 Visual design

- Design system: a small set of tokens (color, spacing, radius, typography) applied
  consistently. Restrained, professional palette — data-dense but uncluttered.
- Components: table/grid, card, tag/badge (for insight types & lead status), filter
  controls, score indicator, empty/loading/error blocks.
- Accessible: readable contrast, keyboard-navigable, sensible focus states.
- Responsive down to laptop widths; graceful narrower.
- **Evolve to:** a component library (e.g. shadcn/ui or MUI) + Storybook once the
  surface grows; charts/trends on the dashboard.

### 1.5 Frontend tech & data layer

- React + TypeScript + Vite (already scaffolded).
- **@tanstack/react-query** for server state: caching, background refetch, pagination.
- Typed API client mirroring backend schemas (`src/api/types.ts` kept in sync).
- Routing via react-router.
- **Evolve to:** generated client from the backend OpenAPI spec (removes hand-sync);
  optimistic updates for status changes; URL-encoded filter state for shareable views.

### 1.6 Frontend build order

1. Design tokens + shared components (table, card, tag, states).
2. Leads list with server-driven filter/sort/pagination.
3. Lead detail view.
4. Inline status updates.
5. Accounts + Insights secondary pages.
6. Polish pass: spacing, empty states, transitions, responsiveness.

---

## 2. Backend Plan — Data Management

Goal: store, organize, and retrieve data in a way suitable for production, with a clear
evolution path.

### 2.1 Datastore choice

- **PostgreSQL.** Relational fits the core need — ranking, filtering, and joining
  accounts/contacts/leads/insights. Mature, reliable, great tooling.
- **JSON(B) columns** on entities (`attributes`, `evidence`) absorb messy,
  source-specific fields without a migration per source quirk.
- **Why not NoSQL:** our access patterns are relational and query-heavy (sort by score,
  filter by status/region). Postgres + JSONB gives flexibility without giving up SQL.

### 2.2 Schema (already modeled)

- `accounts` — prospect companies (+ JSON `attributes`).
- `contacts` — people at accounts (decision makers).
- `leads` — scored opportunities (score, status), FK to account/contact.
- `insights` — generated recommendations (type, confidence, JSON `evidence`).
- `data_sources` + `ingestion_runs` — source registry + run history.
- Timestamps (`created_at`/`updated_at`) on every table via a mixin.

### 2.3 Access patterns & indexing

- Index the columns reps filter/sort on: `leads.score`, `leads.status`,
  `accounts.name`, `accounts.domain`, `contacts.email`, FKs.
- Pagination is **offset/limit now**, **keyset (cursor) later** for large tables.
- Read paths go through a **service layer** (already present) so query logic is
  centralized and testable.
- **Evolve to:** a repository pattern if query complexity grows; materialized views for
  expensive aggregations.

### 2.4 Data integrity & identity

- **Entity identity / dedup:** identity is **`gaf_contractor_id`** (stable per
  contractor). Add a unique key on it and **upsert** in the pipeline instead of
  create-only — essential because overlapping ZIP-radius searches return the same
  contractor many times.
- **Provenance:** insights/leads carry the source (`gaf`) + `gaf_contractor_id` and the
  GAF profile `uri` that produced them.
- Foreign keys with sensible `ON DELETE` (cascade for children, set-null for optional
  links) — already defined.

### 2.5 Migrations & environments

- **Alembic** for versioned schema changes (configured; generate first migration once
  models settle).
- Secrets via environment / secret manager — never in the DB or repo.
- Separate configs per environment (local / staging / prod) through settings.

### 2.6 Production-readiness roadmap (state these as "future work")

- **Read replicas** for the rep-facing read load; writes to primary.
- **Connection pooling** (PgBouncer) as connection count grows.
- **Caching** (Redis) for hot lead lists and reference data.
- **Soft deletes + audit log** for traceability and recovery.
- **Backups + PITR**, monitoring on slow queries.
- **Partitioning / archival** of old ingestion data and stale leads.
- **Row-level access** if reps/teams must be scoped to their own accounts.

---

## 3. Backend Plan — Scalable Pipeline

Goal: an ingest → enrich → score → generate flow that stays reliable as usage grows to
hundreds/thousands of reps.

### 3.1 Current shape (already scaffolded)

- Four decoupled stages: **sources → enrichment → scoring → insights**, wired by an
  **orchestrator**.
- **Pure stages** (enrich/score/generate) are I/O-free and unit-testable.
- **Source adapters** implement a `fetch` + `normalize` contract; registered in a
  registry. Adding a source is additive.
- **IngestionRun** records status, counts, and errors per run.

### 3.2 From synchronous to scalable

Current orchestrator runs inline (fine for skeleton/demo). Production evolution:

- **Task queue + workers.** Move pipeline execution to a queue (Celery / RQ / Arq).
  The API enqueues; workers process. Scale by adding workers.
- **Per-source, per-batch jobs.** Fan out ingestion into independent units so one slow
  or failing source doesn't block others.
- **GAF fans out naturally by geography.** The source is queried per ZIP + radius, so
  ingestion is a list of `(zip, radius)` jobs — one per distributor branch/territory.
  These parallelize cleanly across workers and are the unit of scheduling and retry.
- **Scheduling.** Cron/beat triggers periodic ingestion per source (e.g. refresh each
  territory's contractors nightly to pick up new/updated ratings and reviews).

### 3.3 Reliability at scale

- **Idempotency.** Re-running a source must not duplicate data → upsert on
  `gaf_contractor_id`. Overlapping ZIP radii returning the same contractor is normal and
  must be safe.
- **Incremental ingestion.** Re-scan territories on a schedule and update changed fields
  (rating, review count) in place; the upsert key keeps it idempotent.
- **Retries + backoff** for transient source/network failures.
- **Dead-letter handling** for records that repeatedly fail, so the run continues.
- **Rate limiting / throttling** to respect source API limits.
- **Batching + bulk writes** to the DB instead of row-by-row inserts.

### 3.4 Serving thousands of reps

- Reads dominate at rep scale. Key move: **pre-compute leads/insights in the pipeline**
  so the rep-facing API just reads ready rows — cheap and fast.
- **Stateless API** → scale horizontally behind a load balancer.
- **Cache** hot lead lists; **read replicas** for query load.
- Heavy generation (incl. any future LLM step) happens **offline in workers**, never on
  the request path.

### 3.5 Observability

- Structured logging (upgrade the current basic logger).
- Metrics: records ingested, run duration, failure rate, queue depth, lead counts.
- Per-run visibility already modeled via `ingestion_runs`; surface it in an admin view.

### 3.6 Pipeline build order

1. Keep the sync orchestrator for the demo (done).
2. Add upsert/identity once the source defines it.
3. Introduce a task queue + worker; move `run_source` behind it.
4. Add incremental ingestion + retries + dead-letter.
5. Add scheduling + metrics.

---

## 4. The Data Source — GAF Contractor Directory (Coveo)

### 4.1 How it works

- GAF's public contractor finder is powered by **Coveo**, an enterprise search engine.
  We talk to Coveo's v2 search API **directly** — no HTML scraping.
- **Flow (already built, `app/api/datasource.py`):**
  1. Translate a US ZIP code to lat/lon **offline** with the `pgeocode` library — no
     external geocoding API, so it stays low-latency.
  2. Inject the coordinates into a Coveo search payload that mimics a browser request.
  3. Set `numberOfResults=100` to **bypass the frontend's 10-item pagination** and pull
     all contractors within the radius in one call.
  4. POST to Coveo with the public authorization token GAF's own frontend ships.
- **Auth note:** the Coveo org id + token are the public tokens from GAF's browser
  frontend — not real secrets. They live in `settings` (config), not hardcoded, so they
  can be rotated/overridden per environment.

### 4.2 The client contract (what the UI calls)

- All complexity (geocoding, search, auth) is **abstracted to the backend**. The UI does
  a plain GET — no headers, keys, or body:

  ```
  GET /api/gaf-contractors                      # defaults: zip 10013, radius 25 mi
  GET /api/gaf-contractors?zip_code=90210       # search near a ZIP
  GET /api/gaf-contractors?zip_code=90210&distance=25   # override radius
  ```

- **Response:** a flat object — `zip_searched`, `coordinates` (lat/lon),
  `total_found` (raw Coveo count), and `results[]` (contractor objects).

### 4.3 Fields we get (and how they map)

| Coveo field | Meaning | Maps to |
|-------------|---------|---------|
| `gaf_contractor_id` | Stable contractor id | **Account identity** (dedup key) |
| `gaf_contractor_dba` | Company name | `Account.name` |
| `gaf_contractor_type` | Certification tier / type | `Account.attributes`, scoring signal |
| `gaf_rating` | Consumer review rating | scoring signal + insight |
| `gaf_number_of_reviews` | Review volume | scoring signal (activity proxy) |
| `gaf_f_city`, `gaf_f_state_code` | Location | `Account.city` / `state` |
| `gaf_phone` | Phone | `Contact` channel |
| `gaf_postal_code` | ZIP | `Account.attributes` |
| `gaf_latitude`, `gaf_longitude` | Coordinates | `Account.attributes` |
| `distanceinmiles` | Distance from origin ZIP | territory signal + insight |
| `uri` | GAF profile URL | provenance / rep reference |

### 4.4 Sales-signal interpretation (drives scoring + insights)

- **High rating + high review count** → established, active contractor → strong lead.
- **Review volume** is a proxy for business size/throughput (more jobs = more material).
- **Distance from a branch ZIP** → territory fit / which branch should own the account.
- **Certification type** → product-line fit.

### 4.5 Honest gaps (call these out in the panel)

- The source gives **company + phone**, not a **named decision maker**. So "engage the
  decision maker" needs a later **enrichment** step (or rep-entered contacts). For now a
  `Contact` holds the company phone; named contacts are future enrichment.
- No firmographics like employee count/revenue — we infer activity from review metrics
  instead, and can enrich later.

### 4.6 Two integration modes

1. **Live passthrough (built):** the UI hits `/api/gaf-contractors` for on-demand search
   by ZIP. Great for "look up contractors near this branch right now."
2. **Pipeline pre-compute (planned):** a `GafContractorSource` adapter reuses the same
   fetch logic to ingest contractors across the distributor's branch ZIPs, dedup by
   `gaf_contractor_id`, score them, generate insights, and **persist leads** — so the
   rep-facing lead list is instant and enriched, not a live API round-trip each time.

### 4.7 Turning it into a pipeline source (next implementation step)

- Subclass `BaseSource` as `GafContractorSource`:
  - `fetch()` → call `search_contractors(zip, radius)` for each configured territory ZIP.
  - `normalize()` → map a contractor object to an `AccountCandidate` (fields per 4.3),
    set `provenance = {"gaf": [gaf_contractor_id]}`, attach a phone `Contact`.
- Register it in `SOURCE_REGISTRY` and add a `data_sources` row.
- Switch persistence from create-only to **upsert on `gaf_contractor_id`** so repeated
  runs (overlapping ZIP radii) don't duplicate accounts.
- Everything downstream (enrichment, scoring, insights, API, UI) already consumes the
  normalized shape — no changes needed there.

---

## 5. Phased Delivery (putting it together)

| Phase | Backend | Frontend | Outcome |
|-------|---------|----------|---------|
| **0 — Skeleton** (done) | API, models, pipeline framework, tests, Docker | UI shell + 3 pages, API client | Runs end-to-end on demo data |
| **1 — Live source** (done) | `/api/gaf-contractors` live Coveo search + pgeocode geocoding | — | Real contractor data reachable via API |
| **2 — Lead experience** | Lead query filters/sort/pagination | Polished leads list + lead detail + inline status; ZIP search | Reps review real leads |
| **3 — Pipeline ingest** | `GafContractorSource` adapter; upsert on `gaf_contractor_id`; score + insights; persist leads | Surface scores/insights from stored data | Pre-computed, enriched leads |
| **4 — Scale hardening** | Task queue + workers (per-territory jobs); incremental ingest; retries; metrics | Loading/error resilience | Reliable under growth |
| **5 — Production depth** | Auth/roles; caching; replicas; audit; backups; contact enrichment | Auth UI, admin/run view, dashboard | Production-ready posture |

For the panel/demo timeframe: **Phases 0–1 are built** (skeleton + live GAF data).
Phase 2–3 are the near-term build; Phases 4–5 we present as designed-and-outlined rather
than fully implemented, which the brief explicitly allows.

---

## 6. Open Questions

Resolved by the GAF source:

- **Account identity** → `gaf_contractor_id`. ✔
- **Contacts** → source gives company + phone only; named decision makers need
  enrichment. ✔ (gap noted, Section 4.5)
- **Top signals** → rating, review count, distance, certification type. ✔

Still open:

- Which **branch/territory ZIP codes** define the distributor's coverage? (drives the
  ingestion job list)
- How often does GAF refresh ratings/reviews? (tunes the schedule)
- Coveo **rate limits** on the public token? (drives throttling / backoff)
- Do reps need **account/team scoping**? (drives access control in the data model)
- Preferred **contact-enrichment source** for named decision makers? (fills the gap)
