"""Deterministic synthetic data, isolated from observed government readings."""
import math
import random
from datetime import datetime, timedelta, timezone

from .sources import normalize
from .storage import upsert

DEMO_AREAS = [
    {"area_id": "demo_north", "name": "Demo North", "residents": 9000, "seniors65": 2700,
     "population_year": 2020, "station_id": "DEMO_N", "population_source": "Synthetic demonstration",
     "mapping_method": "Fictional area and station", "mapping_verified": True},
    {"area_id": "demo_central", "name": "Demo Central", "residents": 13000, "seniors65": 1800,
     "population_year": 2020, "station_id": "DEMO_C", "population_source": "Synthetic demonstration",
     "mapping_method": "Fictional area and station", "mapping_verified": True},
    {"area_id": "demo_east", "name": "Demo East", "residents": 8000, "seniors65": 2100,
     "population_year": 2020, "station_id": "DEMO_E", "population_source": "Synthetic demonstration",
     "mapping_method": "Fictional area and station", "mapping_verified": True},
]


def make_demo():
    rng = random.Random(2026)
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    rows = []
    coords = [(1.40, 103.82), (1.34, 103.85), (1.33, 103.94)]
    for slot in range(14 * 96):
        stamp = (start + timedelta(minutes=15 * slot)).isoformat()
        values = []
        for index, area in enumerate(DEMO_AREAS):
            local_hour = ((slot / 4) + 8) % 24
            value = 29.4 + 3.5 * math.cos((local_hour - 14) * math.pi / 12) + index * 0.25 + rng.gauss(0, 0.22)
            if slot == 14 * 96 - 1:
                value = [33.6, 32.1, 30.8][index]
            values.append({"station": {"id": area["station_id"], "name": area["name"]},
                           "location": {"latitude": coords[index][0], "longitude": coords[index][1]},
                           "wbgt": round(value, 2), "heatStress": ""})
        payload = {"code": 0, "data": {"records": [{"datetime": stamp, "updatedTimestamp": stamp,
                   "item": {"type": "observation", "isStationData": True, "readings": values}}]}}
        normalized, _ = normalize("wbgt", payload, stamp)
        rows.extend(normalized)
    last = rows[-1]["observed_at"]
    rainfall = {"code": 0, "data": {"readingUnit": "mm",
        "stations": [{"id": "DEMO_R", "name": "Demo rain gauge", "location": {"latitude": 1.34, "longitude": 103.85}}],
        "readings": [{"timestamp": last, "data": [{"stationId": "DEMO_R", "value": 0.0}]}]}}
    rows.extend(normalize("rainfall", rainfall, last)[0])
    return rows, DEMO_AREAS, last


def seed(root):
    import json
    root.mkdir(parents=True, exist_ok=True)
    rows, areas, last = make_demo()
    upsert(root, rows)
    (root / "areas.json").write_text(json.dumps(areas, indent=2), encoding="utf-8")
    (root / "mode.json").write_text(json.dumps({"mode": "synthetic", "as_of": last}), encoding="utf-8")
    return len(rows)
