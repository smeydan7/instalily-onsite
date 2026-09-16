# Panel Presentation Guide

Speaker notes for presenting the design and app. Concise, scannable point form; each
`##` is roughly one slide / talking beat. Sections 6–9 map the brief's objectives to
exactly **how each was achieved**.

---

## 1. The Problem

- Roofing distributor's sales team plans accounts manually.
- Reps spend hours researching prospects across scattered public data.
- Hard to know **who** to call, **why now**, and **what to say**.
- Result: slow prospecting, missed opportunities, inconsistent outreach.

---

## 2. The Solution — in one line

- A B2B sales intelligence platform that **pre-generates ranked, explained leads** from
  public data, so reps **identify, understand, and engage** decision makers fast — review
  instead of research.

---

## 3. How the Whole App Works — start to finish (plain English)

Follow one rep's click:

1. **Rep opens the app.** It loads with New York (ZIP 10013) already showing ranked leads.
2. **Rep enters a ZIP + radius** (25/50/100 mi) and hits **Search** — their branch's area.
3. **Behind the scenes**, the backend asks GAF's contractor directory for every certified
   roofing contractor in that area.
4. **The pipeline processes them:** cleans each record, adds signals (rating, reviews,
   distance), scores each as a lead, and writes a few plain-English **insights**.
5. **Everything is saved** to a database, de-duplicated so re-searching never doubles up.
6. **The rep sees a ranked list** — same order as GAF's own site — with a fit score.
7. **Rep clicks a lead** → a detail page: the contractor's profile, how to reach them, and
   *why* they're worth a call (the insights).
8. **Rep searches another ZIP** anytime; each search is that area's authoritative list.

> One line: **public data in → ranked, explained leads out → reviewed in a clean UI.**

---

## 4. Who It's For

- **Primary user:** sales reps reviewing leads during account planning.
- **Scale target:** hundreds to thousands of reps.
- **Core job:** identify → understand → engage the right decision makers, fast.

---

## 5. Architecture (high level)

```
GAF directory (Coveo)  →  Pipeline  →  PostgreSQL  →  FastAPI  →  React UI
                        ingest·enrich·score·insights
```

- **Frontend:** React + TypeScript (Vite).
- **Backend:** FastAPI (Python), SQLAlchemy, Alembic.
- **Data store:** PostgreSQL.
- **Pipeline:** modular, stage-based, source-agnostic.
- **Data source:** GAF certified-contractor directory via its Coveo search API.

---

## 6. ✅ Objective 1 — Intuitive UI (how we achieved it)

**Goal:** reps can view the leads the system generates.

- **Lead-first design:** the landing page *is* the ranked lead list — no setup, opens on
  10013 and self-seeds it.
- **One primary action:** type a ZIP, pick a radius (25/50/100), Search. That's the whole
  mental model.
- **Ranked and explained:** each row shows GAF-rank position, a **fit score** (color
  pill), rating + review count, and location.
- **Sortable:** click a header to sort the full list by **Score**, **Company** (A–Z), or
  **Rating** (click again to reverse); **#** restores GAF's recommended order.
- **Scoped by search:** entering a ZIP scopes the list to that area; "show all
  territories" clears it. Refine with score / min-number-of-ratings / company search.
- **Lead detail page:** contractor profile, contact, and the generated **insights**
  ("why this lead"), plus the GAF profile link.
- **Polished + resilient:** consistent design system, first-class loading / empty / error
  states, responsive down to laptop widths.
- **Proof:** opens on 10013 → 83 leads, Allied Brothers Home Corporation first — matching
  GAF's own ordering.

---

## 7. ✅ Objective 2 — Robust Data Management (how we achieved it)

**Goal:** store, organize, retrieve data; production-suitable.

**Built now:**
- **PostgreSQL** — relational, reliable, strong at the ranking/filtering leads need.
- **Clear schema** — `accounts`, `contacts`, `leads`, `insights`, `data_sources`,
  `ingestion_runs`; timestamps on every row.
- **Flexible where messy** — JSON columns (`attributes`, `evidence`) absorb source-specific
  fields without a migration per quirk.
