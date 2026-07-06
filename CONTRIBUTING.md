# Contributing

## Development loop

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
```

## Research changes

Changes that affect cohorts, labels, features, rewards, constraints, metrics, or public claims must include:

- the assumption being changed;
- a versioned configuration or decision record;
- tests for leakage or invariants where applicable;
- regenerated machine-readable metrics; and
- an update to the learning guide if the project explanation changes.

Do not commit raw public-data snapshots, secrets, course materials, or third-party papers.
