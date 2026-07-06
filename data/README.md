# Data Directory

Raw NYC Open Data snapshots are downloaded locally and are not committed.

Planned layout:

```text
data/raw/       immutable source responses and request manifests
data/bronze/    typed source-level Parquet tables
data/silver/    deduplicated and joined entities with match audit
data/gold/      point-in-time decision and calibration tables
data/fixtures/  small synthetic test fixtures safe to commit
```

Sprint 1 will add the data CLI, schemas, and snapshot manifest format.
