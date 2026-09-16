# Panel Presentation Guide

Speaker notes for presenting the design and app. Every point is concise and
scannable. Present top to bottom; each `##` is roughly one slide / talking beat.

---

## 1. The Problem

- Roofing distributor's sales team plans accounts manually.
- Reps spend hours researching prospects across scattered public data.
- Hard to know **who** to call, **why now**, and **what to say**.
- Result: slow prospecting, missed opportunities, inconsistent outreach.

---

## 2. The Solution — in one line

- A B2B sales intelligence platform that **pre-generates actionable leads and
  account-planning insights** from public data, so reps review instead of research.

---

## 3. What It Does

- Pulls **certified roofing contractors** from GAF's public directory (our prospects).
- Enriches, scores, and ranks them into **leads**.
- Generates **insights** — recommendations and talking points for engaging them.
- Presents everything in a clean UI built for **account planning**.

---

## 4. Who It's For

- **Primary user:** sales reps reviewing leads during account planning.
- **Scale target:** hundreds to thousands of reps.
- **Core job:** identify → understand → engage the right decision makers, fast.

---

## 5. Architecture (high level)

```
GAF directory (Coveo) → Pipeline → PostgreSQL → FastAPI → React UI
                       (ingest·enrich·score·generate)
```

- **Frontend:** React + TypeScript (Vite).
- **Backend:** FastAPI (Python), SQLAlchemy, Alembic.
- **Data store:** PostgreSQL.
- **Pipeline:** modular, stage-based, source-agnostic.
- **Data source:** GAF contractor directory via its Coveo search API (see next slide).

---

## 5A. The Data Source — GAF via Coveo

- GAF (major roofing manufacturer) publishes a **certified contractor directory**.
- Those contractors = the distributor's prospects.
- We skip HTML scraping — we call **Coveo**, the search engine behind GAF's site, directly.
- **Flow:** ZIP → offline geocode (pgeocode) → Coveo search → 100 results in one call
  (bypasses the site's 10-per-page limit).
- **Per contractor we get:** name, rating, review count, city/state, phone, distance,
  certification type, stable id.
- **Exact replication:** using GAF's pipeline + `tab`/`context.sortingStrategy`, we return
  the *same set in the same order* as the public site (verified 10013/25 mi → 83, first
  ten position-for-position).
- **UI just calls** `GET /api/v1/gaf-contractors?zip_code=90210` — no auth/keys client-side.

---

## 5B. Turning Contractors into Leads

- Each contractor → an **Account**; identity = `gaf_contractor_id` (dedup key).
- **Signals we score on:** high rating + many reviews = active, established contractor =
  strong lead. Distance = territory fit. Certification = product fit.
- **Honest gap:** source gives company + phone, not a named decision maker → that's a
  future **enrichment** step. (Good thing to raise before the panel does.)

---

## 6. Domain Model (the vocabulary)

- **Account** — a prospect company.
- **Contact** — a person at an account (the decision maker).
- **Lead** — a scored, actionable opportunity tied to an account.
- **Insight** — a generated recommendation for account planning.
- **DataSource / IngestionRun** — registered sources + run history.

---

## 7. The Pipeline — designed for scale

- Four decoupled stages: **ingest → enrich → score → generate insights**.
- Each stage is small and replaceable; pure logic separated from I/O.
- New data source = one adapter class, zero core changes.
- Runs tracked per source (status, records, errors) for reliability.
- Scales out via a task queue and workers (design ready; see slide 10).

---

## 8. The UI — built around the rep

- **ZIP-driven:** a rep types a ZIP + radius → the system pulls & scores that territory's
  contractors → the ranked lead list scopes to that ZIP.
- Refine within scope by score, min number of ratings, company name.
- **Order matches GAF's site** (their recommended ranking), with our lead score alongside.
- Lead detail = contractor profile + contact + insights.
- Clean, uncluttered, visually polished — review at a glance, act quickly.

---

## 9. Data Management — production-minded

- PostgreSQL: reliable, relational, strong querying for lead ranking.
- Normalized core entities + JSON columns for source-specific fields.
- Schema versioned with Alembic migrations.
- **Provenance tracked** — every lead/insight traces back to source records.
- Future: read replicas, caching, partitioning, soft-deletes/audit (see plan).

---

## 10. Scalability Story (the panel will ask)

- **Pipeline:** queue + horizontal workers; idempotent, incremental, retried.
- **Serving thousands of reps:** reads dominate — scale with replicas + caching.
- Pre-compute leads/insights offline so the UI is always fast.
- Stateless API → scale horizontally behind a load balancer.
- Bounded by the DB, which we scale independently.

---

## 11. What's Built vs. What's Planned

- **Built + verified end-to-end:** live GAF source → pipeline ingest (`GafContractorSource`,
  upsert on `gaf_contractor_id`) → scored leads with insights → polished rep UI (ranked
  leads list, filters, lead detail, one-click "pull a territory").
- **Demo proof:** search a ZIP, leads appear in GAF's exact order and count; re-run
  doesn't duplicate.
- **Planned (designed, not built):** task queue + workers, incremental ingest, contact
  enrichment (named decision makers), auth/roles, caching/replicas.
- Adapter design let GAF flow through **without reworking anything downstream**.

---

## 12. Key Design Decisions (defend these)

- **Modular pipeline stages** — swap/scale any stage independently.
- **Source adapter pattern** — new sources are additive, not invasive.
- **JSON attribute columns** — absorb messy public data without constant migrations.
- **Pre-compute over on-demand** — keeps the rep-facing UI fast at scale.
- **Provenance everywhere** — trust and traceability for generated insights.

---

## 13. Closing

- Turns scattered public data into a ranked, explained, ready-to-action lead list.
- Saves rep time, standardizes outreach, surfaces the right decision makers.
- Built to grow from one team to thousands of reps.

---

## Likely Panel Questions — quick answers

- **"Why call Coveo directly instead of scraping the site?"** — Faster and more robust:
  we get clean structured fields, and one call returns 100 results vs. the site's 10 per
  page. No brittle HTML parsing.
- **"How do you geocode without an external API?"** — `pgeocode` translates ZIP → lat/lon
  offline from a local postal DB. Low-latency, no third-party dependency.
- **"You only get a company + phone — how do you engage a decision maker?"** — Honest
  gap. We surface the company + phone now and plan a contact-enrichment step to add named
  decision makers. Called out in the plan.
- **"How do you avoid duplicate contractors?"** — Overlapping ZIP searches repeat records;
  we upsert on the stable `gaf_contractor_id`, so re-runs are idempotent.
- **"Why Postgres, not NoSQL?"** — Relational fits ranking/filtering leads; JSON columns
  cover flexible source fields. Best of both.
- **"How does it scale to thousands of reps?"** — Reads dominate; pre-compute + cache +
  replicas. API is stateless; pipeline fans out per territory ZIP across workers.
- **"How do you trust a generated insight?"** — Every insight stores its evidence and
  provenance (source + `gaf_contractor_id` + GAF profile link).
- **"What next with more time?"** — Pipeline ingest, contact enrichment, task queue,
  auth/roles, UI polish. All in `PLAN.md`.
