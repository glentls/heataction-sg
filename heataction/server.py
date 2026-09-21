"""Loopback-only development server. Not intended for public deployment."""
import csv
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .planner import build_plan, validate_areas
from .sources import now_utc
from .storage import observations, recent_runs


def safe_csv(value):
    # Spreadsheet formula injection protection for externally sourced text.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_csv(plan):
    buf = io.StringIO(newline="")
    fields = ["data_mode", "as_of", "budget", "contacts_per_slot", "count_weight", "name", "assigned",
              "contact_capacity", "priority", "category", "status", "forecast_wbgt", "forecast_method",
              "forecast_target", "observed_at", "station_id", "population_year", "population_source", "mapping_method"]
    writer = csv.DictWriter(buf, fields)
    writer.writeheader()
    for row in plan["rows"]:
        if row["eligible"]:
            merged = {**plan, **row}
            writer.writerow({key: safe_csv(merged.get(key, "")) for key in fields})
    return buf.getvalue()


def serve(mode, port, area_path=None):
    root = Path(f"data/runtime/{mode}")
    if mode == "demo":
        if not (root / "mode.json").exists():
            raise ValueError("Run python -m heataction demo first")
        areas = json.loads((root / "areas.json").read_text(encoding="utf-8"))
        demo_time = json.loads((root / "mode.json").read_text())["as_of"]
    else:
        if area_path is None:
            areas = []  # Observation inspector works before demographics are ready.
        else:
            areas = json.loads(area_path.read_text(encoding="utf-8"))
        demo_time = None
    validate_areas(areas)

    class Handler(BaseHTTPRequestHandler):
        def send_body(self, body, mime, status=200, filename=None):
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            try:
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    return self.send_body((Path(__file__).parent / "web/index.html").read_text(encoding="utf-8"), "text/html")
                if parsed.path not in ("/api/plan", "/api/export"):
                    return self.send_body("Not found", "text/plain", 404)
                params = parse_qs(parsed.query, keep_blank_values=True)
                selected = params["areas"][0].split(",") if params.get("areas", [""])[0] else ([] if "areas" in params else None)
                locked = params.get("locked", [""])[0].split(",") if params.get("locked", [""])[0] else []
                readings = observations(root)
                plan = build_plan(areas, readings, as_of=demo_time or now_utc(),
                                  budget=int(params.get("budget", ["2"])[0]),
                                  contacts=int(params.get("contacts", ["10"])[0]),
                                  count_weight=float(params.get("weight", ["0.5"])[0]),
                                  selected=selected, locked=locked)
                latest = {}
                for record in readings:
                    latest[(record["source"], record["station_id"])] = record
                plan.update({"data_mode": "synthetic" if mode == "demo" else "observed",
                             "recent_runs": recent_runs(root), "latest_observations": list(latest.values()),
                             "has_areas": bool(areas)})
                if parsed.path == "/api/export":
                    return self.send_body(export_csv(plan), "text/csv", filename="heataction_plan.csv")
                self.send_body(json.dumps(plan, allow_nan=False), "application/json")
            except (ValueError, KeyError) as exc:
                self.send_body(json.dumps({"error": str(exc)}), "application/json", 400)
            except Exception:
                self.send_body(json.dumps({"error": "Unexpected local error; inspect the terminal and data files"}), "application/json", 500)
                raise

    print(f"HeatAction SG ({mode}) at http://127.0.0.1:{port} - Ctrl+C to stop", flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
