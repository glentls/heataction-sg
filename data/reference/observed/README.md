# Observed geographic reference snapshots

These are official public source snapshots, not generated demonstration data.

- `census2020_age.csv`: Singapore Department of Statistics, **Resident Population by Planning Area/Subzone of Residence, Age Group and Sex (Census of Population 2020)**, [dataset d_d95ae740c0f8961a0b10435836660ce0](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view). Population vintage: 2020.
- `planning_areas_2019.geojson`: Urban Redevelopment Authority, **Master Plan 2019 Planning Area Boundary (No Sea)**, [dataset d_4765db0e87b9c86336792efe8a1f7a66](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view). Boundary vintage: 2019.
- `manifest.json`: source provenance, retrieval timestamps and SHA-256 checksums for the unmodified downloads. Webpage update years do not change the data vintages.
- `pilot_mappings.json`: project-authored technical review of three area-to-station links, based on observed NEA station metadata. It contains no invented readings or populations and is not partner/field validation.

Source data is made available under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). SingStat and URA do not endorse the project's mappings, planning policy or interpretations. See `docs/DATA.md` for aggregation rules, coverage limitations and the audit table.

Run `python -m heataction check-areas` from the repository root to verify and rebuild the in-memory joins. To refresh a snapshot, use its `download_endpoint` from the manifest to request a temporary download URL, download the official file, then review any schema/vintage changes, update the checksum and retrieval record, and rerun the regression tests. Never write the temporary signed URL into this repository or replace a failed download with synthetic data. Pilot station changes require a new documented mapping review.
