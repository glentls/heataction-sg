import copy
import csv
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from heataction.demo import DEMO_AREAS
from heataction.sources import normalize, utc_time, fetch_pages
from heataction.storage import upsert, observations, save_lock_reason, delete_lock_reason, lock_reasons
from heataction.planner import build_plan, heat_category
from heataction.evaluation import supervised_examples, chronological_split
from heataction.server import safe_csv

STAMP = "2026-09-21T06:00:00+00:00"


def wbgt_payload(value="33.6"):
    return {"code": 0, "data": {"records": [{"datetime": STAMP, "updatedTimestamp": STAMP,
        "item": {"type": "observation", "isStationData": True, "readings": [{
            "station": {"id": "DEMO_N", "name": "Synthetic station"},
            "location": {"latitude": "1.4", "longitude": "103.8"}, "wbgt": value, "heatStress": "High"}]}}]}}


def sample_rows():
    result = []
    for area, value in zip(DEMO_AREAS, (33.6, 32.1, 31.8)):
        row = normalize("wbgt", wbgt_payload(value), STAMP)[0][0]
        row["station_id"] = area["station_id"]
        result.append(row)
    return result


class SourceTests(unittest.TestCase):
    def test_parsers_accept_frozen_real_public_responses(self):
        fixtures = Path(__file__).parent / "fixtures"
        for source in ("wbgt", "rainfall"):
            payload = json.loads((fixtures / f"{source}_observed.json").read_text())["payload"]
            rows, rejects = normalize(source, payload, "2026-09-21T07:00:00+00:00")
            self.assertGreater(len(rows), 10)
            self.assertEqual(rejects, [])
            self.assertFalse(any(r["station_id"].startswith("DEMO") for r in rows))

    def test_wbgt_contract_converts_strings_and_timezones(self):
        payload = wbgt_payload()
        payload["data"]["records"][0]["datetime"] = "2026-09-21T14:00:00+08:00"
        rows, rejects = normalize("wbgt", payload, STAMP)
        self.assertEqual(rows[0]["observed_at"], STAMP)
        self.assertEqual(rows[0]["value"], 33.6)
        self.assertEqual(rejects, [])

    def test_missing_and_nan_are_quarantined(self):
        for value in (None, "na", "NaN", "Infinity", True):
            rows, rejects = normalize("wbgt", wbgt_payload(value), STAMP)
            self.assertEqual(rows, [])
            self.assertEqual(len(rejects), 1)

    def test_rainfall_zero_is_not_missing(self):
        payload = {"code": 0, "data": {"stations": [{"id": "R", "name": "Rain", "location": {"latitude": 1.3, "longitude": 103.8}}],
                   "readings": [{"timestamp": STAMP, "data": [{"stationId": "R", "value": 0}]}], "readingUnit": "mm"}}
        rows, rejects = normalize("rainfall", payload, STAMP)
        self.assertEqual(rows[0]["value"], 0)
        self.assertEqual(rejects, [])
        payload["data"]["readings"][0]["data"][0]["stationId"] = "UNKNOWN"
        self.assertEqual(len(normalize("rainfall", payload, STAMP)[1]), 1)

    def test_unknown_schema_fails(self):
        with self.assertRaises(ValueError):
            normalize("wbgt", {"code": 0, "data": {"new_shape": []}}, STAMP)
        with self.assertRaises(ValueError):
            utc_time("2026-09-21T06:00:00")

    def test_pagination_loop_fails(self):
        payload = {"code": 0, "data": {"paginationToken": "same"}}
        with patch("heataction.sources.request_json", return_value=payload):
            with self.assertRaises(ValueError):
                list(fetch_pages("rainfall", "2026-09-20"))

    def test_upsert_is_idempotent_and_newer_correction_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = sample_rows()[0]
            upsert(root, [row, row])
            self.assertEqual(len(observations(root)), 1)
            correction = {**row, "value": 32.0, "source_updated_at": "2026-09-21T06:10:00+00:00"}
            upsert(root, [correction])
            upsert(root, [row])
            self.assertEqual(observations(root)[0]["value"], 32.0)

    def test_lock_reasons_upsert_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(lock_reasons(root), {})
            save_lock_reason(root, "demo_east", "Clinic visit scheduled 3pm")
            saved = lock_reasons(root)
            self.assertEqual(saved["demo_east"]["reason"], "Clinic visit scheduled 3pm")
            self.assertTrue(saved["demo_east"]["recorded_at"])
            save_lock_reason(root, "demo_east", "Updated: volunteer confirmed")
            self.assertEqual(lock_reasons(root)["demo_east"]["reason"], "Updated: volunteer confirmed")
            self.assertEqual(len(lock_reasons(root)), 1)
            delete_lock_reason(root, "demo_east")
            self.assertEqual(lock_reasons(root), {})
            delete_lock_reason(root, "never_saved")


