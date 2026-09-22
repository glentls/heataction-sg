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

The real-area map, coordinator lock controls (with required saved reasons) and side-by-side scenario comparison are now implemented. Start the observed pilot with `.\.venv\Scripts\python.exe -m heataction serve --mode observed --pilot --port 8001`; see STATUS.md and DATA.md for the verified Census/URA joins and technical station review. All 27 regression tests and desktop/mobile browser checks pass. The next feature milestone is real chronological evaluation on observed WBGT and a deployed forecast artifact/inference path. The older handoff prompt below describes the original project starting point, not the latest state.

Open the project folder containing README.md. Use this message to give a coding assistant the context:

> We are building HeatAction SG for DAISI 2026 B1 HeatGuard. Read AGENTS.md, README.md, docs/STATUS.md, docs/DATA.md and docs/TASKS.md before making changes. The local synthetic app and collector are implemented. Databricks source notebooks are supplied but workspace execution is pending. Start by helping me run the app and collect both real weather feeds. Then implement verified Census/URA ingestion and reviewed area-weather joins. Preserve explicit synthetic/observed labels. Keep the documentation updated after meaningful changes, and report actual test results. Do not claim the model improves on a baseline until real chronological evaluation supports it.

## Documentation rhythm

After each session, record in STATUS.md:

1. What changed and why.
2. What was executed and the result.
3. What remains untested or blocked.
4. The single next implementation task.

Use DECISIONS.md for architecture/policy choices, DATA.md for source contracts, TASKS.md for remaining work and CHANGELOG.md for a short version history. Keep secrets and personal resident information out of all documentation.
