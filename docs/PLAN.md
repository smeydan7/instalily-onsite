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

- Default order: **GAF's recommended ranking** (`gaf_rank`) so it matches the public site.
- Each row shows: rank, score, company name, rating/reviews, location.
- **Primary control — ZIP + radius search (built):** a rep types a ZIP, picks a radius
  (**25 / 50 / 100 mi — the same fixed options GAF offers**), and hits Search; the backend
  ingests that territory (GAF → pipeline) and the list **scopes to that ZIP**
  (`?origin_zip=`). "Show all territories" clears the scope. This is the main way reps
  drive the tool. **Defaults to 10013 (New York) on open** and self-seeds it on first run.
- **Refine within scope:** score range, min number of ratings, company-name search.
- **Column sorting (built):** click a table header to sort the full result set
  server-side — **Score**, **Company** (alphabetical), or **Rating**; click again to flip
  direction. **#** returns to GAF's recommended order (the default). Location isn't sorted.
- **Scoping model:** each account stores the `origin_zip` that surfaced it
  (last-write-wins). Good enough now; a future many-to-many (a lead can belong to several
  overlapping searched ZIPs) is noted in §4.
- **Pagination / infinite scroll** — server-driven, since lead volume grows.
- **Empty + loading + error states** — first-class, not afterthoughts.

### 1.3 Lead detail — everything in one place

- **Header:** contractor name, score, rating + review count, distance.
- **Why this lead:** the generated insights (opportunity / risk / engagement /
  firmographic), each with its confidence and evidence.
- **Decision makers / contact:** company phone now; named decision makers once enrichment
  lands (see Section 4.5).
- **Account facts:** location, certification type, rating/reviews, GAF profile link,
  source-provided attributes.
- **Rep actions (future):** add notes, mark outreach, save/shortlist.

### 1.4 Visual design

- Design system: a small set of tokens (color, spacing, radius, typography) applied
  consistently. Restrained, professional palette — data-dense but uncluttered.
- Components: table/grid, card, tag/badge (for insight types), filter
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
  URL-encoded filter/scope state for shareable views.

### 1.6 Frontend build order

1. Design tokens + shared components (table, card, tag, states).
2. Leads list with server-driven filter/sort/pagination.
3. Lead detail view.
4. ZIP search + scope, default territory.
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
  filter by rating/region). Postgres + JSONB gives flexibility without giving up SQL.

### 2.2 Schema (already modeled)

- `accounts` — prospect companies (+ JSON `attributes`).
- `contacts` — people at accounts (decision makers).
- `leads` — scored opportunities (score), FK to account/contact.
- `insights` — generated recommendations (type, confidence, JSON `evidence`).
- `data_sources` + `ingestion_runs` — source registry + run history.
- Timestamps (`created_at`/`updated_at`) on every table via a mixin.

### 2.3 Access patterns & indexing

- Index the columns reps filter/sort on: `leads.score`, `accounts.gaf_rank`,
  `accounts.origin_zip`, `accounts.state`, `accounts.rating`, `accounts.name`, FKs.
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
- **LLM insights (OpenAI):** rule-based insights are written at ingest, then **upgraded to
  LLM-authored insights on the first lead-detail view and cached** (`insight_service`).
  Lazy-by-design so an LLM call is spent only on leads a rep opens — cost tracks usage, not
  catalog size — and it falls back to rule-based if the key is unset or a call fails.

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
  1. Translate a US ZIP code to lat/lon **matching GAF's own geocoder**: a curated
     override table (exact GAF coords, seeded with 10013) → Google Geocoding if a key is
     set → offline `pgeocode` fallback. Matching GAF's coordinate is what makes the counts
     identical at every radius (verified 10013: 25→83, 50→173, 100→361).
  2. Inject the coordinates into a Coveo payload that **exactly replicates GAF's own
     site query** — same pipeline plus `tab=defaultTab` and
     `context.sortingStrategy=gafrecommended-initial`. This returns the identical set and
     ordering the public site shows (verified: 10013/25 mi → 83 results, first ten match
     position-for-position).
  3. **Paginate** through all matches (100 per page) until the full set is retrieved,
     bounded by a hard cap (1000).
  4. POST to Coveo with the public authorization token GAF's own frontend ships.

We store each contractor's position (`gaf_rank`) and order the lead list by it, so the UI
mirrors GAF's ranking. The computed lead score is shown alongside as extra signal and does
not reorder the list.
- **Auth note:** the Coveo org id + token are the public tokens from GAF's browser
  frontend — not real secrets. They live in `settings` (config), not hardcoded, so they
  can be rotated/overridden per environment.

### 4.2 The client contract (what the UI calls)

- All complexity (geocoding, search, auth) is **abstracted to the backend**. The UI does
  a plain GET — no headers, keys, or body:

  ```
  GET /api/v1/gaf-contractors                      # defaults: zip 10013, radius 25 mi
  GET /api/v1/gaf-contractors?zip_code=90210       # search near a ZIP
  GET /api/v1/gaf-contractors?zip_code=90210&distance=25   # override radius
  ```

