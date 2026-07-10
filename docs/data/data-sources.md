# Data Sources and Join Plan

All sources below are official NYC public datasets. Source schemas are validated at ingestion because Socrata datasets update over time.

## Core sources

### 311 Service Requests from 2020 to Present

- Dataset ID: `erm2-nwe9`
- Page: https://data.cityofnewyork.us/d/erm2-nwe9
- Role: complaint timestamp, problem/detail, resolution, geography, BBL, channel, and status.
- Initial cohort: `agency = 'DOB'` and `complaint_type = 'AHV Inspection Unit'`.
- Caution: resolution text is an outcome field and must not enter point-in-time features.

### DOB Complaints Received

- Dataset ID: `eabe-havv`
- Page: https://data.cityofnewyork.us/d/eabe-havv
- Role: complaint number, BIN, complaint category, inspection/disposition dates, disposition code, and status.
- Candidate join: address/geography plus time-window reconciliation; retain match confidence and do not assume every 311 request has a one-to-one DOB row.

### Building Complaint Disposition Codes

- Dataset ID: `6v9u-ndjg`
- Page: https://data.cityofnewyork.us/d/6v9u-ndjg
- Role: human-readable lookup for raw DOB disposition codes.

### DOB After Hour Variance Permits

- Dataset ID: `g76y-dcqj`
- Page: https://data.cityofnewyork.us/d/g76y-dcqj
- Role: permitted work interval, BIN/BBL, permit status, variance reason, nearby residence, enclosure, demolition, and crane indicators.
- Candidate join: BIN or BBL plus interval overlap at complaint creation time.
- Source grain: one permit number may contain multiple authorized time intervals; the
  validated key is permit number plus interval start and end.

## Candidate enrichment sources

Future sprints will evaluate official PLUTO/building characteristics, DOB permit/job filings, DOB violations, HPD building/violation history, and public geographic crosswalks. A source enters the model only if its timestamp supports point-in-time reconstruction.

## Data layers

```text
raw      Exact API responses plus request metadata and retrieval time
bronze   Typed source tables with source fields preserved
silver   Deduplicated complaints, permit intervals, dispositions, and match audit
gold     Point-in-time decision rows and simulator calibration tables
```

Raw data is not committed to Git. Small, license-compatible fixtures are hand-crafted or deterministically sampled and de-identified for tests.

## Reproducible commands

```bash
uv run civic-inspection fetch --snapshot-date YYYY-MM-DD --source all
uv run civic-inspection verify --snapshot-date YYYY-MM-DD --source all
uv run civic-inspection build --snapshot-date YYYY-MM-DD
```

`fetch` writes JSONL source parts and a manifest under `data/raw/`. `verify` confirms
the exact part hashes and row counts. `build` validates source contracts, writes bronze and
silver Parquet layers locally, produces a cohort data card, and records content hashes in a
tracked manifest. The 2026-07-06 profile is documented in
[AHV Cohort Profile](ahv-cohort-2026-07-06.md).

## Join quality requirements

Every linked record must include:

- join keys used;
- time-window rule;
- match type and confidence;
- number of candidate matches;
- reason for ambiguity or rejection; and
- a leakage check proving joined features existed by the decision cutoff.

Headline experiments will report cohort attrition and unmatched rates.
