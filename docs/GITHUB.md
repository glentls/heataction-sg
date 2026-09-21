# GitHub repository

Target: `glentls/heataction-sg`, private. See STATUS.md for upload status.

The repository includes application code, tests, frozen public weather fixtures, Databricks source notebooks and project documentation. `.gitignore` excludes `.venv`, Python caches, runtime weather databases and snapshots, generated artifacts, and `.env` files. A new clone must recreate the virtual environment and generate its own demo data using README.md.

## Save later changes

Run from the project folder in PowerShell:

```powershell
git status
git diff
git add README.md
git commit -m "Update project documentation"
git push
```

Replace `README.md` with the files you intend to include. Review them before committing. Keep credentials in environment variables or the platform's secret mechanism.

The GitHub repository stores the project source. The local development app still runs on your computer; Databricks remains the submission platform.