- **Response:** a flat object — `zip_searched`, `coordinates` (lat/lon),
  `total_found` (raw Coveo count), and `results[]` (contractor objects).

### 4.3 Fields we get (and how they map)

| Coveo field | Meaning | Maps to |
|-------------|---------|---------|
| `gaf_contractor_id` | Stable contractor id | **Account identity** (dedup key) |
| result `title` / `gaf_navigation_title` | Company name (`gaf_contractor_dba` is often null) | `Account.name` |
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

### 4.6 Two integration modes (both built)

1. **Live passthrough:** the UI can hit `/api/v1/gaf-contractors` for on-demand search by
   ZIP. Raw, real-time look-up near a branch.
2. **Pipeline pre-compute:** the `GafContractorSource` adapter reuses the same Coveo
   integration to ingest contractors across the distributor's branch ZIPs, dedup by
   `gaf_contractor_id`, score them, generate insights, and **persist leads** — so the
   rep-facing lead list is instant and enriched, not a live API round-trip each time.

### 4.7 The pipeline source (built)

- `app/pipeline/sources/gaf_source.py` — `GafContractorSource(BaseSource)`:
  - `fetch()` → `gaf_coveo.search_sync(zip, radius)` for each configured territory ZIP,
    yielding one `RawRecord` per contractor.
  - `normalize()` → maps a contractor to an `AccountCandidate` (fields per 4.3), attaches
    a company-phone `Contact`, sets `provenance = {"gaf_contractors": [id], ...}`.
- Registered in `SOURCE_REGISTRY`; the orchestrator get-or-creates its `data_sources` row
  and records each `IngestionRun`.
- Persistence is **upsert on (`source_key`, `external_id`) = (`gaf_contractors`,
  `gaf_contractor_id`)**. Re-runs update contractor fields, score, and `gaf_rank` in place;
  derived insights are regenerated. Verified: re-running the same ZIP keeps the lead count
  flat (no duplicates).
- Everything downstream (enrichment, scoring, insights, API, UI) consumes the normalized
  shape unchanged.

### 4.8 ZIP scoping (built) & its evolution

- A rep-entered ZIP + radius is the primary UX. On search we ingest that radius and store
  `origin_zip` on each account, so the lead list filters to `?origin_zip=<zip>`.
- **Each ZIP search is authoritative.** After a run, the orchestrator **reconciles** the
  ZIP's scope — contractors previously tagged to that ZIP but not in the new result set are
  deleted. So changing the radius correctly shrinks/grows the list instead of unioning
  stale results. Verified: 10013 at r25→83, r10→12, r2→1, back to r25→83.
- **Last-write-wins caveat:** if the same contractor is surfaced by two overlapping ZIP
  searches, its `origin_zip` reflects the most recent one. Fine for distinct territories.
- **Evolve to:** a `search`/`territory` table with a many-to-many link to accounts, so a
  contractor can belong to every ZIP whose radius covers it, and searches become
  first-class, auditable objects.

### 4.9 Shared integration module

Coveo access lives in `app/integrations/gaf_coveo.py` (geocode, payload, `search_async`
for the endpoint, `search_sync` for the pipeline) so the live API and the pipeline share
one implementation. The endpoint (`app/api/datasource.py`) is a thin wrapper.

---

## 5. Phased Delivery (putting it together)

| Phase | Backend | Frontend | Outcome |
|-------|---------|----------|---------|
| **0 — Skeleton** ✅ | API, models, pipeline framework, tests, Docker | UI shell + pages, API client | Runs end-to-end |
| **1 — Live source** ✅ | `/api/v1/gaf-contractors` live Coveo search + pgeocode | — | Real contractor data via API |
| **2 — Lead experience** ✅ | Lead filters/search; GAF-rank ordering; nested account; lead detail | Polished leads list + detail + ZIP search/scope | Reps review real leads |
| **3 — Pipeline ingest** ✅ | `GafContractorSource`; upsert on `gaf_contractor_id`; score + insights; persist leads; run tracking | Trigger ingest from UI; surface scores/insights | Pre-computed, enriched leads |
| **4 — Scale hardening** | Task queue + workers (per-territory jobs); incremental ingest; retries; metrics | Loading/error resilience | Reliable under growth |
| **5 — Production depth** | Auth/roles; caching; replicas; audit; backups; contact enrichment | Auth UI, admin/run view, dashboard | Production-ready posture |

Phases 0–3 are **built and verified end-to-end** (live GAF ingest → scored leads → UI).
Phases 4–5 we present as designed-and-outlined rather than fully implemented, which the
brief explicitly allows. Current pipeline execution uses FastAPI `BackgroundTasks`; the
orchestrator entry point (`run_source_background`) is shaped to drop behind a real task
queue with no call-site changes.

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
