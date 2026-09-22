"""Run with python -m heataction from the project directory."""
import argparse
import json
import sys
from pathlib import Path

from .sources import fetch_pages, normalize, save_raw
from .storage import observations, upsert, log_run


def main():
    parser = argparse.ArgumentParser(description="HeatAction SG development commands")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Create isolated synthetic demo data")
    sub.add_parser("check-areas", help="Verify bundled observed Census/URA sources and pilot station mappings")
    ingest = sub.add_parser("ingest", help="Fetch public API observations; never substitutes demo data")
    ingest.add_argument("--source", choices=["all", "wbgt", "rainfall"], default="all")
    ingest.add_argument("--date", help="SGT YYYY-MM-DD; verify source history support before bulk backfill")
    ingest.add_argument("--data-dir", type=Path, default=Path("data/runtime/observed"))
    serve = sub.add_parser("serve", help="Start local app at http://127.0.0.1:8000")
    serve.add_argument("--mode", choices=["demo", "observed"], default="demo")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--areas", type=Path, help="Reviewed area/station mapping JSON for observed mode")
    serve.add_argument("--pilot", action="store_true", help="Load the reviewed three-area Census 2020 / MP2019 pilot and map (observed mode only)")
    evaluate = sub.add_parser("evaluate", help="Run exploratory chronological model comparison")
    evaluate.add_argument("--mode", choices=["demo", "observed"], default="demo")
    compare = sub.add_parser("compare-policies", help="Backtest the allocation policy against naive baselines")
    compare.add_argument("--mode", choices=["demo", "observed"], default="demo")
    compare.add_argument("--budget", type=int, default=1)
    compare.add_argument("--count-weight", type=float, default=0.5)
    compare.add_argument("--contacts", type=int, default=10)
    args = parser.parse_args()
    try:
        if args.command == "demo":
            from .demo import seed
            count = seed(Path("data/runtime/demo"))
            print(f"Prepared {count} synthetic observations. Run: python -m heataction serve")
        elif args.command == "check-areas":
            from .geography import build_pilot
            pilot = build_pilot()
            print(json.dumps({"data_mode": pilot["data_mode"], "sources": pilot["sources"],
                              "review_scope": pilot["review_scope"], "audit": pilot["audit"]}, indent=2))
        elif args.command == "ingest":
            failures = []
            for source in (["wbgt", "rainfall"] if args.source == "all" else [args.source]):
                count, bad = 0, 0
                try:
                    for envelope in fetch_pages(source, args.date):
                        raw_path = save_raw(envelope, args.data_dir)
                        rows, rejected = normalize(source, envelope["payload"], envelope["retrieved_at"])
                        if rejected:
                            raw_path.with_suffix(".rejected.json").write_text(json.dumps(rejected, indent=2), encoding="utf-8")
                        upsert(args.data_dir, rows)
                        count += len(rows)
                        bad += len(rejected)
                    log_run(args.data_dir, source, "ok" if count else "empty", count, bad)
                    print(f"{source}: {count} valid rows processed, {bad} quarantined. Reruns upsert existing keys.")
                except Exception as exc:
                    log_run(args.data_dir, source, "failed", count, bad, str(exc))
                    failures.append(f"{source}: {exc}")
            if failures:
                raise RuntimeError("; ".join(failures))
        elif args.command == "serve":
            from .server import serve
            serve(args.mode, args.port, args.areas, pilot=args.pilot)
        elif args.command == "evaluate":
            from .evaluation import evaluate
            report = evaluate(observations(Path(f"data/runtime/{args.mode}")),
                              mode="synthetic" if args.mode == "demo" else "observed")
            path = Path("artifacts") / f"evaluation_{args.mode}.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
            print(json.dumps(report, indent=2))
            print(f"Saved {path}")
        else:
            from .policy_evaluation import compare_policies
            if args.mode == "demo":
                from .demo import DEMO_AREAS
                areas = DEMO_AREAS
            else:
                from .geography import build_pilot
                areas = build_pilot()["areas"]
            report = compare_policies(areas, observations(Path(f"data/runtime/{args.mode}")),
                                      budget=args.budget, contacts=args.contacts, count_weight=args.count_weight)
            path = Path("artifacts") / f"policy_comparison_{args.mode}.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
            print(json.dumps(report, indent=2))
            print(f"Saved {path}")
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
