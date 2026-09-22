# Continue this project in VS Code

## Local startup verified on 21 September 2026

The Windows `py` launcher reported `No installed Python found!`, while `python` resolved to Python 3.13.7. Use these commands from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m heataction demo
.\.venv\Scripts\python.exe -m heataction serve
```

Open http://127.0.0.1:8000. The demo generated 4,033 synthetic observations; all 16 regression tests and local HTTP smoke checks passed. Browser visual inspection remains pending. This session left a background demo server running, with logs in `data/runtime/demo/server.stdout.log` and `server.stderr.log`. Before starting another server on port 8000, stop the existing process or choose another port with `serve --port 8001`.

## Continuation prompt

The real-area map, coordinator lock controls (with required saved reasons), side-by-side scenario comparison, and a per-station weather-history chart (recent trend, observation age, distinguished one-hour forecast) are now implemented. Start the observed pilot with `.\.venv\Scripts\python.exe -m heataction serve --mode observed --pilot --port 8001`; see STATUS.md and DATA.md for the verified Census/URA joins and technical station review. All 33 regression tests and desktop/mobile browser checks pass.

A policy backtest (`python -m heataction compare-policies`) now gives real, measured evidence that the allocation policy beats naive baselines on synthetic data (93% vs 17% recall against genuinely-High moments) — see STATUS.md for the full numbers and their limitations. A coordinator usability-test protocol exists at docs/USABILITY_TEST.md with six concrete tasks; a scripted walkthrough confirms they're all mechanically completable, but **it has not been run with a real coordinator yet** — that is the single highest-value thing left to do that more engineering cannot substitute for.

The Databricks deployment now goes end to end in Glen's Free Edition workspace (`/Workspace/Users/glentanlusheng@gmail.com/heataction-sg/`, catalogue `workspace`): ingestion, demographic/plan materialisation, and evaluation notebooks all run successfully, and a Databricks App (`databricks_app/`) reads the resulting plan table live — verified working, then stopped (`databricks apps start heataction-plan` to bring it back). See docs/DATABRICKS.md and STATUS.md for exactly what was verified and what's still missing: nothing schedules the notebooks to rerun automatically, so both Gold tables the app reads go stale without a manual rerun. That scheduling is the natural next Databricks step. Separately, real chronological WBGT evaluation remains blocked on collecting enough observed history (the 7-day gate). The older handoff prompt below describes the original project starting point, not the latest state.

Open the project folder containing README.md. Use this message to give a coding assistant the context:

> We are building HeatAction SG for DAISI 2026 B1 HeatGuard. Read AGENTS.md, README.md, docs/STATUS.md, docs/DATA.md and docs/TASKS.md before making changes. The local synthetic app and collector are implemented. Databricks source notebooks are supplied but workspace execution is pending. Start by helping me run the app and collect both real weather feeds. Then implement verified Census/URA ingestion and reviewed area-weather joins. Preserve explicit synthetic/observed labels. Keep the documentation updated after meaningful changes, and report actual test results. Do not claim the model improves on a baseline until real chronological evaluation supports it.

## Documentation rhythm

After each session, record in STATUS.md:

1. What changed and why.
2. What was executed and the result.
3. What remains untested or blocked.
4. The single next implementation task.

Use DECISIONS.md for architecture/policy choices, DATA.md for source contracts, TASKS.md for remaining work and CHANGELOG.md for a short version history. Keep secrets and personal resident information out of all documentation.
