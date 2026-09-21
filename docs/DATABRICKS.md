# Databricks setup

These source notebooks are provided for execution in your workspace. They have not been deployed or executed by this project handoff.

1. Create or open your Databricks Free Edition workspace.
2. Upload the `heataction` package directory into a project folder, preserving the Python files and their names. Import `notebooks/01_ingest_databricks.py` as a Python source notebook. The notebook needs the package's parent directory in its `project_root` widget.
3. Enter that absolute `/Workspace/...` project folder in `project_root`. Choose a catalogue in which you can create schemas. The default is your current catalogue.
4. Leave `raw_dir` and `date` blank for a current API fetch. Run the notebook. It creates `heataction_bronze`, `heataction_silver` and `heataction_gold` schemas within your selected catalogue.
5. Inspect source responses, normalized rows and quarantined records. Confirm both source names appear. Run a second time and verify Silver does not duplicate `(source, station_id, observed_at)`.
6. Query the Gold `current_persistence_forecasts` view. Empty output may mean no readings satisfy the explicit 30-minute freshness policy. Do not fill it with synthetic observations to appear live.
7. If outbound API requests are blocked, collect observed data on your computer, upload raw envelope JSON files into a managed Unity Catalog volume, and set `raw_dir` to that volume path. This is replay ingestion; disclose it. Preserve source timestamps. Do not use the synthetic demo cache here.
8. Once date retrieval and coverage have been validated, backfill a bounded historical range. The prototype collector accepts one date per invocation, so schedule a small controlled sequence rather than an unbounded job.
9. Import `02_evaluate_databricks.py`, set its project root/catalogue, and run it after sufficient history exists. It records comparisons in MLflow. It does not register or deploy a winning model automatically.
10. Create a Lakeflow Job for notebook 01 after manual execution succeeds. Confirm scheduling support, quota use and failure handling in your account. Avoid continuously running compute.

The notebook never drops an existing schema or table. Confirm schema names before running. The same source normalization function runs locally and in Databricks.

## Remaining platform work

- Ingest the verified local snapshots from `data/reference/observed/` into Bronze, then validate their Silver joins. The shared `heataction.geography.build_pilot(reference_root)` loader can verify the uploaded snapshots and mappings; pass their actual workspace/volume directory. This loader is implemented locally but has not yet been executed in Databricks.
- Store reviewed area-weather mappings and demographic vintage in Unity Catalog.
- Materialise Gold area priorities and plan scenarios.
- Connect a Databricks App or dashboard to those tables. The local HTTP server is a development interface, not a supplied production Databricks App deployment.
- Record the actual job schedule, workspace asset locations and MLflow run references in STATUS.md after deployment.
- Inspect captured lineage and document dependencies the platform does not capture automatically.

References: [Delta MERGE](https://docs.databricks.com/aws/en/delta/merge), [Free Edition limits](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).
