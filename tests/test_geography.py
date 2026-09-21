"""Observed source contracts plus explicitly constructed failure cases."""
import copy
import csv
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from heataction.geography import (AGE_COLUMNS, REFERENCE_ROOT, build_pilot, contains,
                                  load_boundaries, parse_census)
from heataction.planner import build_plan


def census_text(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, ["Number", "Total_Total", *AGE_COLUMNS])
    writer.writeheader()
    for label, total, updates in rows:
        writer.writerow({"Number": label, "Total_Total": total,
                         **{column: "10" for column in AGE_COLUMNS}, **updates})
    return stream.getvalue()


class GeographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = build_pilot()

    def test_actual_snapshots_join_expected_totals_and_boundaries(self):
        self.assertEqual(len(self.pilot["geojson"]["features"]), 55)
        expected = {"am": (162280, 35220, "S141"), "bd": (276990, 53370, "S129"),
                    "jw": (262730, 33730, "S132")}
        for area in self.pilot["areas"]:
            self.assertEqual((area["residents"], area["seniors65"], area["station_id"]), expected[area["area_id"]])
            self.assertEqual(area["population_year"], 2020)
            self.assertEqual(area["boundary_year"], 2019)
            self.assertIn("Technical", area["mapping_review_scope"])
        self.assertTrue(all(row["station_inside_boundary"] for row in self.pilot["audit"]))

    def test_census_uses_only_area_totals_and_total_sex_age_bands(self):
        result = parse_census(census_text([("Total", "999999", {}), ("Test - Total", "300", {}),
                                         ("Subzone", "100", {})]))
        self.assertEqual(list(result), ["TEST"])
        self.assertEqual(result["TEST"]["seniors65"], 60)
        self.assertEqual(result["TEST"]["residents"], 300)

    def test_missing_population_is_not_zero_and_duplicate_totals_fail(self):
        result = parse_census(census_text([("Test - Total", "300", {"Total_65_69": ""})]))
        self.assertIsNone(result["TEST"]["seniors65"])
        self.assertIsNone(result["TEST"]["senior_share"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            parse_census(census_text([("Test - Total", "300", {}), ("TEST - Total", "300", {})]))
        with self.assertRaisesRegex(ValueError, "schema"):
            parse_census("Number,Total_Total\nTest - Total,300\n")

    def test_invalid_population_fails(self):
        for total in ("-1", "3.5", "not a count"):
            with self.assertRaises(ValueError):
                parse_census(census_text([("Test - Total", total, {})]))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            parse_census(census_text([("Test - Total", "20", {})]))

    def test_containment_handles_holes_multipolygons_and_edges(self):
        outer = [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]
        hole = [[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]
        geometry = {"type": "Polygon", "coordinates": [outer, hole]}
        self.assertTrue(contains(geometry, 3, 3))
        self.assertTrue(contains(geometry, 0, 3))
        self.assertFalse(contains(geometry, 1.5, 1.5))
        self.assertFalse(contains(geometry, 8, 8))
        multi = {"type": "MultiPolygon", "coordinates": [[outer, hole], [[[6, 6], [7, 6], [7, 7], [6, 6]]]]}
        self.assertTrue(contains(multi, 6.7, 6.3))

    def test_boundary_duplicate_and_wrong_coordinate_system_fail(self):
        payload = json.loads((REFERENCE_ROOT / "planning_areas_2019.geojson").read_text())
        payload["features"].append(copy.deepcopy(payload["features"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_boundaries(payload)
        payload["features"] = payload["features"][:1]
        payload["features"][0]["geometry"]["coordinates"][0][1] = [30000, 40000]
        with self.assertRaisesRegex(ValueError, "longitude/latitude"):
            load_boundaries(payload)

    def test_modified_snapshot_and_outside_station_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in REFERENCE_ROOT.iterdir():
                if path.is_file():
                    shutil.copyfile(path, root / path.name)
            source = root / "census2020_age.csv"
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                build_pilot(root)
            shutil.copyfile(REFERENCE_ROOT / source.name, source)
            path = root / "pilot_mappings.json"
            mappings = json.loads(path.read_text())
            mappings["mappings"][0]["station"]["latitude"] = 1.1
            path.write_text(json.dumps(mappings))
            with self.assertRaisesRegex(ValueError, "outside"):
                build_pilot(root)

    def test_real_areas_gate_missing_stale_and_moved_weather(self):
        areas = self.pilot["areas"]
        stamp = "2026-09-21T07:00:00+00:00"
        # Artificial hot readings for policy regression only; never stored as observed data.
        readings = [{"source": "wbgt", "station_id": area["station_id"], "observed_at": stamp,
                     "value": 33.6, "latitude": area["station_latitude"], "longitude": area["station_longitude"]}
                    for area in areas]
        self.assertEqual(build_plan(areas, [], as_of=stamp)["assigned_slots"], 0)
        self.assertEqual(build_plan(areas, readings, as_of=stamp, budget=2)["assigned_slots"], 2)
        stale = build_plan(areas, readings, as_of="2026-09-21T08:00:00+00:00")
        self.assertEqual(stale["assigned_slots"], 0)
        readings[0]["latitude"] += .02
        moved = build_plan(areas, readings, as_of=stamp, budget=3)
        row = next(r for r in moved["rows"] if r["area_id"] == "am")
        self.assertEqual(row["status"], "Station moved; mapping review needed")
        self.assertFalse(row["assigned"])
        self.assertEqual(row["category"], "Unknown")


class PilotHTTPTests(unittest.TestCase):
    def test_observed_map_works_without_weather_and_cannot_mix_with_demo(self):
        project = Path(__file__).resolve().parents[1]
        invalid = subprocess.run([sys.executable, "-m", "heataction", "serve", "--pilot"],
                                 cwd=project, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("requires --mode observed", invalid.stderr)
        with tempfile.TemporaryDirectory() as directory:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            env = {**os.environ, "PYTHONPATH": str(project)}
            process = subprocess.Popen([sys.executable, "-m", "heataction", "serve", "--mode", "observed",
                                        "--pilot", "--port", str(port)], cwd=directory, env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                base = f"http://127.0.0.1:{port}"
                for _ in range(50):
                    try:
                        with urlopen(base + "/api/plan", timeout=1) as response:
                            plan = json.load(response)
                        break
                    except URLError:
                        if process.poll() is not None:
                            self.fail("Pilot server exited during startup")
                        time.sleep(.1)
                else:
                    self.fail("Pilot server did not start")
                self.assertEqual(plan["data_mode"], "observed")
                self.assertTrue(plan["has_geography"])
                self.assertEqual(len(plan["rows"]), 3)
                self.assertEqual(plan["assigned_slots"], 0)
                self.assertTrue(all(row["status"] == "No observation" for row in plan["rows"]))
                with urlopen(base + "/api/geography") as response:
                    geography = json.load(response)
                self.assertEqual(len(geography["geojson"]["features"]), 55)
                for route, mime in (("/map.js", "application/javascript"), ("/map.css", "text/css")):
                    with urlopen(base + route) as response:
                        self.assertIn(mime, response.headers["Content-Type"])
                with urlopen(base + "/api/export") as response:
                    rows = list(csv.DictReader(io.StringIO(response.read().decode())))
                self.assertEqual({r["population_year"] for r in rows}, {"2020"})
                self.assertTrue(all(r["boundary_dataset_id"] and r["mapping_review_scope"] for r in rows))
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/plan?areas=demo_north")
                self.assertEqual(error.exception.code, 400)
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
