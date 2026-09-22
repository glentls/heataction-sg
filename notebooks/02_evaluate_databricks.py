# Databricks notebook source
# MAGIC %md
# MAGIC # Exploratory WBGT forecast comparison
# MAGIC Run after accumulating at least seven days of usable observed history.
# MAGIC This notebook is supplied for workspace execution; it has not been run here.

# COMMAND ----------
# MAGIC %pip install "scikit-learn>=1.5,<2" mlflow "typing_extensions>=4.13"
# typing_extensions>=4.13 is pinned explicitly: the runtime's preinstalled version predates
# mlflow's pydantic dependency (ImportError: cannot import name 'Sentinel'), observed 22 Sep 2026.
dbutils.library.restartPython()

# COMMAND ----------
import sys, re, json
dbutils.widgets.text("project_root", "")
dbutils.widgets.text("catalog", spark.sql("SELECT current_catalog()").first()[0])
if not dbutils.widgets.get("project_root"):
    raise ValueError("Set project_root to the workspace project folder")
sys.path.insert(0, dbutils.widgets.get("project_root"))
from heataction.evaluation import evaluate
import mlflow

catalog = dbutils.widgets.get("catalog")
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", catalog):
    raise ValueError("Invalid catalog name")
spark.conf.set("spark.sql.session.timeZone", "UTC")
history = spark.sql(f"""SELECT source, station_id,
 date_format(observed_at, "yyyy-MM-dd'T'HH:mm:ss'+00:00'") AS observed_at, value
 FROM {catalog}.heataction_silver.weather_observations
 WHERE source = 'wbgt' ORDER BY observed_at, station_id""")
if history.count() > 1_000_000:
    raise ValueError("Select a documented smaller historical window before collecting to the driver")
records = [row.asDict() for row in history.collect()]
report = evaluate(records, mode="observed")
with mlflow.start_run(run_name="heataction_temporal_holdout"):
    mlflow.log_params({"horizon_minutes": 60, "chosen_model": report["chosen_model"], "selection": "validation_mae"})
    for split in ("validation", "test"):
        for model_name, values in report[split].items():
            for key, value in values.items():
                if value is not None:
                    mlflow.log_metric(f"{split}_{model_name}_{key}", value)
    mlflow.log_dict(report, "evaluation.json")
print(json.dumps(report, indent=2))
