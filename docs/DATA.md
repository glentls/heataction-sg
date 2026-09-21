# Data register and contracts

Reviewed on 21 September 2026. The app keeps raw source observations separate from demographic assumptions and synthetic demonstration data.

| Source | Reference | Implementation |
|---|---|---|
| WBGT | [NEA catalogue](https://data.gov.sg/datasets/d_87884af1f85d702d4f74c6af13b4853d/view) | Collector and station parser implemented. Working response inspected through public web retrieval. |
| Rainfall | [NEA catalogue](https://data.gov.sg/datasets/d_6580738cdd7db79374ed3152159fbd69/view) | Collector and parser implemented. Working response inspected through public web retrieval. |
| Age profiles | [Census 2020](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view) | Dataset identified. Automated download/transformation and real app integration still pending. |
| Boundaries | [URA Master Plan 2019](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) | Compatible edition identified. Map rendering and spatial join still pending. |

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

## Raw data and corrections

Raw snapshots use a SHA-256 of canonical payload JSON. Source URL and retrieval time are retained. Repeated identical payloads reuse the snapshot. SQLite upserts use `(source, station_id, observed_at)` and prefer newer source updates, then newer retrievals for equal update times. Delta notebooks use the same rule. Bronze Delta preserves every fetched response; Silver remains deduplicated.

The local cache keeps only the latest normalized version. Raw snapshots retain earlier payloads, but rebuilding data exactly as published at every historic forecast issue time is not yet implemented. Report this limitation in any retrospective evaluation.
