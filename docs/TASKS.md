# Tasks

## Next working session

- [x] Verify Windows virtual environment, synthetic demo, local HTTP server and all 16 regression tests (Python 3.13.7; use `python` because the `py` launcher fails).
- [x] Save the project owner's original creation-chat link in README and NEXT_SESSION.
- [x] Verify the observed pilot's browser rendering and controls on desktop and mobile using a separate headless Chrome profile outside the sandbox.
- [x] Run `ingest --source all` from Glen's machine. Verified 30 WBGT and 89 rainfall rows, zero quarantined; observation timestamps recorded in STATUS.md.
- [x] Create the private `glentls/heataction-sg` repository and verify the initial upload; local `main` tracks `origin/main`.
- [ ] Test one historical date for both feeds. Inspect actual returned timestamps and pagination before backfilling.
- [x] Download Census 2020 age data and compatible URA MP2019 polygons; verify joins, missing counts and source checksums.
- [x] Select Ang Mo Kio, Bedok and Jurong West and document technical station/geometry reviews with visible vintage and limitations.
- [ ] Validate station representativeness and service boundaries with a prospective coordinator; technical containment is not field validation.

## Next implementation milestone

- [x] Add all 55 planning-area polygons, demographic/heat layers, three pilot station markers, coverage status and source detail panels.
- [ ] Add a nearest valid rainfall-station mapping and issue-time-safe rainfall features.
- [ ] Run chronological evaluation on observed WBGT and record real results.
- [ ] Add an evaluated forecast artifact and inference path to the app, preserving baseline comparison.
- [x] Add UI controls and reason logging for locked assignments (core/API support exists).
- [x] Add an interactive side-by-side scenario comparison (for example two versus three team slots).
- [x] Add a recent weather-history chart per station, with observation age and a distinguished one-hour forecast point.
- [x] Compare the allocation policy against naive baselines (population-only, heat-only, random, round-robin) under identical budgets, with measured results and limitations (`heataction/policy_evaluation.py`, `python -m heataction compare-policies`).
- [ ] Compare forecast models under identical budget and capacity assumptions (baseline vs. trained model, once real chronological evaluation exists — a different comparison from the allocation-policy backtest above).
- [x] Run the Databricks notebooks in a real workspace (ingestion succeeded; evaluation correctly refuses pending more history; a real `typing_extensions`/mlflow dependency bug was found and fixed).
- [x] Ingest `data/reference/observed/` demographic/boundary snapshots into a Unity Catalog volume and add Gold demographic/priority tables (`notebooks/03_geography_and_plan_databricks.py`).
- [x] Connect a Databricks App to the deployed tables (`databricks_app/`); verified working end-to-end, then stopped to avoid ongoing compute.
- [ ] Schedule Databricks ingestion, and re-running the plan notebook after it, as a recurring Job (deliberately deferred; only one-time manual runs so far, so both Gold tables go stale without a manual rerun).

## Before submission

- [x] Write a coordinator usability-test protocol and verify its tasks are mechanically completable (docs/USABILITY_TEST.md); a scripted walkthrough is not a substitute for the item below.
- [ ] Run docs/USABILITY_TEST.md with a real, prospective coordinator; record what changed.
- [ ] Review synthetic versus observed labels in all screenshots, metrics and exports.
- [ ] Measure usability, model performance and simulation results without claiming health outcomes.
- [ ] Confirm one-page versus official three-slide Round 1 format with organisers.
- [ ] Record exact final submission cutoff and complete member details.
- [ ] Rehearse and record a three-minute demo with explicit live/replay mode.
