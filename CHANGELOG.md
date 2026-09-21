# Changelog

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
- Linked the owner-provided original creation conversation in README and continuation notes; shared-chat retrieval was unavailable.
- Recorded the headless browser failure and remaining manual visual check. Application code and Databricks delivery architecture are unchanged.

## 0.1.0 - 21 September 2026

- Added a runnable local app with explicit synthetic and observed modes.
- Added real public WBGT/rainfall collectors, raw snapshots, record quarantine and idempotent local upserts.
- Added transparent planning priorities, service-area filtering, team budget, freshness checks and CSV exports.
- Added optional chronological comparison of persistence, time-of-day and gradient boosting forecasts.
- Added Databricks Delta ingestion and MLflow evaluation source notebooks for workspace testing.
- Added project documentation, VS Code tasks/debug settings and regression checks.
- Real demographic ingestion, map, trained app inference and Databricks-hosted UI remain subsequent milestones.
