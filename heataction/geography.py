"""Observed Census/URA joins and explicit, technically reviewed pilot mappings.

No network requests or synthetic substitutions occur when loading this reference.
"""
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path

REFERENCE_ROOT = Path(__file__).resolve().parent.parent / "data/reference/observed"
POPULATION_ID = "d_d95ae740c0f8961a0b10435836660ce0"
BOUNDARY_ID = "d_4765db0e87b9c86336792efe8a1f7a66"
AGE_COLUMNS = [f"Total_{start}_{start + 4}" for start in range(0, 90, 5)] + ["Total_90andOver"]
SENIOR_COLUMNS = AGE_COLUMNS[13:]
LIMITATION = ("A station inside a planning area is a weather proxy, not proof of uniform heat "
              "or exposure across that area. Technical checks do not establish operational suitability.")


def area_key(name):
    return re.sub(r"\s+", " ", name.strip()).upper()


def census_count(value):
    text = str(value or "").strip()
    if text in ("", "-", "na", "NA", "na.", ".."):
        return None  # Unavailable/suppressed is never interpreted as zero.
    if not re.fullmatch(r"\d+", text):
        raise ValueError(f"Unexpected Census count: {text!r}")
    return int(text)


def parse_census(text):
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    required = {"Number", "Total_Total", *AGE_COLUMNS}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Census schema changed: missing total-sex age columns")
    result = {}
    for row in reader:
        label = row["Number"].strip()
        if not label.endswith(" - Total"):
            continue  # Exclude national total and every subzone: no double counting.
        name = label[:-8].strip()
        key = area_key(name)
        if key in result:
            raise ValueError(f"Duplicate Census planning-area total: {name}")
        residents = census_count(row["Total_Total"])
        bands = [{"label": col.removeprefix("Total_").replace("_", "–").replace("90andOver", "90+"),
                  "count": census_count(row[col])} for col in AGE_COLUMNS]
        seniors = [census_count(row[col]) for col in SENIOR_COLUMNS]
        seniors65 = sum(seniors) if all(v is not None for v in seniors) else None
        if residents is not None and seniors65 is not None and seniors65 > residents:
            raise ValueError(f"Senior count exceeds total population: {name}")
        result[key] = {"name": name, "residents": residents, "seniors65": seniors65,
                       "senior_share": seniors65 / residents if residents and seniors65 is not None else None,
                       "age_bands": bands, "population_year": 2020,
                       "population_dataset_id": POPULATION_ID,
                       "population_source": f"https://data.gov.sg/datasets/{POPULATION_ID}/view",
                       "population_row": label}
    if not result:
        raise ValueError("No Census planning-area totals found")
    return result


def polygons(geometry):
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"]]
    if kind == "MultiPolygon":
        return geometry["coordinates"]
    raise ValueError("Expected Polygon or MultiPolygon boundary")


def in_ring(point, ring):
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]):
        ax, ay = a[:2]
        bx, by = b[:2]
        cross = (x - ax) * (by - ay) - (y - ay) * (bx - ax)
        if abs(cross) < 1e-12 and min(ax, bx) <= x <= max(ax, bx) and min(ay, by) <= y <= max(ay, by):
            return True
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return inside


def contains(geometry, longitude, latitude):
    return any(in_ring((longitude, latitude), poly[0]) and
               not any(in_ring((longitude, latitude), hole) for hole in poly[1:])
               for poly in polygons(geometry))


def bounds(geometry):
    points = [p for poly in polygons(geometry) for ring in poly for p in ring]
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def haversine_km(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, (lon1, lat1, lon2, lat2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1, math.sqrt(a)))


def load_boundaries(payload):
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Expected a boundary FeatureCollection")
    result = {}
    codes = set()
    for feature in payload.get("features", []):
        properties = feature["properties"]
        key, code = area_key(properties["PLN_AREA_N"]), properties["PLN_AREA_C"]
        if key in result or code in codes:
            raise ValueError("Duplicate planning-area boundary")
        codes.add(code)
        geometry = feature["geometry"]
        for poly in polygons(geometry):
            if not poly:
                raise ValueError("Empty boundary polygon")
            for ring in poly:
                if len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError("Boundary ring must be closed")
                if any(len(p) < 2 or not all(math.isfinite(v) for v in p[:2]) or
                       not 103 <= p[0] <= 105 or not 1 <= p[1] <= 2 for p in ring):
                    raise ValueError("Expected Singapore longitude/latitude coordinates")
        result[key] = {"type": "Feature", "geometry": geometry, "properties": {
            "area_id": code.lower(), "boundary_code": code, "name": properties["PLN_AREA_N"].title(),
            "region": properties["REGION_N"].title(), "boundary_year": 2019,
            "boundary_dataset_id": BOUNDARY_ID, "boundary_source": f"https://data.gov.sg/datasets/{BOUNDARY_ID}/view",
            "bounds": bounds(geometry)}}
    if not result:
        raise ValueError("No planning-area boundaries found")
    return result


