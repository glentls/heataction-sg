# HeatAction SG

A working first iteration for DAISI B1 HeatGuard. It includes a local planning app, public weather collectors, an exploratory forecast experiment, Databricks source notebooks and project documentation.

**Private repository:** [glentls/heataction-sg](https://github.com/glentls/heataction-sg). See `docs/GITHUB.md` for saving future changes.

**Start here:** run the synthetic demo, understand the planning flow, then verify live collection on your computer. All demo names, counts and readings are fictional. This is not the final competition submission.

**Project origin:** [Original HeatAction creation chat](https://chatgpt.com/share/e/6ab0d893-c718-83ec-bae1-df575a54ab4b) (provided by the project owner; its contents were not accessible during local verification). See `docs/NEXT_SESSION.md` for the saved continuation context.

## Open in VS Code (Windows)

1. Extract the ZIP and open the `heataction-sg` folder with **File > Open Folder**.
2. Open **Terminal > New Terminal**. Ensure the terminal is in the folder containing this README.
3. Check that Python 3.11 or newer is installed: `py --version`.
4. Run the following commands in PowerShell. No package installation or environment activation is needed for the demo.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m heataction demo
.\.venv\Scripts\python.exe -m heataction serve
```

5. Open http://127.0.0.1:8000 in your browser. Keep the terminal running. Press Ctrl+C to stop it.

If `py` is unavailable or reports `No installed Python found!`, but `python --version` works and is 3.11+, use `python -m venv .venv` for the first command. This fallback was verified on this Windows machine with Python 3.13.7. If neither works, install Python from https://www.python.org/downloads/ and reopen VS Code.

Select `.venv` as the Python interpreter in VS Code if using the included debug configuration and tasks. The command line works independently of the editor extensions.

## Real-area map and planning pilot

The observed pilot includes **Ang Mo Kio, Bedok and Jurong West**, official Census 2020 age profiles, and all 55 URA Master Plan 2019 planning-area boundaries. The reference snapshots ship with the project; map rendering needs no external tile service or extra packages.

```powershell
.\.venv\Scripts\python.exe -m heataction check-areas
.\.venv\Scripts\python.exe -m heataction ingest --source all
.\.venv\Scripts\python.exe -m heataction serve --mode observed --pilot --port 8001
```

Open http://127.0.0.1:8001. Select an area to inspect its age profile, population vintage, mapped station, weather freshness and assignment explanation. Switch between senior population share and pilot station heat, zoom to an area, or exclude a pilot area from the plan. The other 52 areas provide demographic context only.

The 2020 population counts are historical, not current estimates. Pilot mapping checks verify station identities, source coordinates inside the 2019 polygons, and demographic joins; they do not prove station representativeness or partner approval. Missing/stale weather stays Unknown and receives no heat-based assignment. The default synthetic demo remains separate.

## macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m heataction demo
.venv/bin/python -m heataction serve
```

## What to try

- Change the team budget from 2 to 1. The additional assignment changes.
- Exclude an area and inspect the remaining allocation.
- Adjust the relative weight on senior count versus senior share.
- Open the recommendation explanation and export a CSV.
- Set the team budget to zero. The app should allocate zero slots.

The app currently forecasts by carrying the latest WBGT forward for one hour. It labels this **persistence baseline**, not trained AI. The independent ML experiment is not yet used for app inference.

## Collect real observations

Run in another terminal, using the virtual environment's Python:

```powershell
.\.venv\Scripts\python.exe -m heataction ingest --source all
.\.venv\Scripts\python.exe -m heataction serve --mode observed --port 8001
```

Open http://127.0.0.1:8001. Without a reviewed area file, this shows a weather observation inspector and no demographic recommendations. The code does not blend synthetic population data with actual weather.

To plan with real areas, create the reviewed JSON described in `docs/DATA.md` and restart:

```powershell
.\.venv\Scripts\python.exe -m heataction serve --mode observed --areas data/areas_reviewed.json --port 8001
```

Source collection is explicit; refreshing the browser reads stored observations. Rerun ingestion to retrieve new readings. Optional historical command: `python -m heataction ingest --source all --date 2026-09-20`. Historical access is not yet confirmed in the target deployment environment.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Run the optional forecast experiment

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ml]"
.\.venv\Scripts\python.exe -m heataction evaluate --mode demo
```

This compares persistence, a time-of-day baseline and gradient boosting with chronological splits. Synthetic metrics are only a code exercise. Use `--mode observed` once sufficient real history has been collected. Reports go in `artifacts/`.

## Project navigation

| Location | Purpose |
|---|---|
| `heataction/sources.py` | Public API access, response normalization and raw snapshots |
| `heataction/geography.py` | Verified Census/URA joins, polygon checks and reviewed pilot mappings |
| `data/reference/observed/` | Official demographic/boundary snapshots, checksums and mapping audit |
| `heataction/storage.py` | Local cache and ingestion run log |
| `heataction/planner.py` | Priority policy, freshness checks and capacity allocation |
| `heataction/evaluation.py` | Exact next-hour targets and chronological model comparison |
| `heataction/server.py` | Local app API and CSV exports |
| `heataction/web/index.html` | Browser interface |
| `heataction/web/map.js` | Interactive local SVG map and area detail panels |
| `notebooks/` | Databricks ingestion and MLflow experiment source notebooks |
| `tests/` | Data, allocation and temporal validation checks |
| `docs/STATUS.md` | Current truth about implementation and validation |
| `docs/TASKS.md` | Next work in priority order |
| `docs/DECISIONS.md` | Reasons behind major choices |
| `docs/DATA.md` | Sources, contracts, limitations and mapping format |
| `docs/DATABRICKS.md` | Workspace deployment instructions |
| `docs/NEXT_SESSION.md` | Context for continuing in your coding workspace |
| `docs/VISION.md` | Original detailed proposal, including later features |

Keep `docs/STATUS.md` current after each work session. Do not record API keys, passwords or personal resident records. See `docs/GITHUB.md` for repository setup and how to save future changes.