class PlannerTests(unittest.TestCase):
    def plan(self, **kwargs):
        return build_plan(copy.deepcopy(DEMO_AREAS), sample_rows(), as_of=STAMP, **kwargs)

    def test_budget_service_area_and_fixed_reference_cohort(self):
        full = self.plan(budget=1)
        selected = self.plan(budget=3, selected=["demo_east"])
        self.assertEqual(full["assigned_slots"], 1)
        self.assertEqual(selected["assigned_slots"], 1)
        full_east = next(r for r in full["rows"] if r["area_id"] == "demo_east")
        filtered_east = next(r for r in selected["rows"] if r["area_id"] == "demo_east")
        self.assertEqual(full_east["priority"], filtered_east["priority"])
        self.assertEqual(self.plan(budget=3, selected=[])["assigned_slots"], 0)

    def test_missing_stale_future_are_not_low(self):
        for readings, as_of in [([], STAMP), (sample_rows(), "2026-09-21T08:00:00+00:00"),
                                (sample_rows(), "2026-09-21T05:00:00+00:00")]:
            result = build_plan(DEMO_AREAS, readings, as_of=as_of)
            self.assertEqual(result["assigned_slots"], 0)
            self.assertTrue(all(r["category"] == "Unknown" for r in result["rows"]))

    def test_zero_budget_and_low_heat_do_not_force_allocation(self):
        self.assertEqual(self.plan(budget=0)["assigned_slots"], 0)
        low = [{**r, "value": 28.0} for r in sample_rows()]
        self.assertEqual(build_plan(DEMO_AREAS, low, as_of=STAMP)["assigned_slots"], 0)

    def test_mapping_gate_and_invalid_locks(self):
        areas = copy.deepcopy(DEMO_AREAS)
        areas[0]["mapping_verified"] = False
        plan = build_plan(areas, sample_rows(), as_of=STAMP)
        self.assertFalse(next(r for r in plan["rows"] if r["area_id"] == "demo_north")["assigned"])
        with self.assertRaises(ValueError):
            self.plan(budget=0, locked=["demo_north"])
        with self.assertRaises(ValueError):
            self.plan(budget=2, selected=["demo_east"], locked=["demo_north"])
        self.assertTrue(next(r for r in self.plan(budget=1, locked=["demo_east"])["rows"] if r["area_id"] == "demo_east")["assigned"])

    def test_capacity_cannot_exceed_demographic_count(self):
        plan = self.plan(budget=3, contacts=100000)
        for row in plan["rows"]:
            self.assertLessEqual(row["contact_capacity"], row["seniors65"])

    def test_threshold_boundaries_and_invalid_weight(self):
        self.assertEqual([heat_category(v) for v in (30.99, 31, 32.99, 33)], ["Low", "Moderate", "Moderate", "High"])
        with self.assertRaises(ValueError):
            self.plan(count_weight=float("nan"))
        with self.assertRaises(ValueError):
            self.plan(budget=-1)


