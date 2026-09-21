# Databricks notebook source
# MAGIC %md
# MAGIC # HeatAction SG: public observations to governed Delta tables
# MAGIC Import this source notebook and the heataction package into one workspace folder.
# MAGIC Follow docs/DATABRICKS.md. This notebook has not yet been executed in a Databricks workspace.

# COMMAND ----------
import sys, json, hashlib, re, uuid
from pathlib import Path
from datetime import datetime

dbutils.widgets.text("project_root", "", "Absolute workspace project folder")
dbutils.widgets.text("catalog", spark.sql("SELECT current_catalog()").first()[0])
dbutils.widgets.text("raw_dir", "", "Optional /Volumes/... folder containing observed raw envelopes")
dbutils.widgets.text("date", "", "Optional historical SGT date")
project_root = dbutils.widgets.get("project_root")
if not project_root:
    raise ValueError("Set project_root to the uploaded folder containing heataction/")
sys.path.insert(0, project_root)
from heataction.sources import fetch_pages, normalize, now_utc

catalog = dbutils.widgets.get("catalog")
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", catalog):
    raise ValueError("Use a simple catalog identifier containing letters, numbers and underscores")
spark.conf.set("spark.sql.session.timeZone", "UTC")
for layer in ("bronze", "silver", "gold"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.heataction_{layer}")

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from pyspark.sql.window import Window
from delta.tables import DeltaTable

raw_table = f"{catalog}.heataction_bronze.weather_responses"
clean_table = f"{catalog}.heataction_silver.weather_observations"
reject_table = f"{catalog}.heataction_silver.weather_rejections"
spark.sql(f"""CREATE TABLE IF NOT EXISTS {raw_table} (
 run_id STRING, source STRING, source_url STRING, retrieved_at TIMESTAMP,
 payload_sha256 STRING, payload_json STRING) USING DELTA
 COMMENT 'Public weather API response archive. Real observations only; retrieval time may differ from event time.'""")
spark.sql(f"""CREATE TABLE IF NOT EXISTS {reject_table} (
 run_id STRING, source STRING, reason STRING, record_json STRING) USING DELTA""")
schema = StructType([
    StructField("source", StringType()), StructField("station_id", StringType()),
    StructField("station_name", StringType()), StructField("observed_at", TimestampType()),
    StructField("source_updated_at", TimestampType()), StructField("value", DoubleType()),
    StructField("unit", StringType()), StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()), StructField("heat_stress", StringType()),
    StructField("retrieved_at", TimestampType()),
])
if not spark.catalog.tableExists(clean_table):
    spark.createDataFrame([], schema).write.format("delta").saveAsTable(clean_table)

# COMMAND ----------
run_id = str(uuid.uuid4())
raw_dir = dbutils.widgets.get("raw_dir")
date = dbutils.widgets.get("date") or None

def envelopes():
    if raw_dir:
        for path in sorted(Path(raw_dir).rglob("*.json")):
            if path.name.endswith(".rejected.json"):
                continue
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if envelope.get("source") in ("wbgt", "rainfall") and "payload" in envelope:
                yield envelope
    else:
        for source in ("wbgt", "rainfall"):
            yield from fetch_pages(source, date)

counts = {"accepted": 0, "rejected": 0, "responses": 0}
for envelope in envelopes():
    payload_text = json.dumps(envelope["payload"], sort_keys=True)
    digest = hashlib.sha256(payload_text.encode()).hexdigest()
    spark.createDataFrame([(
        run_id, envelope["source"], envelope["source_url"],
        datetime.fromisoformat(envelope["retrieved_at"]), digest, payload_text,
    )], "run_id string, source string, source_url string, retrieved_at timestamp, payload_sha256 string, payload_json string").write.mode("append").saveAsTable(raw_table)
    rows, rejected = normalize(envelope["source"], envelope["payload"], envelope["retrieved_at"])
    if rejected:
        spark.createDataFrame([(run_id, r["source"], r["reason"], json.dumps(r["record"])) for r in rejected],
                              "run_id string, source string, reason string, record_json string").write.mode("append").saveAsTable(reject_table)
    if rows:
        for row in rows:
            for field in ("observed_at", "source_updated_at", "retrieved_at"):
                row[field] = datetime.fromisoformat(row[field])
        df = spark.createDataFrame(rows, schema)
        window = Window.partitionBy("source", "station_id", "observed_at").orderBy(F.desc("source_updated_at"), F.desc("retrieved_at"))
        df = df.withColumn("rn", F.row_number().over(window)).filter("rn = 1").drop("rn")
        DeltaTable.forName(spark, clean_table).alias("t").merge(df.alias("s"),
            "t.source = s.source AND t.station_id = s.station_id AND t.observed_at = s.observed_at"
        ).whenMatchedUpdateAll(condition="s.source_updated_at > t.source_updated_at OR (s.source_updated_at = t.source_updated_at AND s.retrieved_at >= t.retrieved_at)").whenNotMatchedInsertAll().execute()
    counts["accepted"] += len(rows)
    counts["rejected"] += len(rejected)
    counts["responses"] += 1
if not counts["responses"]:
    raise ValueError("No observed source envelopes found")
print({"run_id": run_id, **counts})

# COMMAND ----------
# Gold view exposes a clearly named persistence baseline, not a trained model.
spark.sql(f"""CREATE OR REPLACE VIEW {catalog}.heataction_gold.current_persistence_forecasts AS
WITH ranked AS (
 SELECT *, row_number() OVER (PARTITION BY station_id ORDER BY observed_at DESC) AS rn
 FROM {clean_table} WHERE source = 'wbgt' AND observed_at <= current_timestamp()
)
SELECT station_id, station_name, observed_at, value AS forecast_wbgt,
 current_timestamp() AS issued_at, current_timestamp() + INTERVAL 1 HOUR AS target_at,
 'persistence_v0_1' AS model_version, latitude, longitude
FROM ranked WHERE rn = 1 AND observed_at >= current_timestamp() - INTERVAL 30 MINUTES""")
display(spark.table(f"{catalog}.heataction_gold.current_persistence_forecasts"))
