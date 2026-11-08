# AHV Temporal Policy Benchmark v1.1

## Corrected result: ranking unchanged; learned policies still fail the service test

This is the corrected, artifact-backed replacement for the provisional v1 aggregate result. The
frozen v1 configuration and artifacts are retained; the dated [correction protocol](temporal-benchmark-v1_1-correction.md)
defines the accounting and provenance fixes. This remains a small counterfactual simulator-policy
study, not a causal estimate, predictive-performance headline, demographic fairness result, or
deployment recommendation.

The exact v1 scenario grid was rerun without changing the data, reward, policies, hyperparameters,
seeds, or capacity/access assumptions. Policy ranking on actionable discovery did **not** change:
FIFO, risk-tier, and Safety Floor outperform the contextual-bandit and tabular-Q policies in every
declared scenario. The learned policies primarily defer cases; their low queue pressure is not a
service success.

## Corrected aggregate table

Each cell is the mean across five declared simulation seeds with a 95% seed-bootstrap interval.
“Unfound” now has an exhaustive denominator: actionables that were deferred, inaccessible after a
simulated inspection, or left queued/unserved. It is not merely explicit deferral.

| Capacity | Access | Policy | Found, mean [95% CI] | Unfound, mean [95% CI] |
| ---: | ---: | --- | --- | --- |
| 1 | 0.8 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 1 | 0.8 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 0.8 | Random | 1.60 [1.00, 2.40] | 1.40 [0.60, 2.00] |
| 1 | 0.8 | Risk tier | 2.80 [2.40, 3.00] | 0.20 [0.00, 0.60] |
| 1 | 0.8 | Safety Floor | 2.80 [2.40, 3.00] | 0.20 [0.00, 0.60] |
| 1 | 0.8 | Tabular Q-learning | 0.00 [0.00, 0.00] | 3.00 [3.00, 3.00] |
| 1 | 1.0 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 1 | 1.0 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Random | 1.60 [1.00, 2.40] | 1.40 [0.60, 2.00] |
| 1 | 1.0 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 1 | 1.0 | Tabular Q-learning | 0.40 [0.00, 0.80] | 2.60 [2.20, 3.00] |
| 2 | 0.8 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 2 | 0.8 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Random | 1.60 [1.00, 2.40] | 1.40 [0.60, 2.00] |
| 2 | 0.8 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 0.8 | Tabular Q-learning | 0.00 [0.00, 0.00] | 3.00 [3.00, 3.00] |
| 2 | 1.0 | Contextual bandit | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |
| 2 | 1.0 | FIFO | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Random | 1.60 [1.00, 2.40] | 1.40 [0.60, 2.00] |
| 2 | 1.0 | Risk tier | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Safety Floor | 3.00 [3.00, 3.00] | 0.00 [0.00, 0.00] |
| 2 | 1.0 | Tabular Q-learning | 0.20 [0.00, 0.60] | 2.80 [2.40, 3.00] |

## What changed from v1

At capacity 1 and access 0.8, risk-tier and Safety Floor still find 2.80 actionables on average.
Their corrected 0.20 unfound value is entirely the **inaccessible** category, which v1 failed to
include in its narrowly defined “missed” count. Discovery ranking is unchanged. Terminal reward
accounting and the source-tree fingerprint are corrected, but this does not turn an observed
simulator outcome into operational evidence.

The corrected local artifact set is `artifacts/benchmarks/ahv_temporal_rl_v1_1_correction/`.
Its manifest has config SHA256 `1064c756c46c041db74cf8f36f5bbc9fa704c9119819c54d3444ab453bf8f898`,
silver-input SHA256 `27cc11341b39009cb1906c1be5c6f0032b8586a8b15a3483975bf39362b93618`,
and source-tree SHA256 `dcc77d46c8f6c02a51cf51ad2d23e0c264e0759d4d9765589e573ccf8677f8ec`.
The run was made from clean revision `050f063d951207cc580c0ec535ba55f5978ec812`; all seven
generated output hashes were independently rechecked.

## Important comparability boundary

When a policy serves no complaints, mean delay is `null` / **not comparable**, rather than an
attractive-looking zero. Borough figures remain operational geography service/delay slices only;
they are neither demographic fairness measures nor demographic proxies.
