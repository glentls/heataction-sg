# Changelog

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