def build_pilot(reference_root=REFERENCE_ROOT):
    """Verify snapshots, join area totals, and validate every curated station link."""
    from .planner import validate_areas
    root = Path(reference_root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("data_mode") != "observed":
        raise ValueError("Pilot references must be observed data")
    sources = {source["dataset_id"]: source for source in manifest["sources"]}
    content = {}
    for dataset_id, filename, vintage in ((POPULATION_ID, "census2020_age.csv", 2020),
                                           (BOUNDARY_ID, "planning_areas_2019.geojson", 2019)):
        source = sources[dataset_id]
        if source["file"] != filename or source["vintage"] != vintage:
            raise ValueError("Reference vintage/file does not match reviewed contract")
        data = (root / filename).read_bytes()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError(f"Reference checksum mismatch: {filename}")
        content[dataset_id] = data.decode("utf-8-sig")
    populations = parse_census(content[POPULATION_ID])
    boundaries = load_boundaries(json.loads(content[BOUNDARY_ID]))
    unmatched = set(populations) - set(boundaries)
    if unmatched:
        raise ValueError(f"Census areas have no matching 2019 boundary: {sorted(unmatched)}")
    review = json.loads((root / "pilot_mappings.json").read_text(encoding="utf-8"))
    if review.get("data_mode") != "observed" or review.get("boundary_dataset_id") != BOUNDARY_ID:
        raise ValueError("Mapping review references incompatible data")
    areas, audit = [], []
    for mapping in review["mappings"]:
        key = area_key(mapping["area_name"])
        feature = boundaries[key]
        population = populations[key]
        station = mapping["station"]
        if not population["residents"] or population["seniors65"] is None:
            raise ValueError(f"Pilot population unavailable: {key}")
        if not re.fullmatch(r"S\d+", station["station_id"]):
            raise ValueError("Pilot requires an observed WBGT station ID")
        if not contains(feature["geometry"], station["longitude"], station["latitude"]):
            raise ValueError(f"Reviewed station is outside its planning area: {key}")
        if mapping.get("review_status") != "technical_checks_passed" or not mapping.get("review_note"):
            raise ValueError("Pilot mapping requires a documented technical review")
        west, south, east, north = feature["properties"]["bounds"]
        distance = haversine_km((west + east) / 2, (south + north) / 2, station["longitude"], station["latitude"])
        method = (f"Reviewed station inside MP2019 polygon; {distance:.2f} km from boundary bounding-box centre. "
                  "Centre is geometric, not population-weighted. " + LIMITATION)
        area = {**population, **feature["properties"], "station_id": station["station_id"],
                "station_name": station["station_name"], "station_latitude": station["latitude"],
                "station_longitude": station["longitude"], "mapping_verified": True,
                "mapping_method": method, "mapping_review": mapping["review_note"],
                "mapping_reviewed_at": review["reviewed_at"], "mapping_review_scope": review["review_scope"],
                "station_reference_observed_at": station["observed_at"],
                "mapping_distance_km": round(distance, 3)}
        areas.append(area)
        audit.append({"area_id": area["area_id"], "population_row": population["population_row"],
                      "residents": area["residents"], "seniors65": area["seniors65"],
                      "station_id": area["station_id"], "station_inside_boundary": True,
                      "distance_from_boundary_box_centre_km": round(distance, 3)})
    if not areas:
        raise ValueError("Pilot mapping list is empty")
    validate_areas(areas)
    pilot_ids = {a["area_id"] for a in areas}
    for key, feature in boundaries.items():
        feature["properties"].update(populations.get(key, {"residents": None, "seniors65": None, "senior_share": None}))
        feature["properties"]["pilot"] = feature["properties"]["area_id"] in pilot_ids
    return {"data_mode": "observed", "areas": areas,
            "geojson": {"type": "FeatureCollection", "features": list(boundaries.values())},
            "sources": manifest["sources"], "license_url": manifest["license_url"], "audit": audit,
            "population_year": 2020, "boundary_year": 2019, "mapping_limitation": LIMITATION,
            "review_scope": review["review_scope"],
            "population_note": "Census 2020 snapshot, not current population. Published age bands are rounded; sums may differ from totals."}
