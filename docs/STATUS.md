# Project status

Version 0.1.0. Updated 21 September 2026.

## Current milestone

The local first iteration is implemented. It demonstrates the planning flow with clearly labelled synthetic data, and live WBGT and rainfall collection has succeeded on Glen's machine. The next implementation milestone is verified demographic ingestion and geographic joins.

## Implemented

- Local browser application with capacity settings, service-area filters, explanations and CSV export.
- A deterministic synthetic demonstration isolated from observed data.
- Public WBGT and rainfall collectors, optional date/pagination handling, raw snapshots and malformed-record quarantine.
- Idempotent SQLite upserts for local development, with source-correction handling.
- Persistence forecasts and transparent demographic priority policy.
- Freshness gate, missing-data status, fixed reference cohort and budget-constrained allocation.
- Core/API support for locked assignments. The first UI does not expose lock controls.
- Optional baseline and gradient-boosting experiment with exact next-hour labels, chronological splits and station metrics.
- Databricks source notebooks for Delta ingestion and MLflow evaluation.
- VS Code tasks, debug configuration, tests and documentation.

## Verified here

- Python modules and source notebooks compile.
- 16 regression tests pass, including parsing frozen real public WBGT and rainfall responses.
- Local HTTP app starts. The homepage, budget changes, empty selection, invalid-budget response and CSV export were checked through HTTP requests.
- The optional model comparison runs to completion on synthetic data. Its metrics are not evidence of real forecast performance.
- JavaScript syntax was checked separately.
- Test environment: Python 3.12.14 and scikit-learn 1.8.0. Frozen source-contract checks accepted 30 WBGT rows and 89 rainfall rows with no quarantined records.

## Windows startup verification, 21 September 2026

- Repaired the existing `.venv` using `python -m venv .venv` with Python 3.13.7. The `py` launcher reports `No installed Python found!`; README documents the working fallback.
- Ran `.\.venv\Scripts\python.exe -m heataction demo`: 4,033 synthetic observations prepared in `data/runtime/demo`.
- All 16 regression tests passed on this machine. Browser JavaScript syntax also passed using Node.
- Started the local demo server at http://127.0.0.1:8000. HTTP checks passed for the homepage, synthetic labels, budgets 2/1/0, empty selection, area filtering, demographic weight, invalid budget, missing route and CSV export with provenance. The default plan assigns two slots with 20 assumed contacts.
- Headless Chrome was attempted, but its GPU process failed with Windows access-denied exit code `-1073741790`; no rendered-page verification is claimed. Manual browser inspection remains pending.
- Saved the owner-provided creation-chat link in README and NEXT_SESSION. Retrieval of the shared conversation failed, so its contents have not been reviewed.
- No application code changes were required. Live ingestion, optional ML dependencies and Databricks execution were outside this startup verification.

## Not yet verified or implemented

- Direct Python outbound access timed out in the original validation environment. Live collection has since succeeded on Glen's computer as recorded below; Databricks source access still needs verification.
- Historical API date access, completeness and pagination need deployment smoke tests.
- Initial validation had no browser executable. This Windows machine has Chrome, but the headless check failed as recorded above. Actual browser rendering and interactive layout should be checked when opening the app locally.
- Databricks notebooks have not been run in a workspace. Catalogue permissions, quotas and source access remain to be confirmed.
- No real population table is integrated. No actual planning-area map or automatic spatial mapping is implemented.
- Rainfall is ingested and displayed but not used by the initial model.
- The app uses persistence only. The optional ML experiment does not deploy a model into the app.
- No user interviews, production deployment, social-impact measurements or competition submission have occurred.

## Next task

Continue with Census/URA ingestion and reviewed geographic mappings. Historical weather access and manual browser inspection also remain pending.

## Live collection and GitHub preparation, 21 September 2026

- Verified the observed SQLite cache after the owner's successful collection: WBGT has 30 rows, latest observation `2026-09-21T07:00:00+00:00` (15:00 SGT); rainfall has 89 rows, latest observation `2026-09-21T07:15:00+00:00` (15:15 SGT).
- Both collection runs completed at `2026-09-21T07:23:23+00:00`, with status `ok` and zero quarantined records. These confirm source access, not forecast accuracy.
- The owner requested a private GitHub repository. Authenticated account verified as `glentls`; target repository is `glentls/heataction-sg`.
- Repository preparation is in progress. Runtime data, virtual environments, artifacts and environment files are excluded. GitHub upload is not yet verified.
