# AHV Cohort Profile: 2026-07-06 Snapshot

This profile is derived from the checksummed local snapshot described in
[`data/manifests/2026-07-06.json`](../../data/manifests/2026-07-06.json).
Raw address-level files are deliberately not committed.

## Cohort

The cohort contains 782 NYC 311 requests where the agency is DOB and the problem is
`AHV Inspection Unit`. It spans 2020-10-14 through 2026-06-30.

| Research outcome | Rows | Share |
|---|---:|---:|
| Actionable | 16 | 2.0% |
| No action | 733 | 93.7% |
| Referred or duplicate | 10 | 1.3% |
| Inaccessible | 1 | 0.1% |
| Unresolved | 22 | 2.8% |

`Actionable` combines official 311 records that indicate an OATH summons or an
after-hours stop-work order, plus corresponding matched DOB enforcement dispositions.
It is a research label, not a legal finding or a general measure of building safety.

## Linkage audit

The pipeline links each 311 request to DOB complaint category `4X` by normalized address
and a +/- 1 day entry window. It never presents a weak link as a certain match.

| Link status | Rows | Share |
|---|---:|---:|
| Exact date | 712 | 91.0% |
| Within one day | 2 | 0.3% |
| Ambiguous | 55 | 7.0% |
| Unmatched | 13 | 1.7% |

The 55 ambiguous links are retained with candidate counts for later sensitivity analysis;
they will not silently enter any headline training dataset.

## Geographic and permit coverage

Manhattan accounts for 352 requests (45.0%), Brooklyn 283 (36.2%), Queens 105 (13.4%),
the Bronx 39 (5.0%), and Staten Island 3 (0.4%). These are complaint counts, not measures
of population, need, or protected-class representation.

The initial permit join finds 21 complaints whose BBL has an official after-hours permit
interval overlapping the complaint timestamp. The permit source has historical coverage that
ends before a portion of the recent 311 cohort, so missing overlap is not evidence of an
unpermitted activity.

## How to reproduce locally

```bash
uv sync --extra dev --locked
uv run civic-inspection verify --snapshot-date 2026-07-06 --source all
uv run civic-inspection build --snapshot-date 2026-07-06
```

The `verify` command requires the local raw snapshot. The public manifest records source
IDs, row counts, part-level hashes, and hashes for every derived Parquet and profile artifact.
