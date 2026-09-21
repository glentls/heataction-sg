"""SQLite is a local development cache; Databricks notebooks use Delta tables."""
import json
import sqlite3
from pathlib import Path

from .sources import now_utc


def connect(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "weather.sqlite")
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS observations (
        source TEXT, station_id TEXT, observed_at TEXT, source_updated_at TEXT,
        retrieved_at TEXT, record_json TEXT NOT NULL,
        PRIMARY KEY(source, station_id, observed_at))""")
    connection.execute("""CREATE TABLE IF NOT EXISTS runs (
        run_at TEXT, source TEXT, status TEXT, accepted INTEGER, rejected INTEGER, detail TEXT)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS lock_reasons (
        area_id TEXT PRIMARY KEY, reason TEXT NOT NULL, recorded_at TEXT NOT NULL)""")
    connection.commit()
    return connection


def upsert(root: Path, records: list[dict]):
    db = connect(root)
    try:
        with db:
            for record in records:
                db.execute("""INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source, station_id, observed_at) DO UPDATE SET
                    source_updated_at=excluded.source_updated_at,
                    retrieved_at=excluded.retrieved_at, record_json=excluded.record_json
                    WHERE excluded.source_updated_at > observations.source_updated_at
                    OR (excluded.source_updated_at = observations.source_updated_at
                        AND excluded.retrieved_at >= observations.retrieved_at)""", (
                    record["source"], record["station_id"], record["observed_at"],
                    record["source_updated_at"], record["retrieved_at"], json.dumps(record)))
    finally:
        db.close()


def observations(root: Path) -> list[dict]:
    db = connect(root)
    try:
        return [json.loads(row[0]) for row in db.execute("SELECT record_json FROM observations ORDER BY observed_at, station_id")]
    finally:
        db.close()


def log_run(root, source, status, accepted=0, rejected=0, detail=""):
    db = connect(root)
    try:
        with db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)", (now_utc(), source, status, accepted, rejected, detail))
    finally:
        db.close()


def recent_runs(root):
    db = connect(root)
    try:
        return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY rowid DESC LIMIT 10")]
    finally:
        db.close()


def save_lock_reason(root, area_id, reason):
    db = connect(root)
    try:
        with db:
            db.execute("""INSERT INTO lock_reasons VALUES (?, ?, ?)
                ON CONFLICT(area_id) DO UPDATE SET reason=excluded.reason, recorded_at=excluded.recorded_at""",
                (area_id, reason, now_utc()))
    finally:
        db.close()


def delete_lock_reason(root, area_id):
    db = connect(root)
    try:
        with db:
            db.execute("DELETE FROM lock_reasons WHERE area_id = ?", (area_id,))
    finally:
        db.close()


def lock_reasons(root):
    db = connect(root)
    try:
        return {row["area_id"]: {"reason": row["reason"], "recorded_at": row["recorded_at"]}
                for row in db.execute("SELECT * FROM lock_reasons ORDER BY area_id")}
    finally:
        db.close()
