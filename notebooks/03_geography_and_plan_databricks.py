# Databricks notebook source
# MAGIC %md
# MAGIC # HeatAction SG: reviewed demographics and a Gold priority plan
# MAGIC Run after `01_ingest_databricks` has populated Silver weather observations. Requires the
# MAGIC reviewed Census/URA/mapping snapshots uploaded to a Unity Catalog volume; see docs/DATABRICKS.md.
# MAGIC This materialises the same allocation policy the local app serves (`heataction.planner.build_plan`),
# MAGIC not a separately trained model.

# COMMAND ----------
import re
import sys

dbutils.widgets.text("project_root", "", "Absolute workspace project folder")
dbutils.widgets.text("catalog", spark.sql("SELECT current_catalog()").first()[0])
dbutils.widgets.text("reference_root", "", "Volume path containing the reviewed Census/URA/mapping snapshots")
dbutils.widgets.text("budget", "2", "Team slot budget for the materialised plan")
dbutils.widgets.text("contacts", "10", "Assumed contacts per slot")
project_root = dbutils.widgets.get("project_root")
reference_root = dbutils.widgets.get("reference_root")
if not project_root:
    raise ValueError("Set project_root to the uploaded folder containing heataction/")
if not reference_root:
    raise ValueError("Set reference_root to the Unity Catalog volume holding the reviewed reference snapshots")
sys.path.insert(0, project_root)
from heataction.geography import build_pilot
from heataction.planner import build_plan
from heataction.sources import now_utc

catalog = dbutils.widgets.get("catalog")
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", catalog):
    raise ValueError("Use a simple catalog identifier containing letters, numbers and underscores")
spark.conf.set("spark.sql.session.timeZone", "UTC")

# COMMAND ----------
# Reruns the same checksum/containment/join validation as the local pilot; fails closed on any mismatch.
pilot = build_pilot(reference_root)
print({"pilot_areas": len(pilot["areas"]), "total_boundaries": len(pilot["geojson"]["features"]),
       "population_year": pilot["population_year"], "boundary_year": pilot["boundary_year"]})

# COMMAND ----------
from pyspark.sql import Row

demographics_table = f"{catalog}.heataction_silver.area_demographics"
demographic_rows = [Row(area_id=p["area_id"], name=p["name"], region=p.get("region"),
                        residents=p.get("residents"), seniors65=p.get("seniors65"),
                        senior_share=p.get("senior_share"), population_year=pilot["population_year"],
                        boundary_year=pilot["boundary_year"], pilot=bool(p.get("pilot", False)))
                    for p in (feature["properties"] for feature in pilot["geojson"]["features"])]
spark.createDataFrame(demographic_rows).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(demographics_table)
print(f"Wrote {len(demographic_rows)} rows to {demographics_table} (all 55 boundaries; only 'pilot' areas are planned)")

# COMMAND ----------
audit_table = f"{catalog}.heataction_silver.pilot_mapping_audit"
audit_rows = [Row(**{**a, "mapping_review_scope": pilot["review_scope"]}) for a in pilot["audit"]]
spark.createDataFrame(audit_rows).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(audit_table)
print(f"Wrote {len(audit_rows)} rows to {audit_table}")

# COMMAND ----------
# Materialise the current recommended plan using the same policy and freshness gates as the local app.
clean_table = f"{catalog}.heataction_silver.weather_observations"
history = spark.sql(f"""SELECT source, station_id,
    date_format(observed_at, "yyyy-MM-dd'T'HH:mm:ss'+00:00'") AS observed_at,
    value, latitude, longitude
    FROM {clean_table} WHERE source = 'wbgt'""").collect()
readings = [row.asDict() for row in history]
budget, contacts = int(dbutils.widgets.get("budget")), int(dbutils.widgets.get("contacts"))
plan = build_plan(pilot["areas"], readings, as_of=now_utc(), budget=budget, contacts=contacts)

plan_rows = [Row(area_id=r["area_id"], name=r["name"], residents=r["residents"], seniors65=r["seniors65"],
                  senior_share=r["senior_share"], station_id=r["station_id"], forecast_wbgt=r["forecast_wbgt"],
                  category=r["category"], status=r["status"], priority=r["priority"],
                  contact_capacity=r["contact_capacity"], assigned=r["assigned"], locked=r["locked"],
                  observed_at=r["observed_at"], forecast_target=r["forecast_target"],
                  forecast_method=r["forecast_method"], issued_at=plan["as_of"],
                  budget=budget, contacts_per_slot=contacts) for r in plan["rows"]]
# An explicit schema is required: when every area is stale or missing (a real, expected state,
# not a bug), forecast_wbgt/priority/observed_at are None for every row, and Spark cannot infer
# a type from an all-null column.
from pyspark.sql.types import BooleanType, DoubleType, IntegerType, StringType, StructField, StructType
plan_schema = StructType([
    StructField("area_id", StringType()), StructField("name", StringType()),
    StructField("residents", IntegerType()), StructField("seniors65", IntegerType()),
    StructField("senior_share", DoubleType()), StructField("station_id", StringType()),
    StructField("forecast_wbgt", DoubleType()), StructField("category", StringType()),
    StructField("status", StringType()), StructField("priority", DoubleType()),
    StructField("contact_capacity", IntegerType()), StructField("assigned", BooleanType()),
    StructField("locked", BooleanType()), StructField("observed_at", StringType()),
    StructField("forecast_target", StringType()), StructField("forecast_method", StringType()),
    StructField("issued_at", StringType()), StructField("budget", IntegerType()),
    StructField("contacts_per_slot", IntegerType()),
])
plan_table = f"{catalog}.heataction_gold.area_priority_plan"
spark.createDataFrame(plan_rows, plan_schema).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(plan_table)
print({"plan_table": plan_table, "issued_at": plan["as_of"], "assigned_slots": plan["assigned_slots"],
       "budget": budget, "rows": len(plan_rows)})
display(spark.table(plan_table))
