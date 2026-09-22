# HeatAction SG

[![CI](https://github.com/glentls/heataction-sg/actions/workflows/ci.yml/badge.svg)](https://github.com/glentls/heataction-sg/actions/workflows/ci.yml)

HeatAction SG is a community outreach planning tool for extreme-heat events in Singapore, built for the DAISI 2026 B1 HeatGuard track. It helps a coordinator decide where to send limited outreach teams during a hot period by combining live public weather observations with demographic context, then explains and exports the resulting plan.

This repository contains the local planning application, public weather collectors, an exploratory forecast experiment, Databricks source notebooks, and full project documentation.

## Status

Early-stage prototype under active development. The planning engine, live weather collection, real Singapore demographics/boundaries for a three-area pilot, and coordinator controls (locking, scenario comparison, CSV export) are implemented and tested locally. The full pipeline has also run successfully in a real Databricks workspace: live Bronze/Silver/Gold weather and demographic tables, a Gold priority-plan table built from the same allocation policy as the local app, and a working Databricks App that reads it. That App is currently stopped between demonstrations, and nothing refreshes those tables automatically yet — there is no scheduled job. A policy backtest measures the allocation policy against naive baselines on synthetic data; a coordinator usability-test protocol exists but has not yet been run with a real person. Trained forecasting and field/partner validation are also not yet complete. See [docs/STATUS.md](docs/STATUS.md) for the current, detailed state and [docs/TASKS.md](docs/TASKS.md) for what's next.

## Features

- **Real-area planning pilot** — Ang Mo Kio, Bedok and Jurong West, with official Census 2020 age profiles, all 55 URA Master Plan 2019 planning-area boundaries, and an interactive local SVG map (no external tile service required).
- **Transparent allocation policy** — ranks areas by a heat category and senior-population priority, gated by observation freshness, mapping review status, and a fixed team budget. Every recommendation is explained in plain language.
- **Coordinator controls** — lock a team assignment to a specific area with a recorded reason (persisted and included in exports), and compare two planning scenarios side by side (for example two versus three team slots) to see which areas gain or lose support.
- **Weather history charts** — a per-station chart of recent WBGT readings with observation age and a visually distinguished one-hour forecast point, plus a hover tooltip and a plain-table fallback.
- **Live weather collection** — public WBGT and rainfall observations from data.gov.sg, with raw response snapshots, malformed-record quarantine, and idempotent local storage.
- **CSV export** with full provenance: data mode, source timestamps, population vintage, mapping review status, and lock reasons.
- **Exploratory forecasting** — chronological comparison of a persistence baseline, a time-of-day baseline, and gradient boosting, with results reported honestly as not yet validated for production use.
- **Databricks deployment** — source notebooks for managed Delta ingestion, Unity Catalog demographic/priority tables, and MLflow-tracked evaluation, plus a minimal Databricks App reading the deployed plan table. All executed successfully in a real workspace; see docs/DATABRICKS.md.
- **Policy backtest** — replays historical WBGT data and scores the shipped allocation policy against naive baselines (population-only, heat-only, random, round-robin) under identical budgets, with results and limitations reported honestly; see docs/STATUS.md.

The application currently forecasts by carrying the latest WBGT reading forward for one hour (a **persistence baseline**), clearly labelled as such in the interface. It is not a trained model, and the exploratory ML experiment is not yet used for live inference.

## Getting started

Requires Python 3.11 or newer. No external services or paid API keys are required for the synthetic demo.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m heataction demo
.\.venv\Scripts\python.exe -m heataction serve
```

If `py` is not available, use `python -m venv .venv` instead, provided `python --version` reports 3.11 or newer. If using VS Code, select `.venv` as the Python interpreter to use the included debug configuration and tasks.

### macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m heataction demo
.venv/bin/python -m heataction serve
```

Open http://127.0.0.1:8000 and keep the terminal running. Press Ctrl+C to stop the server. All demo area names, populations and readings are synthetic and clearly labelled as such in the interface.

## Real-area planning pilot

```powershell
.\.venv\Scripts\python.exe -m heataction check-areas
.\.venv\Scripts\python.exe -m heataction ingest --source all
.\.venv\Scripts\python.exe -m heataction serve --mode observed --pilot --port 8001
```

Open http://127.0.0.1:8001. Select an area on the map to inspect its age profile, population vintage, mapped weather station, observation freshness, and assignment explanation. Switch between the senior-population and heat-proxy layers, zoom into an area, or include/exclude a pilot area from the plan. The remaining 52 planning areas provide demographic context only.

The 2020 population figures are historical, not current estimates. Station-to-area mapping has passed a technical review (source identity, coordinate containment, checksum verification) but not field or partner validation; see [docs/DATA.md](docs/DATA.md) for the full mapping methodology and limitations.

## Collecting live weather observations

```powershell
.\.venv\Scripts\python.exe -m heataction ingest --source all
.\.venv\Scripts\python.exe -m heataction serve --mode observed --port 8001
```

Without a reviewed area file, this mode shows a live weather observation inspector without demographic recommendations — synthetic and observed data are never blended. To plan with a custom set of reviewed areas, create the JSON file described in `docs/DATA.md` and run:

```powershell
.\.venv\Scripts\python.exe -m heataction serve --mode observed --areas data/areas_reviewed.json --port 8001
```

Refreshing the browser reads stored observations; rerun `ingest` to fetch new readings.

## What to try

- Change the team budget from 2 to 1 and observe how the assignment changes.
- Exclude an area from the service-area filter and inspect the remaining allocation.
- Adjust the relative weight between senior population count and senior population share.
- Lock an area to a team slot with a recorded reason, then confirm it holds its slot even at a lower budget.
- Use **Compare scenarios** to set two different team budgets (e.g. 2 vs 3 slots) and see which areas gain or lose an assignment.
- Open the recommendation explanation panel and export the plan as a CSV.
- Scroll to **Weather history** and switch between stations to see each one's recent trend, observation age, and forecast point.

## Testing

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions (`.github/workflows/ci.yml`) runs this same suite on every push to `main` and every pull request, across Python 3.11 and 3.12, plus a real-browser check (`tests/browser/main_workflow.mjs`) of the main coordinator workflow — budget changes, locking, scenario comparison, weather history, and CSV export — against the synthetic demo. That browser check is a mechanical correctness check, not usability evidence; see docs/USABILITY_TEST.md for the distinction.

## Optional forecast experiment

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ml]"
.\.venv\Scripts\python.exe -m heataction evaluate --mode demo
```

Compares a persistence baseline, a time-of-day baseline, and gradient boosting using chronological train/validation/test splits. Metrics on synthetic data are a code exercise only; use `--mode observed` once sufficient real weather history has been collected. Reports are written to `artifacts/`.

## Policy backtest

```powershell
.\.venv\Scripts\python.exe -m heataction compare-policies --mode demo --budget 1
```

Replays every observed WBGT timestamp and scores the shipped allocation policy against naive baselines (population-only, heat-only, random, round-robin), reporting how often each one's chosen area was genuinely in the High WBGT category. On the synthetic demo dataset the shipped policy catches 93% of those moments versus 17% for population-only; see docs/STATUS.md for the full numbers and limitations. Reports are written to `artifacts/`.

## Project structure

| Location | Purpose |
|---|---|
| `heataction/sources.py` | Public API access, response normalization and raw snapshots |
| `heataction/geography.py` | Census/URA joins, polygon checks and reviewed pilot mappings |
| `data/reference/observed/` | Official demographic and boundary snapshots, checksums and mapping audit |
| `heataction/storage.py` | Local observation cache, ingestion run log and lock-reason storage |
| `heataction/planner.py` | Priority policy, freshness checks and capacity allocation |
| `heataction/evaluation.py` | Next-hour forecast targets and chronological model comparison |
| `heataction/policy_evaluation.py` | Allocation-policy backtest against naive baselines |
| `heataction/server.py` | Local application API and CSV export |
| `heataction/web/index.html` | Browser interface |
| `heataction/web/map.js` | Interactive local SVG map and area detail panels |
| `heataction/web/chart.js` | Per-station weather-history chart |
| `notebooks/` | Databricks ingestion, Unity Catalog demographic/plan, and MLflow experiment notebooks |
| `databricks_app/` | Databricks App: a read-only view of the deployed Gold plan table |
| `tests/` | Data, allocation and temporal validation checks |
| `tests/browser/main_workflow.mjs` | Real-browser regression check of the main coordinator workflow |
| `.github/workflows/ci.yml` | Runs the test suite and browser check on every push/PR |

## Documentation

| Document | Contents |
|---|---|
| [docs/STATUS.md](docs/STATUS.md) | Current implementation state and what has been verified |
| [docs/TASKS.md](docs/TASKS.md) | Remaining work, in priority order |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Rationale behind major design choices |
| [docs/DATA.md](docs/DATA.md) | Data sources, API contracts, and area-mapping format |
| [docs/DATABRICKS.md](docs/DATABRICKS.md) | Workspace deployment instructions |
| [docs/USABILITY_TEST.md](docs/USABILITY_TEST.md) | Coordinator task-based usability-test protocol |
| [docs/VISION.md](docs/VISION.md) | Full product proposal, including future scope |
| [docs/GITHUB.md](docs/GITHUB.md) | Repository access and how to save changes |
| [AGENTS.md](AGENTS.md) | Working agreement and non-negotiable project constraints |

## Data sources and attribution

- Heat stress (WBGT) and rainfall: [NEA real-time weather API](https://data.gov.sg/datasets/d_87884af1f85d702d4f74c6af13b4853d/view), via data.gov.sg.
- Resident age profiles: [Singapore Census of Population 2020](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view), SingStat.
- Planning-area boundaries: [URA Master Plan 2019](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view).

All datasets are used under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). Population figures reflect the 2020 Census and are not current estimates.

## Scope and limitations

This is a planning-support prototype, not a medical or emergency-response system. Priority scores are planning proxies based on stated policy weights, not individual illness risk assessments or measures of completed outreach. Data mode (synthetic or observed) is always labelled explicitly in the interface and exports. See [docs/STATUS.md](docs/STATUS.md) for what has and has not been verified.
