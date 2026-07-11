# Changelog

All notable project changes are documented here by sprint.

## Sprint 2 - 2026-07-11

- Added a Gymnasium-compatible capacity-constrained inspection-triage simulator.
- Added defer, routine, and expedited actions, persistent backlog, decision/outcome logs, and
  group-sliced service metrics.
- Added FIFO, always-expedite, never-inspect, random, and transparent risk-tier baselines.
- Added a leakage-safe bridge from the silver AHV cohort into simulator scenarios and documented
  product/T&S constraints for the future Policy Lab.

## Sprint 1 - 2026-07-06

- Replaced the synthetic training-data premise with a reproducible Socrata ingestion pipeline.
- Captured and checksummed a 782-row official AHV 311 cohort, 774 linked DOB 4X complaints,
  160 disposition codes, and 14,245 complaint-BBL-linked permit intervals.
- Added source validation, immutable raw manifests, bronze/silver Parquet builders, address/date
  linkage audit, research-label mapping, a cohort data card, and a public lineage manifest.
- Preserved uncertain matches and censored outcomes instead of converting them into negatives.

## Sprint 0 - 2026-07-06

- Established a clean portfolio repository and MIT license.
- Audited the coursework evidence, code, reports, and presentation claims.
- Defined an operational dispatch action space and outcome vocabulary.
- Documented the validation boundary, real-data sources, join plan, system design, and eight-sprint roadmap.
- Added a typed Python package skeleton, unit tests, and lint/type configuration.
- Prepared the GitHub Actions definition under `docs/ci/`; activation is pending a
  GitHub token with `workflow` scope.
