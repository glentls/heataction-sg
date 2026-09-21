# Decisions

## 001: Local development plus Databricks delivery

The first app uses Python's standard library so a teammate can run it without installing framework dependencies. SQLite is only a local development cache. The submission pipeline will use managed Delta tables and Unity Catalog on Databricks. Source normalization and evaluation functions are shared with supplied notebooks.

## 002: Explicit synthetic mode

The demo uses fictional area names, populations, mapping and weather observations. It runs at a fixed historical clock and uses a separate cache from actual API observations. Metrics from synthetic data cannot support the competition's impact claims.

## 003: Correct WBGT endpoint

The observed endpoint is `/v2/real-time/api/weather?api=wbgt`, whose response nests station readings inside `data.records[].item`. The previously explored `/v2/real-time/api/wbgt` did not resolve. The working response shape was inspected on 21 September 2026. Historical date retrieval still needs a successful local/workspace check.

## 004: Persistence is the app's initial forecast

The planner explicitly labels its one-hour forecast as persistence. An optional gradient-boosting experiment evaluates chronological splits but does not automatically replace app inference. Selection happens on validation MAE; the test block is reserved for reporting. Weather history must span at least seven days to run the exploratory experiment, which is a software gate, not a sufficient validation claim.

## 005: Stable planning policy

Priority uses fixed-cohort percentiles of senior count and senior share, with adjustable relative weight. Heat weights 0, 1 and 2 are policy assumptions. Categories follow the reviewed WBGT advisory. At most one extra team slot is assigned per eligible area. A greedy ranking is optimal for this simple equal-cost, one-slot-per-area objective. More complex optimisation requires validated capacity constraints.

## 006: Conservative freshness and geographic gates

The development planner requires a reading no more than 30 minutes old, ignores observations after the scenario clock, and requires an explicitly reviewed area-to-station mapping. Thirty minutes is a configurable engineering policy, not an official safety standard. Stale and missing values become Unknown. An area-station link remains a proxy even after review.

## 007: No unsupported precision

No block-level heat model, medical risk classification, indoor temperature prediction or cooling-centre capacity claim is implemented. Rainfall collection is implemented but rainfall feature engineering is a subsequent milestone.

## 008: Matched historical population and geographic vintages

The real-area pilot uses the official Census 2020 age-by-area table with URA Master Plan 2019 boundaries, because that Census table explicitly uses those boundaries. The two unmodified snapshots ship under `data/reference/observed/` with source IDs, checksums and attribution. The app exposes 2020 age profiles for geographic context and restricts planning to Ang Mo Kio, Bedok and Jurong West. Older demographics are explicitly historical, not estimates for 2026. Downloads and reviewed transformations are separate from runtime weather and synthetic demo data.

## 009: Technical review of bounded station proxies

The three pilot links are explicit curated mappings to observed WBGT station identities whose source coordinates lie inside their matched polygons. `mapping_verified` means the documented prototype technical source/containment review passed; it does not imply coordinator approval, field validation or uniform heat coverage. Each startup rechecks containment, checksums and exact Census joins. A later station-coordinate displacement over 100 metres blocks planning pending review. Missing/stale weather still blocks assignment. Distance labels use the boundary bounding-box centre and do not suggest household-level precision. Population priority uses the fixed three-area cohort; the other 52 boundaries are context only.

## 010: Local SVG geography without third-party tiles

The browser renders the official polygons as an interactive SVG with selectable demographic and station-proxy heat layers, station reference dots, keyboard controls, area zoom and detailed provenance. No CDN, map key, tile downloads or new runtime dependency is needed. Geography is served only with explicit observed `--pilot` mode; synthetic mode cannot load it. This is the local development interface; the shared geography parser and reference snapshots can be reused in the Databricks pipeline, whose execution and deployment remain pending.

## 011: Locks require a saved reason; scenario comparison stays session-local

A coordinator cannot lock an area without first saving a nonempty reason (`/api/locks`, SQLite-backed, per area). This mirrors the app's other fail-closed gates: a lock is a deliberate override of the ranked recommendation, so `/api/plan` and `/api/export` refuse to apply a `locked` area with no reason on file rather than accepting an unexplained override. Reasons persist across reloads and restarts for convenience and audit; the active lock selection itself does not, matching the existing behaviour of budget, contacts, weight and service-area filters, none of which are remembered server-side between page loads. Scenario comparison (for example two versus three team slots) reuses the existing `/api/plan` endpoint twice, client-side, with independent budget/contacts/weight but the same service-area selection and locks; no new comparison endpoint or saved-scenario storage was added, since the local server has no concept of a user session to save a scenario against.
