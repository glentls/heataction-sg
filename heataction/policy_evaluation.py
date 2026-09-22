"""Retrospective comparison of allocation policies against a ground-truth heat signal.

This answers a narrower question than heataction.evaluation (which compares WBGT forecast
models): given a fixed team budget, does the shipped heat+demographic policy actually direct
teams toward areas that are genuinely in the High WBGT category more often than naive
alternatives would? Per DECISIONS.md #002, running this on synthetic data demonstrates the
method; it is not a real-world outreach-impact claim. Running it on observed data would need
enough station-hours of history to be statistically meaningful, which the project does not yet have.
"""
import random
from datetime import datetime

from .planner import build_plan, heat_category


def _latest_by_station(readings, as_of):
    latest = {}
    for row in readings:
        if row["source"] != "wbgt":
            continue
        observed_at = datetime.fromisoformat(row["observed_at"])
        if observed_at > as_of:
            continue
        previous = latest.get(row["station_id"])
        if previous is None or row["observed_at"] > previous["observed_at"]:
            latest[row["station_id"]] = row
    return latest


def ground_truth_high(areas, readings, as_of):
    """Areas whose station currently reads in the High WBGT category, independent of any policy."""
    latest = _latest_by_station(readings, as_of)
    high = set()
    for area in areas:
        observation = latest.get(area["station_id"])
        if observation is not None and heat_category(float(observation["value"])) == "High":
            high.add(area["area_id"])
    return high


def current_policy(areas, readings, as_of, budget, *, contacts=10, count_weight=0.5):
    """The policy the app actually ships: heataction.planner.build_plan, not a reimplementation."""
    plan = build_plan(areas, readings, as_of=as_of.isoformat(), budget=budget, contacts=contacts, count_weight=count_weight)
    return {row["area_id"] for row in plan["rows"] if row["assigned"]}


def population_only_policy(areas, readings, as_of, budget):
    """Ignores weather entirely: always sends teams to the areas with the most seniors."""
    ranked = sorted(areas, key=lambda area: (-area["seniors65"], area["area_id"]))
    return {area["area_id"] for area in ranked[:budget]}


def heat_only_policy(areas, readings, as_of, budget):
    """Ignores demographics entirely: always sends teams to the hottest currently-reporting areas."""
    latest = _latest_by_station(readings, as_of)

    def sort_key(area):
        observation = latest.get(area["station_id"])
        return (-float(observation["value"]) if observation else float("inf"), area["area_id"])
    ranked = sorted(areas, key=sort_key)
    return {area["area_id"] for area in ranked[:budget]}


def random_policy(areas, readings, as_of, budget, rng):
    ids = [area["area_id"] for area in areas]
    rng.shuffle(ids)
    return set(ids[:budget])


def round_robin_policy(areas, readings, as_of, budget, step):
    ids = sorted(area["area_id"] for area in areas)
    return {ids[(step + offset) % len(ids)] for offset in range(min(budget, len(ids)))}


POLICIES = ("current", "population_only", "heat_only", "random", "round_robin")


def compare_policies(areas, readings, *, budget=1, contacts=10, count_weight=0.5, seed=42):
    """Replays every observed WBGT timestamp and scores each policy against ground_truth_high.

    recall: of the timesteps where some area genuinely read High, the fraction where the
      policy's chosen area(s) included at least one of them.
    capacity_to_high: total assumed contact capacity the policy directed at genuinely-High
      areas, summed over the whole run — a coarse proxy for reach, not a count of people helped.
    """
    timestamps = sorted({row["observed_at"] for row in readings if row["source"] == "wbgt"})
    capacity_by_area = {area["area_id"]: min(contacts, area["seniors65"]) for area in areas}
    rng = random.Random(seed)
    stats = {name: {"assignments": 0, "high_opportunities": 0, "hits": 0, "capacity_to_high": 0}
             for name in POLICIES}
    for step, stamp in enumerate(timestamps):
        as_of = datetime.fromisoformat(stamp)
        high = ground_truth_high(areas, readings, as_of)
        choices = {
            "current": current_policy(areas, readings, as_of, budget, contacts=contacts, count_weight=count_weight),
            "population_only": population_only_policy(areas, readings, as_of, budget),
            "heat_only": heat_only_policy(areas, readings, as_of, budget),
            "random": random_policy(areas, readings, as_of, budget, rng),
            "round_robin": round_robin_policy(areas, readings, as_of, budget, step),
        }
        for name, chosen in choices.items():
            record = stats[name]
            record["assignments"] += len(chosen)
            record["capacity_to_high"] += sum(capacity_by_area[area_id] for area_id in chosen & high)
            if high:
                record["high_opportunities"] += 1
                if chosen & high:
                    record["hits"] += 1
    for record in stats.values():
        record["recall"] = record["hits"] / record["high_opportunities"] if record["high_opportunities"] else None
    return {"budget": budget, "count_weight": count_weight, "timesteps": len(timestamps),
            "high_opportunity_timesteps": stats["current"]["high_opportunities"], "policies": stats,
            "limitations": ["Synthetic data only; demonstrates the evaluation method, not a real-world impact claim",
                            "Ground truth is the same heat_category threshold the policy itself uses, not an independent severity measure",
                            "3 areas and 1 station per area; not a claim about performance at city scale",
                            "Recall/capacity are planning proxies; neither counts a person actually helped"]}
