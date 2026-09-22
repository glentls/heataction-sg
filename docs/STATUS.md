# Project status

Version 0.1.0. Updated 22 September 2026.

## Current milestone

The local app now includes an observed three-area planning pilot with Census 2020 age profiles, matched URA 2019 boundaries and an interactive Singapore map, coordinator lock controls with recorded reasons, a side-by-side scenario comparison view, and a per-station weather-history chart with observation age and a distinguished one-hour forecast point. Live WBGT/rainfall collection succeeds on Glen's machine. Technical station mapping checks are implemented. Databricks deployment now includes real Bronze/Silver/Gold weather tables, demographic and pilot-mapping Silver tables, a Gold area-priority-plan table materialised by the same allocation policy as the local app, and a working (currently stopped) Databricks App reading that plan table live over Unity Catalog. A new policy backtest (`heataction/policy_evaluation.py`) measures the shipped allocation policy against naive baselines on synthetic data, and a coordinator usability-test protocol exists but has not yet been run with a real coordinator. A scheduled recurring Databricks job and partner/field/usability validation remain pending. The next milestone is either scheduling the Databricks ingestion, running the usability protocol with a real coordinator, or real chronological WBGT evaluation once enough observed history exists.

## Implemented

- Local browser application with capacity settings, service-area filters, explanations and CSV export.
- A deterministic synthetic demonstration isolated from observed data.
- Public WBGT and rainfall collectors, optional date/pagination handling, raw snapshots and malformed-record quarantine.
- Idempotent SQLite upserts for local development, with source-correction handling.
- Persistence forecasts and transparent demographic priority policy.
- Freshness gate, missing-data status, fixed reference cohort and budget-constrained allocation.
- Coordinator lock controls with a required, server-persisted reason per locked area, shown in the plan, explanations and CSV export.
- A side-by-side scenario comparison view (for example two versus three team slots) showing which areas gain or lose an assignment.
- A per-station weather-history chart (bounded, indexed query, not a full-table scan) showing recent WBGT readings, observation age, and a visually and textually distinguished one-hour persistence forecast point, with a hover tooltip and a plain-table fallback.
- Optional baseline and gradient-boosting experiment with exact next-hour labels, chronological splits and station metrics.
- Databricks source notebooks for Delta ingestion, Unity Catalog demographic/plan materialisation, and MLflow evaluation, all executed successfully in a real workspace (see the dated entries below).
- A Databricks App (`databricks_app/`) that queries the Gold area-priority-plan table live over a SQL warehouse and renders it as a read-only, explicitly labelled page; deployed and verified working, then stopped to avoid ongoing compute.
- VS Code tasks, debug configuration, tests and documentation.
- Strict observed Census/URA joins with source checksums, three documented station mappings and moved-station gating.
- Interactive local SVG map of all 55 planning areas, demographic and pilot heat layers, age profiles, coverage status and assignment explanations.
- A policy backtest (`heataction/policy_evaluation.py`, `python -m heataction compare-policies`) that replays every observed timestamp in a dataset and scores the shipped allocation policy, and four naive baselines, against a ground-truth "is any area genuinely in the High WBGT category right now" signal.
- A coordinator usability-test protocol (`docs/USABILITY_TEST.md`): six concrete tasks with success criteria, written for someone else to administer with a real coordinator.

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
- The ingestion, geography/plan, and evaluation notebooks have all now been run successfully in a real workspace (below). The evaluation notebook has not yet produced a report, since observed history is still far short of the 7-day gate; that is its correct behaviour, not a defect. A scheduled recurring ingestion job has not been created.
- Real population and boundaries are integrated locally. Mapping is limited to three technically reviewed station proxies; automatic nationwide assignment and partner validation are not implemented.
- Rainfall is ingested and displayed but not used by the initial model.
- The app uses persistence only. The optional ML experiment does not deploy a model into the app.
- No user interviews, production deployment, social-impact measurements or competition submission have occurred. A usability-test protocol now exists (docs/USABILITY_TEST.md) but has not been run with a real coordinator; only a scripted functional walkthrough of the same six tasks has been done (below), which checks the mechanism works, not that a naive user finds it usable.

## Next task

Run the coordinator usability protocol (docs/USABILITY_TEST.md) with a real, naive participant — this is the one piece of evidence in this project that genuinely cannot be produced by more engineering. Separately: schedule the Databricks ingestion as a recurring Lakeflow Job, and once enough observed history exists, run chronological evaluation on observed WBGT and add an evaluated forecast artifact/inference path preserving the persistence baseline comparison. Historical API access and field validation remain separate pending tasks.

