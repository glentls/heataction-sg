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
