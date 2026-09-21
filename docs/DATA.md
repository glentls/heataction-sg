# Data register and contracts

Reviewed on 21 September 2026. The app keeps raw source observations separate from demographic assumptions and synthetic demonstration data.

| Source | Reference | Implementation |
|---|---|---|
| WBGT | [NEA catalogue](https://data.gov.sg/datasets/d_87884af1f85d702d4f74c6af13b4853d/view) | Collector and station parser implemented. Working response inspected through public web retrieval. |
| Rainfall | [NEA catalogue](https://data.gov.sg/datasets/d_6580738cdd7db79374ed3152159fbd69/view) | Collector and parser implemented. Working response inspected through public web retrieval. |
| Age profiles | [Census 2020](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view) | Official CSV snapshot, strict area-total parser and pilot integration implemented. |
| Boundaries | [URA Master Plan 2019](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) | Official GeoJSON snapshot; all 55 boundaries rendered and three station containment checks implemented. |

## API contracts

WBGT endpoint: `https://api-open.data.gov.sg/v2/real-time/api/weather?api=wbgt`.
Expected payload: `code=0`, then `data.records[]`, each containing `datetime`, `updatedTimestamp`, and `item` with `type=observation`, `isStationData=true`, and `readings[]`. Each reading supplies `station.id`, `station.name`, `location.latitude`, `location.longitude`, `wbgt`, and `heatStress`.

Rainfall endpoint: `https://api-open.data.gov.sg/v2/real-time/api/rainfall`.
Expected payload: `code=0`, `data.stations[]`, `data.readings[].timestamp`, `data.readings[].data[]` containing `stationId` and `value`, and `readingUnit=mm`.

The collector supports a date parameter and pagination tokens. The history route and retention period must be demonstrated in the user's environment before bulk backfill. Unexpected response shapes raise errors. Invalid individual records are quarantined. An API error never switches to synthetic mode.

An API key is optional. If needed, set `DATA_GOV_SG_API_KEY` in your process environment. It is sent only to the configured source request and is never written to raw snapshots. See [data.gov.sg API overview](https://guide.data.gov.sg/developer-guide/api-overview).

## WBGT category version

The [June 2026 official advisory](https://www.weather.gov.sg/wp-content/uploads/2026/06/Manage-HeatStress-Eng_updated.pdf) defines Low below 31 C, Moderate from 31 C up to but excluding 33 C, and High at or above 33 C. These are WBGT categories for general-population prolonged outdoor activity. They do not classify individual clinical risk. The planner's additional demographic weights are our own policy assumptions.

## Real area configuration

The bundled pilot can be loaded with `serve --mode observed --pilot --port 8001`. This option cannot be combined with `--areas` or synthetic mode. `check-areas` verifies source checksums and prints the join/mapping audit. For your own independently reviewed areas, the existing `--areas` format below remains supported.

Create `data/areas_reviewed.json` only after checking the actual population figures, vintage and station mapping. It must be a JSON array of objects with these fields:

| Field | Meaning |
|---|---|
| `area_id` | Unique nonempty internal identifier |
| `name` | Planning-area name |
| `residents` | Positive integer count from the cited population source |
| `seniors65` | Integer aged-65+ count, no greater than residents |
| `population_year` | Actual observation year, not webpage update year |
| `population_source` | Source citation/URL |
| `station_id` | WBGT station identifier from the observed API |
| `mapping_method` | How the area maps to the station, including distance/limits where known |
| `mapping_verified` | Boolean, initially false; true only after reviewing the link |

No example here supplies fabricated figures for a real area. The synthetic sample in `heataction/demo.py` demonstrates the JSON structure. The app does not verify your human review; it merely enforces the explicit flag. Record review reasoning and distance in mapping_method and the data audit.

Do not add both planning-area totals and subzone totals into one population aggregate. Use total-sex age bands once. Census 2020 uses Master Plan 2019 geography. Population at home does not reveal outdoor exposure or an individual's health condition.

## Bundled observed pilot audit

Official snapshots were downloaded on 21 September 2026 into `data/reference/observed/`. `manifest.json` records dataset IDs, source and download-endpoint URLs, retrieval times, SHA-256 checksums and the actual 2020/2019 vintages. Temporary signed download URLs are not retained. Data attribution is to SingStat and URA under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence).

The parser reads only rows ending in ` - Total`, uses `Total_Total` once, and sums only the six total-sex age bands from 65–69 through 90+. National, subzone, male and female totals are never added. Unavailable age counts propagate to unavailable senior totals, not zero. Published bands are rounded and need not sum exactly to published totals. Census and geometry are joined by normalized exact planning-area names; unmatched Census areas fail validation.

| Pilot (URA code) | Residents, 2020 | Aged 65+, 2020 | Reviewed WBGT station | Distance from boundary-box centre |
|---|---:|---:|---|---:|
| Ang Mo Kio (AM) | 162,280 | 35,220 | S141, Yio Chu Kang Stadium | 1.051 km |
| Bedok (BD) | 276,990 | 53,370 | S129, Bedok North Street 2 | 1.090 km |
| Jurong West (JW) | 262,730 | 33,730 | S132, Jurong West Street 93 | 0.965 km |

`pilot_mappings.json` records the inspected NEA station IDs, names, coordinates, observation/retrieval times and technical review scope. At every startup, each station must remain inside the exact mapped polygon, respecting Polygon/MultiPolygon geometry and holes. The review is a technical source/geometry review, not a claim of human partner approval, uniform heat, or operational coverage. It is sufficient for this explicitly labelled prototype proxy only. The recorded distance is to a geometric bounding-box centre; it is not a household distance or a population-weighted centre.

Live readings whose coordinates move more than 100 metres from the reviewed station reference are gated as `Station moved; mapping review needed`. This tolerance is an engineering review trigger, not an official standard. The existing 30-minute freshness policy still applies. No nearby station is silently substituted.

All 55 polygons can be inspected for demographics. Only the three pilot areas participate in the fixed planning reference cohort. Heat colouring outside the pilot is disabled, and unavailable pilot weather is shown as Unknown. The SVG uses an approximate longitude/latitude display projection for local context; distance checks use haversine distance on the original coordinates. No smoothed heat surface is inferred.

## Raw data and corrections

Raw snapshots use a SHA-256 of canonical payload JSON. Source URL and retrieval time are retained. Repeated identical payloads reuse the snapshot. SQLite upserts use `(source, station_id, observed_at)` and prefer newer source updates, then newer retrievals for equal update times. Delta notebooks use the same rule. Bronze Delta preserves every fetched response; Silver remains deduplicated.

The local cache keeps only the latest normalized version. Raw snapshots retain earlier payloads, but rebuilding data exactly as published at every historic forecast issue time is not yet implemented. Report this limitation in any retrospective evaluation.
