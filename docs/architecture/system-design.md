# System Design

## Design goals

- One reproducible path from public data to displayed metric.
- Fast local exploration with immutable experiment artifacts.
- Clear separation between observed history and simulated counterfactuals.
- A user-facing experience that works without requiring users to understand RL.
- Swappable policies behind one typed interface.

## Components

### Data layer

A Python ingestion package queries Socrata with pagination, retries, schema validation, retrieval metadata, and content hashes. DuckDB queries local Parquet snapshots. Feature builders enforce decision-time cutoffs.

### Research layer

Gymnasium-compatible environments expose queue and capacity dynamics. Policy adapters normalize baselines, scikit-learn risk rankers, tabular agents, and deep-RL models behind `act(observation)`. An evaluation runner writes a manifest, row-level decisions, aggregate metrics, and confidence intervals.

### Service layer

FastAPI now serves bounded, versioned policy-run scenarios at `POST /v1/policy-runs` and a health
endpoint. It validates capacity, access probability, seed, policy, and data snapshot; it writes a
stable-ID artifact containing a manifest, aggregate metrics, decisions, and outcomes. The endpoint
is deliberately not a dispatch interface. Long experiments will run as jobs; the interactive demo
uses bounded simulations.

### Experience layer

The Next.js application will contain four connected views:

1. **Story:** the real problem, data, and validation boundary.
2. **City Explorer:** complaint/outcome maps and timelines.
3. **Policy Lab:** staffing and objective controls with live replay.
4. **Research Bench:** algorithms, uncertainty, ablations, and failure modes.

The initial public experience is implemented as the Policy Lab landing page. It has a deterministic
browser-local preview for staffing and policy-posture interactions, always labeled as simulated.
`web/src/lib/policy-api.ts` defines the typed future boundary to FastAPI; production results must
be loaded from versioned experiment artifacts, never hand-entered UI values.

## Proposed repository layout

```text
configs/
data/
docs/
src/nyc_housing_rl/
  data/
  features/
  environments/
  policies/
  evaluation/
  api/
tests/
web/
```

## Artifact contract

Each experiment directory will contain:

```text
manifest.json       code/data/config/seed identity
metrics.json        machine-readable summary
decisions.parquet   row- or step-level actions and outcomes
curves.parquet      time-indexed learning/evaluation metrics
model-card.md       intended use and limitations
```

Charts and UI cards read these artifacts; prose does not carry independent hand-entered numbers.

## Technology choices

- Python 3.12 and uv for a locked research environment.
- Pandas/Polars and DuckDB/Parquet for auditable local analytics.
- Pydantic/Pandera-style contracts for source and feature schemas.
- Gymnasium plus policy-specific libraries only where justified.
- FastAPI for typed experiment endpoints.
- Next.js/TypeScript with MapLibre or deck.gl and accessible charting.
- Pytest, Ruff, mypy, and GitHub Actions for quality gates.

Dependencies will be introduced in the sprint that uses them and recorded in decision logs.
