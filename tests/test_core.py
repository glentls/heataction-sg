import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from heataction.demo import DEMO_AREAS
from heataction.sources import normalize, utc_time, fetch_pages
from heataction.storage import upsert, observations
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


if __name__ == "__main__":
    unittest.main()