class ForecastTests(unittest.TestCase):
    def test_exact_target_does_not_bridge_missing_timestamp(self):
        start = datetime(2026, 9, 1, tzinfo=timezone.utc)
        rows = [{"source": "wbgt", "station_id": "X", "value": 30 + i / 100,
                 "observed_at": (start + timedelta(minutes=15 * i)).isoformat()} for i in range(20)]
        all_examples = supervised_examples(rows)
        self.assertTrue(all(x["target_at"] - x["issued_at"] == timedelta(hours=1) for x in all_examples))
        missing = rows[12]["observed_at"]
        incomplete = supervised_examples([r for r in rows if r["observed_at"] != missing])
        self.assertFalse(any(x["target_at"].isoformat() == missing for x in incomplete))

    def test_temporal_boundaries_exclude_crossing_targets(self):
        start = datetime(2026, 9, 1, tzinfo=timezone.utc)
        examples = [{"issued_at": start + timedelta(minutes=15 * i),
                     "target_at": start + timedelta(minutes=15 * i + 60)} for i in range(1000)]
        train, validation, test = chronological_split(examples)
        self.assertLess(max(x["target_at"] for x in train), min(x["issued_at"] for x in validation))
        self.assertLess(max(x["target_at"] for x in validation), min(x["issued_at"] for x in test))

    def test_csv_formula_escaping(self):
        self.assertTrue(safe_csv(" =HYPERLINK(x)").startswith("'"))
        self.assertEqual(safe_csv("Demo North"), "Demo North")


class ServerLockTests(unittest.TestCase):
    def test_locks_require_a_reason_and_flow_into_plan_and_export(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "PYTHONPATH": str(project)}
            demo = subprocess.run([sys.executable, "-m", "heataction", "demo"], cwd=directory, env=env,
                                  capture_output=True, text=True, timeout=30)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            process = subprocess.Popen([sys.executable, "-m", "heataction", "serve", "--mode", "demo",
                                        "--port", str(port)], cwd=directory, env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                base = f"http://127.0.0.1:{port}"
                for _ in range(50):
                    try:
                        with urlopen(base + "/api/plan", timeout=1):
                            break
                    except URLError:
                        if process.poll() is not None:
                            self.fail("Demo server exited during startup")
                        time.sleep(.1)
                else:
                    self.fail("Demo server did not start")

                # demo_north is High-category in the fixed demo snapshot, so it carries positive
                # allocation value and is a valid lock target; demo_east's Low reading is not.
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/plan?locked=demo_north")
                self.assertEqual(error.exception.code, 400)

                def api(path, payload=None, method=None):
                    data = json.dumps(payload).encode() if payload is not None else None
                    request = Request(base + path, data=data, method=method,
                                      headers={"Content-Type": "application/json"} if data else {})
                    return urlopen(request)

                with self.assertRaises(HTTPError) as error:
                    api("/api/locks", {"area_id": "demo_north", "reason": "   "}, "POST")
                self.assertEqual(error.exception.code, 400)
                with self.assertRaises(HTTPError) as error:
                    api("/api/locks", {"area_id": "not_a_real_area", "reason": "Clinic visit"}, "POST")
                self.assertEqual(error.exception.code, 400)

                with api("/api/locks", {"area_id": "demo_north", "reason": "Clinic visit scheduled 3pm"}, "POST") as response:
                    saved = json.load(response)
                self.assertEqual(saved["demo_north"]["reason"], "Clinic visit scheduled 3pm")
                with api("/api/locks") as response:
                    self.assertIn("demo_north", json.load(response))

                with api("/api/plan?budget=1&locked=demo_north") as response:
                    plan = json.load(response)
                north = next(r for r in plan["rows"] if r["area_id"] == "demo_north")
                self.assertTrue(north["locked"] and north["assigned"])
                self.assertEqual(north["lock_reason"], "Clinic visit scheduled 3pm")

                with api("/api/export?budget=1&locked=demo_north") as response:
                    rows = list(csv.DictReader(io.StringIO(response.read().decode())))
                exported = next(r for r in rows if r["area_id"] == "demo_north")
                self.assertEqual(exported["lock_reason"], "Clinic visit scheduled 3pm")
                self.assertEqual(exported["locked"], "True")

                with api("/api/locks?area_id=demo_north", method="DELETE") as response:
                    self.assertTrue(json.load(response)["deleted"])
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/plan?locked=demo_north")
                self.assertEqual(error.exception.code, 400)
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
