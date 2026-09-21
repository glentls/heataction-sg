# Project working agreement

Read README.md, docs/STATUS.md and docs/DECISIONS.md before changing the project.
Treat docs/VISION.md as the longer-term proposal; STATUS.md describes what actually works.

- Keep synthetic and observed data in separate directories and visibly labelled in outputs.
- Never silently replace a failed API response with generated data.
- Do not claim a forecast or social impact improvement before measuring it on the appropriate data.
- Keep demographic vintage, source identifiers and mapping assumptions visible.
- Update docs/STATUS.md, docs/TASKS.md and CHANGELOG.md after meaningful work.
- Record consequential architecture decisions in docs/DECISIONS.md.
- Verify changes to ingestion, forecasting and allocation with meaningful regression checks.
- Keep credentials in environment variables or the platform's secret mechanism, never in tracked files.
- Preserve this project's Databricks submission goal. The local server is a development tool.
- Do not publish, submit, contact partners or create cloud resources without the user's instruction.
