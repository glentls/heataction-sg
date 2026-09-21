# Tasks

## Next working session

- [x] Verify Windows virtual environment, synthetic demo, local HTTP server and all 16 regression tests (Python 3.13.7; use `python` because the `py` launcher fails).
- [x] Save the project owner's original creation-chat link in README and NEXT_SESSION.
- [ ] Open http://127.0.0.1:8000 in a browser and inspect rendering and controls; headless Chrome could not complete in the restricted environment.
- [x] Run `ingest --source all` from Glen's machine. Verified 30 WBGT and 89 rainfall rows, zero quarantined; observation timestamps recorded in STATUS.md.
- [x] Create the private `glentls/heataction-sg` repository and verify the initial upload; local `main` tracks `origin/main`.
- [ ] Test one historical date for both feeds. Inspect actual returned timestamps and pagination before backfilling.
- [ ] Download the Census age table and URA polygons. Implement and check demographic parsing.
- [ ] Select pilot areas and review area-to-station mappings. Keep data vintage visible.

## Next implementation milestone

- [ ] Add actual planning-area map and geographic coverage indicators.
- [ ] Add a nearest valid rainfall-station mapping and issue-time-safe rainfall features.
- [ ] Run chronological evaluation on observed WBGT and record real results.
- [ ] Add an evaluated forecast artifact and inference path to the app, preserving baseline comparison.
- [ ] Add UI controls and reason logging for locked assignments (core/API support exists).
- [ ] Compare planning policies under identical budget and capacity assumptions.
- [ ] Run the Databricks notebooks in the final workspace.
- [ ] Add Gold demographic/priority tables and Databricks-hosted interface.

## Before submission

- [ ] Interview/test with a prospective coordinator; record what changed.
- [ ] Review synthetic versus observed labels in all screenshots, metrics and exports.
- [ ] Measure usability, model performance and simulation results without claiming health outcomes.
- [ ] Confirm one-page versus official three-slide Round 1 format with organisers.
- [ ] Record exact final submission cutoff and complete member details.
- [ ] Rehearse and record a three-minute demo with explicit live/replay mode.
