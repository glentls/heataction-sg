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
