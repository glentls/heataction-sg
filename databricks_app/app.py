"""HeatAction SG Databricks App: a read-only view of the Gold area priority plan.

This is a hosted, read-only companion to the interactive local server (heataction/server.py),
not a replacement for it. It has no lock/scenario-compare controls; it only reads the tables that
notebooks/01_ingest_databricks.py and notebooks/03_geography_and_plan_databricks.py already wrote.
Unlike the local server, this binds 0.0.0.0 deliberately: Databricks Apps are reachable only through
the platform's own authenticated reverse proxy, not the public internet directly.
"""
import html
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from databricks import sql
from databricks.sdk.core import Config

CATALOG = os.environ.get("HEATACTION_CATALOG", "workspace")
WAREHOUSE_ID = os.environ["HEATACTION_WAREHOUSE_ID"]
PORT = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))
CONFIG = Config()


def query(statement):
    hostname = urlparse(CONFIG.host).netloc or CONFIG.host
    with sql.connect(server_hostname=hostname, http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
                      credentials_provider=lambda: CONFIG.authenticate) as connection:
        with connection.cursor() as cursor:
            cursor.execute(statement)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def esc(value):
    return "&mdash;" if value is None else html.escape(str(value))


def format_row(row):
    wbgt = "Unavailable" if row["forecast_wbgt"] is None else f"{row['forecast_wbgt']:.1f} °C"
    priority = "—" if row["priority"] is None else f"{row['priority']:.2f}"
    plan = "Assigned" if row["assigned"] else "No extra slot"
    return (f"<tr><td><strong>{esc(row['name'])}</strong><br><small>{esc(row['status'])}</small></td>"
            f"<td>{wbgt}</td><td>{esc(row['category'])}</td><td>{priority}</td><td>{plan}</td></tr>")


def render_page():
    plan_rows = query(f"SELECT * FROM {CATALOG}.heataction_gold.area_priority_plan ORDER BY area_id")
    demo_count = query(f"SELECT count(*) AS n FROM {CATALOG}.heataction_silver.area_demographics")[0]["n"]
    issued_at = plan_rows[0]["issued_at"] if plan_rows else None
    budget = plan_rows[0]["budget"] if plan_rows else None
    assigned = sum(1 for row in plan_rows if row["assigned"])
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body_rows = "".join(format_row(row) for row in plan_rows) or "<tr><td colspan=5>No plan rows yet. Run 03_geography_and_plan_databricks.</td></tr>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HeatAction SG (Databricks)</title>
<style>
body{{margin:0;background:#f3f6f4;color:#17363d;font:16px/1.5 system-ui,sans-serif}}
header{{background:#12383e;color:white;padding:20px}}h1{{margin:0;font-size:24px}}
main{{max-width:900px;margin:auto;padding:24px}}
.notice{{padding:12px 16px;background:#fff2ce;border-left:4px solid #c18600;margin-bottom:20px}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:10px 8px;text-align:left;border-bottom:1px solid #d9e3df}}
th{{font-size:12px;text-transform:uppercase;color:#52666c}}small{{color:#52666c}}
</style></head><body>
<header><h1>HeatAction SG &mdash; Databricks read-only view</h1></header>
<main>
<div class="notice">OBSERVED DATA served from Unity Catalog Gold tables (catalog <code>{esc(CATALOG)}</code>), not the interactive local planner.
Plan last materialised: {esc(issued_at)}. Page rendered: {esc(generated_at)}. Only the {len(plan_rows)} pilot area(s) out of {esc(demo_count)}
reviewed planning areas are planned here; the rest have demographic context only. Locking and scenario comparison are only in the local app.</div>
<p><strong>{assigned}</strong> of <strong>{esc(budget)}</strong> team slots assigned right now.</p>
<table><thead><tr><th>Area</th><th>WBGT forecast</th><th>Category</th><th>Priority</th><th>Plan</th></tr></thead>
<tbody>{body_rows}</tbody></table>
<p><small>Forecast is a one-hour persistence baseline, not trained AI. Priority is a planning proxy, not an individual illness-risk score.
Refresh this page to re-query the tables; it does not push live updates on its own.</small></p>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = render_page().encode("utf-8")
            status, content_type = 200, "text/html; charset=utf-8"
        except Exception as exc:
            data = f"<p>Could not load the plan: {html.escape(str(exc))}</p>".encode("utf-8")
            status, content_type = 500, "text/html; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"HeatAction SG Databricks App listening on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
