# Civic Inspection Lab

An interactive reinforcement-learning research project for allocating New York City building inspections under limited capacity, uncertain outcomes, and explicit equity constraints.

> **Status:** Sprint 0 - foundation and research audit. The original coursework is preserved separately. No model in this repository is ready for operational use.

## What this project is becoming

Civic Inspection Lab will let a user:

- explore real NYC 311 and Department of Buildings complaint outcomes on a map;
- replay historical complaint queues under competing dispatch policies;
- change staffing, safety, cost, delay, and equity assumptions;
- watch policies allocate inspections in a discrete-event simulator;
- compare random, FIFO, risk-ranking, bandit, tabular, deep-RL, and constrained policies;
- inspect uncertainty, failure cases, feature attribution, and subgroup outcomes; and
- stress-test policies against shifting complaint patterns and simulated strategic adaptation.

The intended audience is technical recruiters, operations-research practitioners, public-interest technologists, and curious non-specialists. The interface will explain the work without hiding the research limitations.

## Research question

Can a capacity-constrained inspection policy improve timely discovery of actionable building violations without increasing geographic or demographic disparity, when evaluated on temporally held-out data and in a simulator calibrated only with information available at decision time?

This is a research and educational system. Historical complaint outcomes are observational; they do not identify the causal effect of dispatch decisions without additional assumptions.

## Why the coursework is being rebuilt

The submitted project established useful prototypes for MDPs, Monte Carlo control, Q-learning, DQN, REINFORCE, Shapley-style attribution, multi-objective optimization, and Bayesian bandits. The audit found that its principal 755-row training dataset was generated synthetically and evaluated in-sample. Several presentation claims consequently exceed the evidence.

The rebuild keeps the useful ideas but changes the standard of evidence:

1. real, versioned public-data ingestion;
2. point-in-time-correct features and temporal validation;
3. operationally valid actions and constraints;
4. uncertainty and repeated-seed reporting;
5. fairness measurement separated from reward tuning;
6. reproducible experiments, tests, and data/model cards; and
7. an interactive simulator that clearly separates historical facts from modeled counterfactuals.

Read the full [coursework audit](docs/audit/coursework-audit.md) and [research methodology](docs/research/methodology.md).

## Planned system

```text
NYC Open Data APIs
      |
      v
versioned snapshots -> point-in-time features -> historical evaluation
                               |                         |
                               v                         v
                       calibrated simulator <---- policy benchmark suite
                               |                         |
                               +------------+------------+
                                            v
                               FastAPI experiment service
                                            |
                                            v
                              interactive Next.js policy lab
```

The detailed component boundaries are in [system architecture](docs/architecture/system-design.md).

## Repository map

```text
src/nyc_housing_rl/  Core Python package
tests/               Unit and later integration tests
configs/             Versioned experiment and policy assumptions
data/                Data contracts and local-only snapshot locations
docs/                Audit, methodology, architecture, and learning guide
web/                 Interactive application (planned)
```

## Development

Prerequisites: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
```

To fetch a new local source snapshot and build its verified analytical layers:

```bash
uv run civic-inspection fetch --snapshot-date YYYY-MM-DD --source all
uv run civic-inspection verify --snapshot-date YYYY-MM-DD --source all
uv run civic-inspection build --snapshot-date YYYY-MM-DD
```

The package includes the Sprint 1 reproducible NYC data pipeline. Raw data remains local;
the committed [data manifest](data/manifests/2026-07-06.json) preserves its lineage.

## Documentation

- [Roadmap and sprint acceptance criteria](docs/project/roadmap.md)
- [Coursework evidence audit](docs/audit/coursework-audit.md)
- [Research methodology](docs/research/methodology.md)
- [Data sources and proposed joins](docs/data/data-sources.md)
- [First real AHV cohort profile](docs/data/ahv-cohort-2026-07-06.md)
- [System architecture](docs/architecture/system-design.md)
- [Project learning and interview guide](docs/learning-guide.md)
- [Decision records](docs/architecture/decisions/)

## Ethics and use

Inspection prioritization can redirect state attention toward particular residents and neighborhoods. This project will not describe borough balance as proof of fair housing outcomes, will not use protected attributes to target enforcement, and will not recommend deployment from simulator-only evidence. See [SECURITY.md](SECURITY.md) for responsible disclosure and the methodology document for the validation boundary.

## License

Original code and documentation are released under the [MIT License](LICENSE). NYC Open Data remains subject to its source terms. Cornell course materials and third-party papers are not included in this repository.