## Policy backtest and usability protocol, 22 September 2026

- Added `heataction/policy_evaluation.py` and `python -m heataction compare-policies`: replays every observed WBGT timestamp in a dataset and scores the shipped allocation policy (calling `heataction.planner.build_plan` directly, not a reimplementation) against four naive baselines — population-only (ignores weather), heat-only (ignores demographics), random, and round-robin — using a ground truth of "is any area genuinely in the High WBGT category right now."
- Ran it on the synthetic demo dataset (14 days, 1,344 timesteps, budget=1 team slot): 216 timesteps (16.1%) had at least one genuinely High area. The shipped policy caught 93.1% of them (201/216); the population-only baseline caught only 17.1% (37/216); a pure heat-chasing oracle baseline caught 100% by construction; random caught 55.1%; round-robin caught 52.3%. Full numbers: `artifacts/policy_comparison_demo.json` (git-ignored, reproducible via the command above).
- The shipped policy's gap versus the heat-only oracle (93.1% vs 100%) is a real, explainable trade-off, not noise: the policy also weighs demographic need, so on the small number of timesteps where a high-demographic area is only Moderate while a low-demographic area is High, it sometimes still favours the Moderate area. That is the intended equity/reactivity trade-off the weighting was designed to make, now quantified for the first time rather than asserted.
- At budget=2, the shipped policy also revealed a property the naive baselines don't have: it only used its full budget when conditions warranted it (1,054 assignments across 1,344 timesteps, i.e. it left a slot unused whenever fewer than 2 areas had positive priority), while every naive baseline always spent its full budget regardless of conditions (2,688 assignments each, budget × timesteps).
- Limitations, stated in the tool's own output and repeated here: synthetic data only (DECISIONS.md #002 — this demonstrates the evaluation method, not a real-world impact number); the ground truth uses the same `heat_category` threshold the policy itself uses, not an independent severity measure; only 3 areas and 1 station per area, so this says nothing about performance at city scale; recall/capacity are planning proxies, not counts of people actually helped.
- Added `docs/USABILITY_TEST.md`: a six-task coordinator protocol (reduce capacity, explain a recommendation, lock a commitment, compare team sizes, check weather freshness, export a handoff CSV) written for someone else to administer with a real, naive participant, with explicit success criteria and a note not to average outcomes into a single score with only one or two participants.
- Ran a scripted functional walkthrough of the same six tasks via real headless Chrome (`artifacts/check-usability-tasks.mjs`, not committed): all six completed without errors (correct area identified when the budget dropped, an explanation was readable, a lock survived a budget cut, the comparison correctly named a gaining area, the weather-history summary stated both trend window and observation age, and the CSV export returned a real 200 response with data rows). This is explicitly an engineering completeness check, not usability evidence — it cannot reveal confusion, hesitation, or misreadings the way a real first-time coordinator would, and the protocol document says so.
- Added 4 unit tests for the policy backtest (`tests/test_policy_evaluation.py`) using a crafted two-area fixture with a known correct answer, independent of the demo dataset. All 33 regression tests pass locally (Python 3.13.7).

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

## Lock controls and scenario comparison, 21 September 2026

- Added a `lock_reasons` SQLite table (`heataction/storage.py`) and an `/api/locks` endpoint (`GET`/`POST`/`DELETE` in `heataction/server.py`) so a coordinator's reason for pinning an area to a team slot is saved locally, keyed by area, and survives a server restart.
- `/api/plan` and `/api/export` now reject a `locked` area that has no saved reason (400, explicit message), and attach each area's saved reason and record time to every plan row and CSV export.
- Added a Lock/Unlock control to each eligible area row in `heataction/web/index.html`: locking requires typing a nonempty reason (client- and server-validated, 300-character limit); unlocking keeps the saved reason for reuse, with a separate "delete reason" action. A locked area's reason also appears in the recommendation explanations.
- Added a "Compare scenarios" panel: two independent budget/contacts/weight settings (for example two versus three team slots) sharing the same service-area selection and locks, fetched via two parallel `/api/plan` calls and rendered as a gained/lost/unchanged diff with slot and contact-capacity totals. No new backend endpoint was needed for this.
- If a previously locked area becomes invalid (for example its data goes stale after a refresh), the app fails closed with a clear error and a "clear all locks" recovery control, rather than silently dropping the lock.
- Added 1 storage unit test and 1 subprocess HTTP integration test (spawns `serve --mode demo` and exercises `/api/locks` plus the plan/export validation and data). All 27 regression tests pass locally (Python 3.13.7). JavaScript syntax passed via `node --check`.
- Verified interactively with real headless Chrome (`artifacts/check-locks-browser.mjs`, not committed): lock validation, save/reason round-trip and pre-fill on reopen, unlock, explanation text, and the two-scenario diff, all with zero JavaScript exceptions; 390px width produced no horizontal overflow. Evidence is local only, matching the project's prior browser-check pattern.
- Not yet done: only the latest reason per area is kept (no history/audit trail across relocks), and no field/coordinator usability testing of the new controls.