- **Indexed for the real queries** — `gaf_rank`, `origin_zip`, `state`, `rating`,
  `review_count`, `score`, plus foreign keys.
- **Identity & dedup** — upsert on `(source_key, external_id)` = `gaf_contractor_id`, so
  overlapping searches never duplicate a contractor.
- **Authoritative scopes** — re-searching a ZIP **reconciles** it (stale contractors
  removed), so the data always reflects the latest search.
- **Provenance** — every lead/insight traces to its source id + GAF profile URL.
- **Schema versioning** — Alembic migrations configured (dev can auto-create for speed).

**→ Evolve to full production (we were time-limited here):**
- **Read replicas** for the rep read load; writes to primary.
- **Connection pooling** (PgBouncer) as connections grow.
- **Redis cache** for hot lead lists / reference data.
- **Soft-deletes + audit log** instead of hard deletes; full change history.
- **Backups + point-in-time recovery**, slow-query monitoring, alerting.
- **Partitioning / archival** of old ingestion runs and cold leads.
- **Multi-tenant access control** (row-level security) to scope reps/teams to their book.
- **A first-class `search`/`territory` table** (many-to-many to accounts) so a contractor
  can belong to several overlapping searches — replacing today's last-write-wins `origin_zip`.

---

## 8. ✅ Objective 3 — Scalable Pipeline, explained end-to-end

**Goal:** a pipeline designed for scale (hundreds→thousands of reps).

### The pipeline, start to finish
1. **Trigger** — a ZIP search (or a scheduled territory job) calls the orchestrator with a
   `source_key` + config (`zips`, `radius`).
2. **Geocode** — ZIP → lat/lon, matching GAF's own geocoder (override table → Google key →
   offline `pgeocode` fallback).
3. **Ingest (source adapter)** — `GafContractorSource` builds GAF's exact Coveo query and
   **paginates** through every contractor in the radius. Each becomes a normalized
   `AccountCandidate`. *New source = one new adapter class; nothing downstream changes.*
4. **Enrich** — pure functions add derived signals (e.g. review-activity band). No I/O.
5. **Score** — transparent weighted score (0–100) over rating, review volume, proximity.
6. **Generate insights** — rule-based recommendations at ingest, **upgraded to LLM
   (OpenAI) insights on first lead-detail view** and cached (see slide 9).
7. **Persist** — upsert the account, sync contact, upsert the primary lead, regenerate
   insights, record `gaf_rank`.
8. **Reconcile & record** — make the ZIP authoritative (remove stale), and log the
   `IngestionRun` (status, records, errors).

### Why it scales
- **Decoupled stages** — each is small and independently replaceable/scalable; pure
  compute (enrich/score/insights) separated from I/O.
- **Pre-compute, then serve** — heavy work runs in the pipeline; the rep-facing API just
  reads ready rows. This is the key to serving many reps cheaply.
- **Geographic fan-out** — ingestion is a list of `(zip, radius)` jobs (one per branch),
  which parallelize cleanly across workers.
- **Idempotent & safe** — upsert on stable id; re-runs don't duplicate; commit-per-record
  is restart-safe.
- **Queue-ready** — the entry point (`run_source_background`) is shaped to move from
  FastAPI background tasks to a real task queue (Celery/RQ/Arq) with no call-site changes.
- **Stateless API** — scale horizontally behind a load balancer; the DB scales separately.

---

## 9. ✅ AI-powered insights (built)

- **What it does:** an **LLM (OpenAI)** writes the rep-facing insights on each lead —
  concrete talking points to **identify, understand, and engage** the decision maker
  (why-now signals, how to open, product/volume angles), grounded in the contractor's real
  data (rating, reviews, certification, proximity).
- **Where the rep sees it:** open a lead → the "Why this lead" cards are AI-authored,
  tagged **AI**, with evidence/provenance stored.
- **Scale-smart design — lazy + cached:** we do **not** call the LLM for every contractor
  at ingest. Insights are generated on **first lead-detail view** and cached, so we only
  spend an LLM call on leads a rep actually opens — this is what keeps it affordable across
  thousands of reps.
