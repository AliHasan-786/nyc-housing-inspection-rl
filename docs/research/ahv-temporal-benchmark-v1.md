# AHV Temporal Policy Benchmark v1 (Provisional; superseded)

> This historical v1 write-up is retained for auditability, but its aggregate result is
> superseded by the corrected [v1.1 benchmark](ahv-temporal-benchmark-v1_1.md). V1 used
> incomplete unfound-actionable accounting and a terminal-reward defect; do not cite its table.

## Result: the learned policies did not beat transparent baselines

This is a small, counterfactual simulator-policy study—not a causal estimate of NYC inspection
performance, a predictive-performance headline, or a demographic fairness finding. The exact
protocol is frozen in [`ahv_temporal_rl_v1.json`](../../configs/experiments/ahv_temporal_rl_v1.json).

The first learned policies, a contextual bandit and tabular Q-learning policy, were trained only
on complaints created on or before June 30, 2024 and evaluated on later complaints. They did not
outperform FIFO, the transparent risk-tier baseline, or Safety Floor in any declared scenario.
Both learned policies frequently deferred cases, a useful failure mode that the artifact logs make
inspectable.

## Scope and reproducibility

| Item | Value |
| --- | --- |
| Data snapshot | 2026-07-06 AHV silver cohort |
| Temporal split | 700 train / 82 evaluation complaints |
| Evaluation actionables | 3 administrative outcomes |
| Scenarios | 5 seeds × 2 capacities × 2 access assumptions |
| Policies | FIFO, random, risk tier, Safety Floor, contextual bandit, tabular Q-learning |
| Run count | 120 |
| Decision/outcome rows | 9,840 / 6,045 |
| Repeated buildings across split | 13 evaluation buildings also seen before cutoff |

The local artifact directory is ignored to avoid publishing row-level source-derived logs. Its
`manifest.json` records hashes for the configuration, silver input, implementation files, each
output file, and serialized learned-policy values. Regenerate it with:

```bash
uv run civic-inspection run-temporal-benchmark \
  --config configs/experiments/ahv_temporal_rl_v1.json
```

## Artifact-derived comparison

Means and 95% seed-bootstrap intervals below are counts from the 3 evaluation actionables. They
describe the declared simulator assumptions only.

| Capacity | Access | Policy | Found, mean [95% CI] | Missed, mean [95% CI] |
| ---: | ---: | --- | --- | --- |
| 1 | 0.8 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 0.8 | Risk tier | 2.80 [2.40, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 0.8 | Safety Floor | 2.80 [2.40, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 0.8 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 1 | 0.8 | Tabular Q-learning | 0.00 [0.00, 0.00] | 3.00 [3.00, 3.00] |
| 1 | 1.0 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 1 | 1.0 | Tabular Q-learning | 0.40 [0.00, 0.80] | 2.60 [2.20, 3.00] |
| 2 | 0.8 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 2 | 0.8 | Tabular Q-learning | 0.00 [0.00, 0.00] | 3.00 [3.00, 3.00] |
| 2 | 1.0 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 2 | 1.0 | Tabular Q-learning | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |

## Operational geography, not demographic fairness

The artifact also reports service rate and mean delay by borough. These are operational geography
slices only; borough is not used as a protected-class proxy and does not prove or disprove
demographic fairness. In the full-access, capacity-1 condition, FIFO/risk-tier/Safety Floor had
complete service of the evaluation queue, while the learned policies served only a small fraction
of each borough’s cases because they deferred most cases. This is a guardrail failure, not an
equity result.

## Why this is still useful

The failure identifies a concrete product and policy risk: optimizing a sparse outcome reward with
a defer action can produce superficially low queues by not serving the queue. A defensible next
study must set and separately measure a non-deferral/service constraint, use a wider audited cohort,
and compare learning with calibrated risk ranking and transparent constrained baselines.
