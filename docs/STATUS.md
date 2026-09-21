# Project status

Version 0.1.0. Updated 21 September 2026.

## Current milestone

The local app now includes an observed three-area planning pilot with Census 2020 age profiles, matched URA 2019 boundaries and an interactive Singapore map. Live WBGT/rainfall collection succeeds on Glen's machine. Technical station mapping checks are implemented; partner/field validation and Databricks execution remain pending. The next feature milestone is saved scenario comparison and coordinator assignment controls.

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
- Strict observed Census/URA joins with source checksums, three documented station mappings and moved-station gating.
- Interactive local SVG map of all 55 planning areas, demographic and pilot heat layers, age profiles, coverage status and assignment explanations.

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
- The initial sandboxed browser check failed. The observed pilot has since passed real Chrome interaction and desktop/mobile rendering checks outside the sandbox; broader user testing remains pending.
- Databricks notebooks have not been run in a workspace. Catalogue permissions, quotas and source access remain to be confirmed.
- Real population and boundaries are integrated locally. Mapping is limited to three technically reviewed station proxies; automatic nationwide assignment and partner validation are not implemented.
- Rainfall is ingested and displayed but not used by the initial model.
- The app uses persistence only. The optional ML experiment does not deploy a model into the app.
- No user interviews, production deployment, social-impact measurements or competition submission have occurred.

## Next task

Add saved scenario comparison and expose assignment locks with reason logging. Continue collecting observed weather history; historical API access, field validation and Databricks deployment remain separate pending tasks.

## Real-area map milestone, 21 September 2026

- Downloaded official Census 2020 age data and URA MP2019 planning-area GeoJSON into `data/reference/observed/` with dataset IDs, attribution, source timestamps and SHA-256 checksums.
- Verified three prototype links: Ang Mo Kio / S141 (162,280 residents; 35,220 aged 65+), Bedok / S129 (276,990; 53,370), Jurong West / S132 (262,730; 33,730). All counts are Census 2020. Exact source totals and geometric containment are tested; no field validation is claimed.
- Added `check-areas` and `serve --mode observed --pilot --port 8001`. Default demo and observed inspector remain available. The pilot loads the verified references on startup and refuses mixed synthetic mode.
- Added a clickable/keyboard-accessible map with all 55 boundaries, 2020 senior-share and pilot station-heat layers, area zoom, three station markers, age profiles, coverage/freshness status, source IDs and mapping explanations. Other areas are context only. Area details can toggle the existing service-area selection.
- Extended CSV provenance with area/boundary dataset identifiers and mapping review fields. Station displacement over 100 m now blocks allocation for the affected reviewed link.
- All 25 regression tests pass (16 existing, 9 new), including actual source counts, aggregation, missing values, geometry holes, altered snapshots, outside/moved stations, empty weather and HTTP mode isolation. JavaScript syntax checks pass.
- Chrome checks passed for map loading, population counts, selection, keyboard interaction, zoom/reset, heat layer, service-area toggles and clearing/recovering from a failed plan request. Desktop and 390-pixel mobile screenshots were inspected; mobile table overflow was corrected. Evidence is local in ignored `artifacts/pilot-desktop.png` and `artifacts/pilot-mobile.png`.
- Refreshed both live feeds successfully (30 WBGT / 89 rainfall rows processed, zero quarantined). At the browser check around 15:58 SGT all three pilot stations were fresh and Low; zero extra heat-driven slots was correct. These readings are time-specific, not a continuing freshness guarantee.
- Left the pilot server running at http://127.0.0.1:8001, with local logs under `data/runtime/observed/pilot-server.*.log`. Databricks notebooks were not executed and no cloud resources were created.

## Live collection and GitHub connection, 21 September 2026

- Verified the observed SQLite cache after the owner's successful collection: WBGT has 30 rows, latest observation `2026-09-21T07:00:00+00:00` (15:00 SGT); rainfall has 89 rows, latest observation `2026-09-21T07:15:00+00:00` (15:15 SGT).
- Both collection runs completed at `2026-09-21T07:23:23+00:00`, with status `ok` and zero quarantined records. These confirm source access, not forecast accuracy.
- The owner requested a private GitHub repository. Authenticated account verified as `glentls`; target repository is `glentls/heataction-sg`.
- Created [glentls/heataction-sg](https://github.com/glentls/heataction-sg) and verified that GitHub reports it as private. Initial commit `20864fc` uploaded successfully; local `main` tracks `origin/main`.
- Reviewed all 30 staged files and checked for common credential formats, with no matches. Runtime data, virtual environments, artifacts and environment files are excluded. No application code changed during GitHub setup; the previously passing 16 regression tests remain the latest test run.