- **Safe fallback:** the score is deterministic; if the LLM key is unset or a call fails,
  the lead keeps its rule-based insights. No hard dependency, no broken page.
- **Clean seam:** insight generation is its own stage — swapping models (or moving to a
  learned scorer) is a local change, not a rewrite.

---

## 10. The Data Source — GAF via Coveo (and exact-match)

- GAF (major roofing manufacturer) publishes a **certified contractor directory** — those
  contractors are the distributor's prospects.
- We skip HTML scraping and call **Coveo**, the search engine behind GAF's site, directly.
- **Exact replication:** GAF's pipeline + `tab=defaultTab` +
  `context.sortingStrategy=gafrecommended-initial` → identical set and order as the site.
- **Geocoding matched to GAF** so counts are exact at every radius. Verified for 10013:
  **25→83, 50→173, 100→361**, first ten position-for-position.
- **Per contractor:** name, rating, review count, city/state, phone, distance,
  certification type, stable id, GAF profile URL.
- **Honest gap:** the source gives company + phone, **not a named decision maker** — a
  future enrichment step (surfaced, not hidden).

---

## 11. Key Design Decisions (defend these)

- **Modular pipeline stages** — swap/scale any stage independently; AI drops into one.
- **Source adapter pattern** — new data sources are additive, not invasive.
- **Exact-match the source** — replicate GAF's query + geocoding so reps trust the data.
- **Pre-compute over on-demand** — keeps the rep UI fast at scale.
- **JSON attribute columns** — absorb messy public data without constant migrations.
- **Provenance everywhere** — trust and traceability for every generated lead/insight.

---

## 12. What's Built vs. What's Planned

- **Built + verified end-to-end:** exact-match GAF source → pipeline (ingest, enrich,
  score, insights, upsert, reconcile, run tracking) → scored/ranked leads → polished rep
  UI (ZIP search, scoping, filters, lead detail).
- **Demo proof:** search a ZIP → leads in GAF's exact order and count; change radius →
  set updates correctly; re-run → no duplicates.
- **Planned (designed, outlined):** task queue + workers, incremental ingest, LLM insight
  generation, named-decision-maker enrichment, auth/roles, caching/replicas.

---

## 13. Closing

- Turns scattered public data into a ranked, explained, ready-to-action lead list.
- Reps **identify** (ranked leads), **understand** (score + insights), **engage**
  (contact + talking points) — the exact brief.
- Production-minded foundation, built to grow from one team to thousands of reps.

---

## Likely Panel Questions — quick answers

- **"Is it really AI?"** — Yes: an OpenAI LLM writes the rep-facing insights per lead
  (lazy + cached), grounded in the contractor's real data. The deterministic score is a
  safe fallback if the LLM is unavailable.
- **"Isn't calling an LLM per contractor expensive at scale?"** — We don't. Insights are
  generated only on the leads a rep opens (first view), then cached — so cost tracks
  actual usage, not catalog size.
- **"Why call Coveo directly instead of scraping?"** — Clean structured fields, and we can
  replicate GAF's exact query; no brittle HTML parsing.
- **"How do you know the data matches GAF?"** — Same pipeline + `tab`/`context`, and
  geocoding matched to GAF's coordinates. Verified 10013: 25→83, 50→173, 100→361.
- **"How do you engage a decision maker with only a company + phone?"** — Honest gap; we
  surface company + phone now and plan named-contact enrichment.
- **"How do you avoid duplicates / stale data?"** — Upsert on `gaf_contractor_id`; each ZIP
  search reconciles its scope (removes stale). Verified re-runs stay flat.
- **"Why Postgres, not NoSQL?"** — Relational fits ranking/filtering; JSON columns cover
  flexible source fields. Best of both.
- **"How does it scale to thousands of reps?"** — Pre-compute + cache + read replicas;
  stateless API; pipeline fans out per territory ZIP across workers.
- **"What would you build next?"** — Task queue, LLM insights, contact enrichment,
  auth/roles, caching/replicas. Detailed in `PLAN.md`.
