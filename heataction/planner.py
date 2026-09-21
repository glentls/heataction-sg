"""Explicit planning policy. Scores are not medical probabilities."""
from datetime import datetime, timedelta
import math

from .sources import utc_time


def heat_category(value):
    # WBGT category boundaries in the official advisory, reviewed 21 Sep 2026.
    # General-population outdoor guidance, not an individual clinical threshold.
    return "High" if value >= 33 else "Moderate" if value >= 31 else "Low"


def validate_areas(areas):
    seen = set()
    for area in areas:
        if not isinstance(area.get("area_id"), str) or not area["area_id"] or area["area_id"] in seen:
            raise ValueError("Area IDs must be nonempty and unique")
        seen.add(area["area_id"])
        for key in ("residents", "seniors65", "population_year"):
            if type(area.get(key)) is not int:
                raise ValueError(f"{key} must be an integer")
        if area["residents"] <= 0 or not 0 <= area["seniors65"] <= area["residents"]:
            raise ValueError("Invalid demographic counts")
        for key in ("name", "station_id", "population_source", "mapping_method"):
            if not isinstance(area.get(key), str) or not area[key].strip():
                raise ValueError(f"Area missing {key}")
        if not isinstance(area.get("mapping_verified"), bool):
            raise ValueError("mapping_verified must be explicitly true or false")


def percentile(values, value):
    # Midrank over a fixed full reference cohort; filters never change this cohort.
    return (sum(v < value for v in values) + 0.5 * sum(v == value for v in values)) / len(values)


def build_plan(areas, readings, *, as_of, budget=2, contacts=10, selected=None,
               locked=(), max_age_minutes=30, count_weight=0.5):
    validate_areas(areas)
    if type(budget) is not int or budget < 0 or type(contacts) is not int or contacts <= 0:
        raise ValueError("Budget must be a nonnegative integer; contacts must be positive")
    if not math.isfinite(count_weight) or not 0 <= count_weight <= 1:
        raise ValueError("Population count weight must be between zero and one")
    current = datetime.fromisoformat(utc_time(as_of))
    known = {a["area_id"] for a in areas}
    selected = set(known if selected is None else selected)
    locked = set(locked)
    if not selected <= known or not locked <= selected:
        raise ValueError("Selection/locked areas are outside the configured service area")
    if len(locked) > budget:
        raise ValueError("Locked assignments exceed the team budget")
    latest = {}
    for row in readings:
        if row["source"] != "wbgt":
            continue
        t = datetime.fromisoformat(utc_time(row["observed_at"]))
        if t > current:
            continue
        previous = latest.get(row["station_id"])
        if previous is None or row["observed_at"] > previous["observed_at"]:
            latest[row["station_id"]] = row
    counts = [a["seniors65"] for a in areas]
    shares = [a["seniors65"] / a["residents"] for a in areas]
    rows = []
    for area in areas:
        observation = latest.get(area["station_id"])
        age = ((current - datetime.fromisoformat(observation["observed_at"])).total_seconds() / 60
               if observation else None)
        status = "Ready"
        if not area["mapping_verified"]:
            status = "Mapping unverified"
        elif observation is None:
            status = "No observation"
        elif "station_latitude" in area and "station_longitude" in area:
            from .geography import haversine_km
            if haversine_km(area["station_longitude"], area["station_latitude"],
                            observation["longitude"], observation["latitude"]) > 0.1:
                status = "Station moved; mapping review needed"
        if status == "Ready" and age > max_age_minutes:
            status = "Stale observation"
        predicted = float(observation["value"]) if observation and status == "Ready" else None
        if predicted is not None and not math.isfinite(predicted):
            status, predicted = "Invalid observation", None
        category = heat_category(predicted) if predicted is not None else "Unknown"
        h = {"Low": 0, "Moderate": 1, "High": 2, "Unknown": 0}[category]
        cp = percentile(counts, area["seniors65"])
        sp = percentile(shares, area["seniors65"] / area["residents"])
        priority = h * (count_weight * cp + (1 - count_weight) * sp) if status == "Ready" else None
        q = min(contacts, area["seniors65"])
        rows.append({**area, "senior_share": area["seniors65"] / area["residents"],
                     "observed_at": observation["observed_at"] if observation else None,
                     "observation_age_minutes": age, "forecast_wbgt": predicted,
                     "forecast_target": (current + timedelta(hours=1)).isoformat(),
                     "forecast_method": "Persistence baseline (not trained ML)",
                     "category": category, "status": status, "count_percentile": cp,
                     "share_percentile": sp, "priority": priority, "contact_capacity": q,
                     "allocation_value": (priority or 0) * q, "assigned": False,
                     "eligible": area["area_id"] in selected})
    ready = [r for r in rows if r["eligible"] and r["status"] == "Ready" and r["allocation_value"] > 0]
    valid_locks = {r["area_id"] for r in ready}
    if not locked <= valid_locks:
        raise ValueError("Cannot lock an area with missing/stale data or zero additional heat priority")
    ready.sort(key=lambda r: (-r["allocation_value"], r["area_id"]))
    assigned = locked | {r["area_id"] for r in [x for x in ready if x["area_id"] not in locked][:budget - len(locked)]}
    for row in rows:
        row["assigned"] = row["area_id"] in assigned
        row["locked"] = row["area_id"] in locked
    rows.sort(key=lambda r: (-r["allocation_value"], r["area_id"]))
    return {"rows": rows, "budget": budget, "assigned_slots": len(assigned),
            "unused_slots": budget - len(assigned), "contacts_per_slot": contacts,
            "planned_contact_capacity": sum(r["contact_capacity"] for r in rows if r["assigned"]),
            "as_of": current.isoformat(), "count_weight": count_weight,
            "reference_cohort": sorted(known), "max_age_minutes": max_age_minutes,
            "scope": "Simulated additional outreach capacity, not completed contacts or health outcomes"}