## Weather history charts, 22 September 2026

- Added a bounded, indexed `history()` query (`heataction/storage.py`, keyed on the existing `(source, station_id, observed_at)` primary key) and an `/api/history` endpoint (`station_id`, `source`, `limit`, capped at 1000) instead of loading the full observation table for chart data.
- Added a per-station weather-history chart to the "Source observations" panel: a hand-rolled inline SVG line chart (`heataction/web/chart.js` + `chart.css`, no charting library or CDN, consistent with the existing map's approach) showing recent WBGT readings, a filled marker and direct label for the latest observation with its age in minutes, and a dashed connector to a hollow marker and label for the one-hour persistence-baseline forecast point, textually distinguished as "(forecast)" everywhere it appears.
- Added a hover crosshair and tooltip (pointer events on a transparent hit rectangle) and a keyboard/screen-reader-reachable "View as table" fallback listing every point, so no information is hover-only.
- A station selector lists every WBGT station with data; a "Limited history" note appears below five observations, and an explicit message appears when a station has none yet, rather than rendering a misleading empty chart.
- Added 1 storage unit test and 1 subprocess HTTP integration test (bounds, chronological order, unknown station, and validation of `source`/`limit`/missing `station_id`). All 29 regression tests pass locally (Python 3.13.7).
- Verified interactively with real headless Chrome (`artifacts/check-history-browser.mjs`, not committed): station population, forecast marker and label, table fallback, station switching, and hover-tooltip behaviour (fixed one bug found this way: the transparent SVG hit rectangle needed explicit `pointer-events:all`, since a CSS-transparent fill is otherwise not hit-tested). No JavaScript exceptions; no 390px-width overflow.
- Not yet done: the review that prompted this noted the observed database currently holds very little real history (collection has only been run a few times), so the chart's real-data view will stay sparse until ingestion runs regularly; no scheduler was added in this pass.

## First Databricks deployment, 22 September 2026

- Installed the Databricks CLI (v1.17.0) and authenticated via OAuth browser login to Glen's Databricks Free Edition workspace (`https://dbc-739b29bf-8050.cloud.databricks.com`, workspace id `7474651204213756`). No token was ever shared in chat.
- Uploaded the `heataction` package as plain workspace files (confirmed `object_type: FILE`, not converted to notebooks) and both source notebooks to `/Workspace/Users/glentanlusheng@gmail.com/heataction-sg/`.
- Ran `01_ingest_databricks` as a one-time job submission (`catalog=workspace`, live fetch, no `raw_dir`/`date`) against the `Serverless Starter Warehouse`. It succeeded and created real Unity Catalog tables: `workspace.heataction_bronze.weather_responses` (1 raw response per source), `workspace.heataction_silver.weather_observations` (30 WBGT rows, 89 rainfall rows — the same counts as the local machine's most recent live collection), and the `workspace.heataction_gold.current_persistence_forecasts` view (30 fresh station forecasts, `model_version = persistence_v0_1`). Verified all three by querying them directly through the SQL Statement Execution API, not just by trusting the job's "success" status.
- Ran `02_evaluate_databricks` the same way. First attempt failed with `ImportError: cannot import name 'Sentinel' from 'typing_extensions'`: the Databricks Runtime's preinstalled `typing_extensions` predates what mlflow's `pydantic` dependency needs. Fixed by pinning `typing_extensions>=4.13` in the notebook's `%pip install` line and adding an explicit `dbutils.library.restartPython()` (`notebooks/02_evaluate_databricks.py`). Re-ran: it now correctly reaches and raises `ValueError: Collect at least 7 days of usable history before this exploratory experiment` — the intended gate from `heataction/evaluation.py`, working as designed against real (currently very sparse) observed history. This is a genuine bug found and fixed by real execution, not a hypothetical.
- Scope for this pass was deliberately limited to a manual run plus table verification (the user's choice): no recurring Databricks Job/schedule was created, so there is no ongoing compute cost. All runs used `jobs submit` (one-time), which does not appear in the Jobs UI and does not retry.
- Not yet done: the `data/reference/observed/` demographic/boundary snapshots have not been uploaded or ingested into Bronze; no Gold area-priority/planning tables exist; no Databricks App or dashboard is connected to any of this; no scheduled collection.

## Databricks demographic tables and App, 22 September 2026

- Created a managed Unity Catalog volume `workspace.heataction_bronze.reference` and uploaded the reviewed Census/URA/mapping snapshots from `data/reference/observed/` into it.
- Added `notebooks/03_geography_and_plan_databricks.py`: reruns `heataction.geography.build_pilot` (the same checksum/containment/join validation as locally) against that volume, then writes `heataction_silver.area_demographics` (all 55 boundaries, 3 flagged `pilot`, 7 with genuinely unavailable — not zeroed — resident counts) and `heataction_silver.pilot_mapping_audit` (the technical review record for the 3 pilot links).
- The same notebook then pulls the latest Silver WBGT readings and calls `heataction.planner.build_plan` directly — the identical allocation function the local app serves, not a reimplementation — writing the result to `heataction_gold.area_priority_plan` (overwritten each run; represents "the current plan", matching the existing Gold forecast view's framing).
- First run hit a real bug: `spark.createDataFrame` failed with `CANNOT_DETERMINE_TYPE` because every pilot area was stale at that moment (a real, expected state — not a bug in the plan itself) and `forecast_wbgt`/`priority` were `None` for every row, leaving Spark unable to infer a column type. Fixed by giving the write an explicit `StructType` schema instead of relying on inference; this is a permanent fix, since some areas being stale/missing at read time is expected, ongoing behaviour, not a one-off. Re-ran ingestion immediately afterward and re-ran this notebook: with fresh data, all three pilot areas showed `status = Ready`, real WBGT values (24.8-27.8 °C, all category Low at that hour, so zero slots assigned) — verified by direct SQL query, not by trusting job success alone.
- Built and deployed a Databricks App (`databricks_app/app.py`, `app.yaml`, `requirements.txt`): a plain `http.server`-based page (no new framework, consistent with the rest of the project) that authenticates as the app's own service principal (`databricks.sdk.core.Config` + `databricks-sql-connector`, no user token involved) and queries `heataction_gold.area_priority_plan` live over the `Serverless Starter Warehouse`. Granted the app's service principal `CAN_USE` on that warehouse and `USE`/`SELECT` on the `heataction_gold` and `heataction_silver` schemas.
- Verified the deployed app end-to-end with an authenticated HTTP request (HTTP 200, correct plan rows, correct labels) before stopping it. Per the project's own "avoid continuously running compute" principle (docs/DATABRICKS.md), the app was stopped immediately after verification — creating and deploying it does consume compute while running, unlike the one-time `jobs submit` runs used elsewhere. It can be restarted with `databricks apps start heataction-plan`.
- Not yet done: no scheduled Job re-runs ingestion or the plan notebook automatically, so both Gold tables the app reads will go stale until someone reruns them manually; the app has no auto-refresh/polling of its own either (it only re-queries on page load).

## Live collection and GitHub connection, 21 September 2026

- Verified the observed SQLite cache after the owner's successful collection: WBGT has 30 rows, latest observation `2026-09-21T07:00:00+00:00` (15:00 SGT); rainfall has 89 rows, latest observation `2026-09-21T07:15:00+00:00` (15:15 SGT).
- Both collection runs completed at `2026-09-21T07:23:23+00:00`, with status `ok` and zero quarantined records. These confirm source access, not forecast accuracy.
- The owner requested a private GitHub repository. Authenticated account verified as `glentls`; target repository is `glentls/heataction-sg`.
- Created [glentls/heataction-sg](https://github.com/glentls/heataction-sg) and verified that GitHub reports it as private. Initial commit `20864fc` uploaded successfully; local `main` tracks `origin/main`.
- Reviewed all 30 staged files and checked for common credential formats, with no matches. Runtime data, virtual environments, artifacts and environment files are excluded. No application code changed during GitHub setup; the previously passing 16 regression tests remain the latest test run.
