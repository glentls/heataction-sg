# Changelog

## Databricks demographic tables and App - 22 September 2026

- Added `notebooks/03_geography_and_plan_databricks.py`: uploads the reviewed Census/URA/mapping snapshots to a Unity Catalog volume, rebuilds the pilot via the same validation as the local app, and writes `heataction_silver.area_demographics`, `heataction_silver.pilot_mapping_audit`, and a `heataction_gold.area_priority_plan` table materialised by calling `heataction.planner.build_plan` directly.
- Found and fixed a real bug: writing the plan table failed with `CANNOT_DETERMINE_TYPE` whenever every area was stale (an expected, ongoing state, not a fluke) because Spark cannot infer a type from all-null columns; fixed with an explicit schema.
- Built and deployed `databricks_app/`, a minimal Databricks App (plain `http.server`, no new framework) that authenticates as its own service principal and renders the live Gold plan table. Verified it end-to-end with an authenticated request, then stopped it, since an App consumes compute continuously while a one-time job run does not.

## First Databricks deployment - 22 September 2026

- Executed the ingestion notebook for real in a Databricks Free Edition workspace: created and verified live Bronze/Silver/Gold Unity Catalog tables (30 WBGT / 89 rainfall rows, 30 fresh persistence forecasts), matching local collection counts.
- Executed the evaluation notebook, found and fixed a real `typing_extensions`/mlflow dependency conflict in the Databricks Runtime, then confirmed it correctly refuses to run with a clear error until at least 7 days of observed history exist.
- Deliberately used one-time manual job runs only (no recurring schedule), so no ongoing compute cost was introduced.

## Weather history charts - 22 September 2026

- Added a bounded, indexed history query and an `/api/history` endpoint, replacing a full-table scan for chart data.
- Added a per-station weather-history chart (local inline SVG, no library) showing recent WBGT trend, observation age, and a visually and textually distinguished one-hour persistence forecast point, with hover tooltip and a table fallback.
- Passed 29 regression tests (27 existing, 2 new) and real-headless-Chrome interaction checks; fixed a transparent-hit-area pointer-events bug found during that check.

## Lock controls and scenario comparison - 21 September 2026

- Added coordinator lock/unlock controls per area, requiring a saved, nonempty reason; reasons persist server-side in SQLite and appear in the plan, recommendation explanations and CSV export.
- Added an `/api/locks` endpoint (`GET`/`POST`/`DELETE`) and rejected `locked` plan/export requests for areas without a saved reason.
- Added a side-by-side scenario comparison view (for example two versus three team slots) showing which areas gain or lose an assignment, with slot and contact-capacity totals.
- Added a "clear all locks" recovery control for when a locked area becomes ineligible between refreshes.
- Passed 27 regression tests (25 existing, 1 new storage test, 1 new HTTP integration test) and real-headless-Chrome interaction checks with no JavaScript exceptions or mobile overflow.

## Real-area map pilot - 21 September 2026

- Integrated attributed Census 2020 and URA MP2019 snapshots with checksum validation and strict planning-area joins.
- Added the Ang Mo Kio, Bedok and Jurong West pilot, documented station proxy reviews, containment validation and moved-station protection.
- Added an interactive map of all 55 planning areas, demographic/heat layers, age profiles, station locations, source details, coverage status and area selection controls.
- Added `check-areas` and observed `--pilot` startup, expanded CSV provenance, and preserved synthetic mode isolation.
- Passed 25 regression tests and real-browser desktop/mobile checks; fixed narrow-screen table overflow.

## GitHub connection - 21 September 2026

- Created the private `glentls/heataction-sg` GitHub repository, pushed the initial source commit, connected local `main` to `origin/main`, and added instructions for saving future changes.
- Extended environment-file exclusions; runtime observations, demo data, artifacts and the virtual environment remain local.
- Verified successful live WBGT/rainfall collection in the local cache and recorded counts and timestamps in STATUS.md.

## Local startup verification - 21 September 2026

- Repaired the Windows virtual environment with Python 3.13.7 and documented the `python` fallback for the failing `py` launcher.
- Generated 4,033 synthetic observations, passed all 16 regression tests and JavaScript syntax validation, and verified the running local server's planning and CSV endpoints.
- Recorded the headless browser failure and remaining manual visual check. Application code and Databricks delivery architecture are unchanged.

## 0.1.0 - 21 September 2026

- Added a runnable local app with explicit synthetic and observed modes.
- Added real public WBGT/rainfall collectors, raw snapshots, record quarantine and idempotent local upserts.
- Added transparent planning priorities, service-area filtering, team budget, freshness checks and CSV exports.
- Added optional chronological comparison of persistence, time-of-day and gradient boosting forecasts.
- Added Databricks Delta ingestion and MLflow evaluation source notebooks for workspace testing.
- Added project documentation, VS Code tasks/debug settings and regression checks.
- Real demographic ingestion, map, trained app inference and Databricks-hosted UI remain subsequent milestones.
