# Changelog

All notable project changes are documented here by sprint.

## Verification correction - 2026-07-16

- Withdrew hand-authored local Policy Lab metric values when no versioned API scenario is available.
- Recorded independent verification findings and benchmark requirements for the next research sprint.

## Sprint 3 - 2026-07-14

- Added a tested FastAPI Policy Lab service and CLI for bounded, reproducible scenario runs.
- Added stable, inspectable artifacts with scenario manifests, aggregate metrics, and row-level
  decision/outcome Parquet files.
- Added a safety-floor baseline that makes a no-silent-deferral safeguard testable alongside
  efficiency-oriented baselines.
- Enforced request bounds and returned explicit counterfactual, fairness, and human-oversight
  limitations with every API response.

## Policy Lab Alpha - 2026-07-11

- Added a production-buildable Next.js public case-study experience.
- Added interactive staffing, safety-priority, and policy-posture controls with clearly labeled
  deterministic simulated preview metrics.
- Added Product Management and Trust & Safety framing: user workflows, review requirement,
  limitations, policy logs, and guardrails.
- Added a typed future FastAPI policy-run contract so browser-local preview can be replaced by
  versioned simulation artifacts without changing the experience layer.

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
