# Research Methodology

## 1. Decision problem

At each dispatch interval, a manager observes a queue of unresolved building complaints and limited inspection capacity. The policy assigns each eligible complaint one of three priorities: defer, routine, or expedited. Capacity is consumed when an inspection is scheduled, not recreated independently for each complaint.

The primary unit of analysis is a complaint at a decision timestamp. The simulator operates at shift or day level so delays, queue aging, capacity, and repeat complaints are stateful.

## 2. Validation boundary

Historical records show complaints, inspection timing, and dispositions. They do not reveal every feasible action or the outcome that would have occurred under a different action. Therefore:

- supervised risk models may be evaluated predictively on held-out time periods;
- historical policy comparisons require explicit off-policy assumptions;
- simulator comparisons are counterfactual model results, not causal deployment estimates; and
- no simulator result will be described as an observed reduction in violations or disparity.

## 3. State available at decision time

Candidate state variables include:

- complaint time, detail, channel, and queue age;
- borough, community district, and non-sensitive location features;
- building identifier and counts of prior complaints known before the cutoff;
- prior dispositions known before the cutoff;
- whether a valid after-hours variance overlaps the complaint time;
- permit and job characteristics known before the cutoff;
- current queue composition, remaining shift capacity, and recent utilization; and
- calendar effects.

Post-decision fields such as closed date, inspection date, resolution, or later violations are labels/transitions and may never enter the state for that decision.

## 4. Actions

| Code | Action | Operational interpretation |
|---|---|---|
| 0 | Defer | Keep in queue; reconsider later or close under a separately modeled rule |
| 1 | Routine | Schedule within the normal service window |
| 2 | Expedited | Schedule in the earliest capacity window |

Issuing a summons or stop-work order is an outcome, not a dispatch action.

## 5. Outcomes

Raw resolution and DOB disposition codes remain intact. A documented mapping creates research labels:

- actionable;
- no action required;
- inaccessible;
- referred or duplicate; and
- unresolved/censored.

Open and right-censored complaints are not treated as negative outcomes. Sensitivity analyses will test alternative mappings.

## 6. Objectives and constraints

Outcomes are reported as a vector before any scalar reward is applied:

1. actionable findings discovered;
2. severity-weighted time to finding;
3. inspections and travel/resource cost;
4. queue delay and abandonment;
5. unresolved or inaccessible cases; and
6. disparity and calibration measures with uncertainty.

Scalar rewards are stakeholder assumptions stored in versioned configuration. Safety constraints, capacity constraints, and chosen equity bounds are reported separately so reward tuning cannot conceal violations.

## 7. Policy ladder

Policies will be added in increasing complexity:

1. random and always/never inspect controls;
2. FIFO, oldest-first, borough rotation, and rule-based risk tiers;
3. supervised risk ranking with calibrated probabilities;
4. contextual bandits for myopic allocation;
5. tabular dynamic programming/Q-learning on simplified environments;
6. DQN and PPO variants with correct categorical encodings;
7. constrained or Lagrangian policies;
8. multi-objective policy sets; and
9. adversarial/MARL stress tests in simulation only.

Complex policies must beat simple baselines on held-out metrics and robustness checks to remain in the final comparison.

## 8. Evaluation design

- Rolling temporal splits, never random row splits for the headline result.
- Building-group checks to quantify repeated-address leakage.
- Multiple random seeds and bootstrap confidence intervals.
- Fixed experiment manifests: data snapshot, feature version, policy config, seed, code SHA.
- Calibration, precision-recall, capacity-constrained recall, cost curves, delay, and subgroup slices.
- Stress tests for capacity shocks, geographic shifts, missing data, outcome drift, and strategic behavior.
- Ablations for each state feature family and reward/constraint term.

## 9. Explainability

Explainability is matched to the object being explained:

- feature attribution and calibration for the predictive risk model;
- policy maps and counterfactual state changes for RL policies;
- occupancy and action-frequency diagnostics for the simulator;
- Pareto and constraint plots for stakeholder tradeoffs; and
- example complaint timelines for non-technical users.

Feature importance is not a causal effect and will be labeled accordingly.

## 10. Reproducibility threshold

Every published metric must be regenerable from a clean environment with:

- an immutable or checksummed data snapshot;
- a data card and schema validation report;
- a committed configuration;
- deterministic seed handling where supported;
- automated tests; and
- one command that writes machine-readable metrics before plots or prose.

## 11. Restricted authorship material

The project author is a co-author on an unpublished group draft concerning equitable municipal
inspection prioritization. That source is intentionally excluded from the public repository: it
explicitly prohibits citation and distribution. It may inform high-level research questions, but
it cannot substantiate public results, data definitions, or deployment claims. See
[Restricted Research Materials](restricted-materials.md).
