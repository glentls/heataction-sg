"""Crafted fixtures with a known correct answer, independent of the real demo dataset."""
import copy
import random as random_module
import unittest
from datetime import datetime, timedelta, timezone

from heataction.policy_evaluation import (compare_policies, current_policy, ground_truth_high,
                                          heat_only_policy, population_only_policy, random_policy,
                                          round_robin_policy)

AREAS = [
    {"area_id": "hot", "name": "Hot Area", "residents": 5000, "seniors65": 500,
     "population_year": 2020, "station_id": "HOT", "population_source": "Test fixture",
     "mapping_method": "Fictional", "mapping_verified": True},
    {"area_id": "cool", "name": "Cool Area", "residents": 5000, "seniors65": 4000,
     "population_year": 2020, "station_id": "COOL", "population_source": "Test fixture",
     "mapping_method": "Fictional", "mapping_verified": True},
]


def reading(station_id, value, stamp):
    return {"source": "wbgt", "station_id": station_id, "observed_at": stamp, "value": value}


def make_readings(count, interval_minutes=15):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    readings = []
    for i in range(count):
        stamp = (start + timedelta(minutes=interval_minutes * i)).isoformat()
        readings.append(reading("HOT", 34.0, stamp))
        readings.append(reading("COOL", 28.0, stamp))
    return readings


class PolicyEvaluationTests(unittest.TestCase):
    def test_ground_truth_and_individual_policies(self):
        readings = make_readings(1)
        as_of = datetime.fromisoformat(readings[0]["observed_at"])
        self.assertEqual(ground_truth_high(AREAS, readings, as_of), {"hot"})
        self.assertEqual(heat_only_policy(AREAS, readings, as_of, 1), {"hot"})
        # Population-only ignores heat entirely and always prefers the larger senior count.
        self.assertEqual(population_only_policy(AREAS, readings, as_of, 1), {"cool"})
        self.assertEqual(current_policy(AREAS, readings, as_of, 1), {"hot"})

    def test_compare_policies_separates_heat_aware_from_population_only(self):
        readings = make_readings(40)
        result = compare_policies(copy.deepcopy(AREAS), readings, budget=1)
        self.assertEqual(result["high_opportunity_timesteps"], 40)
        self.assertEqual(result["policies"]["current"]["recall"], 1.0)
        self.assertEqual(result["policies"]["heat_only"]["recall"], 1.0)
        self.assertEqual(result["policies"]["population_only"]["recall"], 0.0)
        self.assertGreater(result["policies"]["current"]["capacity_to_high"], 0)
        self.assertEqual(result["policies"]["population_only"]["capacity_to_high"], 0)
        for name in ("random", "round_robin"):
            recall = result["policies"][name]["recall"]
            self.assertIsNotNone(recall)
            self.assertGreaterEqual(recall, 0)
            self.assertLessEqual(recall, 1)
        for name, stats in result["policies"].items():
            self.assertEqual(stats["assignments"], 40, name)

    def test_round_robin_and_random_respect_budget(self):
        readings = make_readings(1)
        as_of = datetime.fromisoformat(readings[0]["observed_at"])
        self.assertEqual(len(round_robin_policy(AREAS, readings, as_of, 1, step=0)), 1)
        self.assertEqual(len(round_robin_policy(AREAS, readings, as_of, 2, step=0)), 2)
        self.assertEqual(len(random_policy(AREAS, readings, as_of, 1, random_module.Random(1))), 1)

    def test_no_opportunities_yields_none_recall(self):
        readings = [reading("HOT", 28.0, "2026-01-01T00:00:00+00:00"),
                    reading("COOL", 27.0, "2026-01-01T00:00:00+00:00")]
        result = compare_policies(copy.deepcopy(AREAS), readings, budget=1)
        self.assertEqual(result["high_opportunity_timesteps"], 0)
        for stats in result["policies"].values():
            self.assertIsNone(stats["recall"])


if __name__ == "__main__":
    unittest.main()
