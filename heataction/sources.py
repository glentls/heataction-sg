"""Public source access and strict normalization. No fabricated live fallback."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINTS = {
    "wbgt": "https://api-open.data.gov.sg/v2/real-time/api/weather?api=wbgt",
    "rainfall": "https://api-open.data.gov.sg/v2/real-time/api/rainfall",
}
OBSERVATION_FIELDS = (
    "source", "station_id", "station_name", "observed_at", "source_updated_at",
    "value", "unit", "latitude", "longitude", "heat_stress", "retrieved_at",
)


def utc_time(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp must contain an explicit timezone")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def number(value) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("Missing or invalid numeric value")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite numeric value")
    return result


def request_json(url: str, *, timeout: int = 12) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "HeatActionSG/0.1"}
    if os.environ.get("DATA_GOV_SG_API_KEY"):
        headers["x-api-key"] = os.environ["DATA_GOV_SG_API_KEY"]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
                data = json.load(response)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"Source returned HTTP {exc.code}") from exc
            # Bounded backoff, retaining public API rate-limit signals.
            retry = exc.headers.get("Retry-After", "")
            delay = min(float(retry), 10) if retry.isdigit() else 2 ** attempt
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError("Source connection failed; raw/live status is unchanged") from exc
            time.sleep(2 ** attempt)
    raise RuntimeError("Request failed")


def fetch_pages(source: str, date: str | None = None):
    """Yield raw envelopes. Date support/history is to be smoke-tested in deployment."""
    base = ENDPOINTS[source]
    params = {"date": date} if date else {}
    seen = set()
    for _ in range(1000):
        url = base + (("&" if "?" in base else "?") + urllib.parse.urlencode(params) if params else "")
        payload = request_json(url)
        if payload.get("code") != 0:
            raise ValueError(f"API reported failure for {source}")
        yield {"source": source, "source_url": url, "retrieved_at": now_utc(), "payload": payload}
        token = payload.get("data", {}).get("paginationToken")
        if not token:
            return
        if token in seen:
            raise ValueError("Repeated pagination token; stopping to avoid a loop")
        seen.add(token)
        params["paginationToken"] = token
    raise ValueError("Pagination limit exceeded")


def normalize(source: str, payload: dict, retrieved_at: str):
    """Return (accepted, rejected). Unknown top-level shapes fail loudly."""
    if source not in ENDPOINTS or payload.get("code") != 0:
        raise ValueError("Unsupported source or unsuccessful API response")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing API data object")
    retrieved_at = utc_time(retrieved_at)
    accepted, rejected = [], []

    def add(raw, stamp, updated, station_id, name, location, value, heat=""):
        try:
            if not station_id:
                raise ValueError("Missing station identifier")
            n = number(value)
            if source == "rainfall" and n < 0:
                raise ValueError("Negative rainfall")
            if source == "wbgt" and not -10 <= n <= 60:
                raise ValueError("WBGT outside broad engineering validity bounds")
            lat, lon = number(location["latitude"]), number(location["longitude"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError("Invalid coordinates")
            observed = utc_time(stamp)
            accepted.append(dict(zip(OBSERVATION_FIELDS, [
                source, str(station_id), str(name), observed, utc_time(updated or stamp),
                n, "degC_WBGT" if source == "wbgt" else "mm", lat, lon,
                str(heat or ""), retrieved_at,
            ])))
        except (KeyError, TypeError, ValueError) as exc:
            rejected.append({"source": source, "reason": str(exc), "record": raw})

    if source == "wbgt":
        records = data.get("records")
        if not isinstance(records, list):
            raise ValueError("WBGT schema changed: expected data.records")
        for record in records:
            item = record.get("item", {})
            if item.get("isStationData") is not True or not isinstance(item.get("readings"), list):
                raise ValueError("WBGT schema changed: expected station observations")
            if item.get("type") != "observation":
                raise ValueError("Expected observed WBGT, not a source forecast")
            for reading in item["readings"]:
                station = reading.get("station", {})
                add(reading, record.get("datetime"), record.get("updatedTimestamp"),
                    station.get("id"), station.get("name", ""), reading.get("location", {}),
                    reading.get("wbgt"), reading.get("heatStress", ""))
    else:
        if not isinstance(data.get("stations"), list) or not isinstance(data.get("readings"), list):
            raise ValueError("Rainfall schema changed: expected stations/readings")
        if data.get("readingUnit") != "mm":
            raise ValueError("Rainfall unit changed; review before ingesting")
        stations = {s["id"]: s for s in data["stations"]}
        for group in data["readings"]:
            if not isinstance(group.get("data"), list):
                raise ValueError("Rainfall schema changed: expected readings[].data")
            for reading in group["data"]:
                station = stations.get(reading.get("stationId"), {})
                add(reading, group.get("timestamp"), group.get("timestamp"),
                    station.get("id"), station.get("name", ""), station.get("location", {}),
                    reading.get("value"))
    return accepted, rejected


def save_raw(envelope: dict, root: Path) -> Path:
    canonical = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    root = root / "raw" / envelope["source"]
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{digest}.json"
    if not path.exists():
        path.write_text(json.dumps({**envelope, "payload_sha256": digest}, indent=2), encoding="utf-8")
    return path
