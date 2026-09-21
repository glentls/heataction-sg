"""Optional station-level experiment. App v0.1 intentionally serves persistence."""
from datetime import datetime, timedelta
from collections import defaultdict
import math
import statistics


def supervised_examples(observations):
    series = {}
    for row in observations:
        if row["source"] == "wbgt":
            series[(row["station_id"], datetime.fromisoformat(row["observed_at"]))] = float(row["value"])
    stations = sorted({s for s, _ in series})
    examples = []
    for (station, stamp), value in sorted(series.items(), key=lambda pair: (pair[0][1], pair[0][0])):
        previous = series.get((station, stamp - timedelta(minutes=15)))
        hour_ago = series.get((station, stamp - timedelta(hours=1)))
        target_time = stamp + timedelta(hours=1)
        target = series.get((station, target_time))
        if None in (previous, hour_ago, target):
            continue
        minutes = ((stamp.hour + 8) % 24) * 60 + stamp.minute
        angle = minutes * 2 * math.pi / 1440
        features = [value, value - previous, value - hour_ago, math.sin(angle), math.cos(angle)]
        features += [int(station == s) for s in stations]
        examples.append({"station_id": station, "issued_at": stamp, "target_at": target_time,
                         "value": value, "target": target, "features": features,
                         "season_key": (station, target_time.hour, target_time.minute)})
    return examples


def chronological_split(examples):
    times = sorted({x["issued_at"] for x in examples})
    if len(times) < 96 or times[-1] - times[0] < timedelta(days=7):
        raise ValueError("Collect at least 7 days of usable history before this exploratory experiment")
    validation_start = times[int(len(times) * 0.6)]
    test_start = times[int(len(times) * 0.8)]
    train = [x for x in examples if x["target_at"] < validation_start]
    validation = [x for x in examples if x["issued_at"] >= validation_start and x["target_at"] < test_start]
    test = [x for x in examples if x["issued_at"] >= test_start]
    if min(len(train), len(validation), len(test)) < 20:
        raise ValueError("Insufficient examples after temporal embargo")
    return train, validation, test


def metrics(actual, predicted):
    mae = statistics.mean(abs(a - p) for a, p in zip(actual, predicted))
    true_high = sum(a >= 33 for a in actual)
    predicted_high = sum(p >= 33 for p in predicted)
    tp = sum(a >= 33 and p >= 33 for a, p in zip(actual, predicted))
    return {"mae_wbgt_c": mae, "high_heat_recall": tp / true_high if true_high else None,
            "high_heat_precision": tp / predicted_high if predicted_high else None,
            "high_heat_count": true_high, "samples": len(actual)}


def evaluate(observations, *, mode):
    from sklearn.ensemble import HistGradientBoostingRegressor
    examples = supervised_examples(observations)
    train, validation, test = chronological_split(examples)
    seasonal = defaultdict(list)
    for item in train:
        seasonal[item["season_key"]].append(item["target"])
    seasonal_mean = {key: statistics.mean(values) for key, values in seasonal.items()}
    model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15, random_state=42, early_stopping=False)
    model.fit([x["features"] for x in train], [x["target"] for x in train])

    def predictions(rows):
        return {
            "persistence": [x["value"] for x in rows],
            "time_of_day": [seasonal_mean.get(x["season_key"], x["value"]) for x in rows],
            "gradient_boosting": model.predict([x["features"] for x in rows]).tolist(),
        }
    valid_predictions = predictions(validation)
    validation_metrics = {name: metrics([x["target"] for x in validation], p) for name, p in valid_predictions.items()}
    chosen = min(validation_metrics, key=lambda name: validation_metrics[name]["mae_wbgt_c"])
    test_predictions = predictions(test)
    test_metrics = {name: metrics([x["target"] for x in test], p) for name, p in test_predictions.items()}
    by_station = {}
    for station in sorted({x["station_id"] for x in test}):
        ids = [i for i, x in enumerate(test) if x["station_id"] == station]
        by_station[station] = metrics([test[i]["target"] for i in ids], [test_predictions[chosen][i] for i in ids])
    return {"data_mode": mode, "selected_using": "validation MAE only", "chosen_model": chosen,
            "train_samples": len(train), "validation": validation_metrics, "test": test_metrics,
            "selected_model_test_by_station": by_station,
            "split_dates": {"train_last_target": train[-1]["target_at"].isoformat(),
                            "validation_first_issue": validation[0]["issued_at"].isoformat(),
                            "validation_last_target": validation[-1]["target_at"].isoformat(),
                            "test_first_issue": test[0]["issued_at"].isoformat()},
            "limitations": ["Exploratory single temporal holdout; no uncertainty intervals",
                            "WBGT-only model; rainfall is ingested but is not yet a feature",
                            "Latest corrected observations are not a full as-published historical reconstruction",
                            "Experiment does not replace the app's persistence forecast",
                            "Synthetic results demonstrate code execution only" if mode == "synthetic" else "Requires seasonally representative external validation"]}
