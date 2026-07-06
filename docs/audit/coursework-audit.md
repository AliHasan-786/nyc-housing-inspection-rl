# Coursework Evidence Audit

Audit date: 2026-07-06

## Bottom line

The coursework is a useful algorithmic prototype, not a validated policy result. Its strongest portfolio value is the breadth of methods explored. Its largest weakness is that the reports and presentation sometimes describe synthetic, in-sample experiments as historical backtests.

The rebuild will preserve the intellectual path while correcting the evidence boundary.

## Materials reviewed

- literature review and five supporting papers;
- HW2 report and `rl_housing_inspection.py`;
- HW3 report, figures, explainer, and `rl_housing_hw3.py`;
- HW4 report and `hw4_bayesian_rl.py`;
- final presentation variants;
- assignment instructions, syllabus, lecture corpus, and housing literature spreadsheet; and
- the existing public GitHub repository and commit history.

Course PDFs and third-party papers remain outside this portfolio repository.

## What is worth keeping

- A clear public-sector resource-allocation problem.
- A Gymnasium-style environment and multiple policy families.
- Attention to sparse outcomes and operational capacity.
- Multi-objective thinking rather than a single accuracy metric.
- An explainability and stakeholder-communication layer.
- A proposed adversarial/MARL extension grounded in the literature review.
- Bayesian decision-making experiments that can later inform uncertainty-aware dispatch.

## Material findings that require correction

### 1. The checked-in CSV is not a 755-row historical dataset

`311_Service_Requests_from_2020_to_Present_20260304.csv` has one header and one value: `AHV Inspection Unit`. The code does not read it. `generate_synthetic_data()` creates 755 observations and assigns exactly 16 positive outcomes by construction.

The generated complaint categories, boroughs, hours, budgets, history, and labels are not empirical rows. Reports that say the model trained on 755 historical hourly records and aligned them with ground-truth dispositions are therefore inaccurate.

### 2. Evaluation replays the training sequence

All agents train repeatedly on one fixed synthetic sequence and are evaluated greedily on that same sequence. This is memorization-oriented simulation analysis, not a temporal backtest or estimate of generalization.

Required correction: temporal train/validation/test windows, repeated seeds, confidence intervals, and a strict point-in-time feature cutoff.

### 3. The action space includes an action the decision-maker does not control

`Aggressive Enforcement` is modeled as a dispatcher action. In practice, complaint triage can prioritize or schedule an inspection; the inspection result and legal remedy depend on conditions, inspector findings, and law.

Required correction: use `defer`, `routine`, and `expedited` dispatch. Model summonses, stop-work orders, referrals, and no-action dispositions as stochastic outcomes.

### 4. Budget mechanics do not match their explanation

The observation space permits inspector budgets from 0 to 5, but generated budgets are always 3, 4, or 5. Action costs are at most 2, so the budget constraint never forces dismissal in the generated data. A claim that budget is important because it forces actions is not supported by this implementation.

Required correction: make capacity a queue- or shift-level resource that is consumed over time and test utilization explicitly.

### 5. The fairness penalty is not a fair-housing audit

The code penalizes a policy whenever one borough exceeds 40% of inspections. This rule:

- is unavoidable during early steps when only one or two inspections have occurred;
- ignores the borough distribution of complaints and actual need;
- treats boroughs as demographic groups;
- does not measure false-positive or true-positive disparities; and
- can reward equal allocation even when risk or population differs.

Required correction: report need-adjusted service rates, opportunity/error-rate gaps, calibration, delay, and uncertainty. Treat constraints and legal interpretation as policy choices, not proof of fairness.

### 6. Reward values are assumptions, not estimated public costs

Values such as -500 for a miss, +400 for an aggressive catch, and -30 for displacement are hand-selected. Housing units at risk are inferred directly from the chosen action rather than observed.

Required correction: version reward assumptions, expose them in sensitivity analysis, and keep factual outcomes separate from stakeholder utilities.

### 7. Several algorithmic interpretations are too strong

- The Monte Carlo update iterates backward and marks the first state-action pair encountered from the end. For repeated pairs this is last-visit, not first-visit Monte Carlo.
- DQN receives ordinal integer codes for nominal categories and is evaluated after one tuning configuration. Its collapse does not establish that neural RL fails because of class imbalance.
- REINFORCE subtracts a value baseline trained on raw returns from normalized returns, mixing scales in the advantage estimate.
- Shapley-style masking substitutes one fixed baseline state and explains learned Q-values on synthetic states; it does not establish real-world feature importance.
- Multi-objective points are trained and tested on the same 16 constructed positives, so a 16/16 result is not evidence of deployment performance.

Required correction: tested reference implementations, ablations, repeated seeds, appropriate encodings, and uncertainty reporting.

### 8. Deliverables report inconsistent headline results

Examples include TD results of 14/16 with 455 wasted inspections in HW2 versus 16/16 with 257 wasted inspections in the final deck, and other tables with different random-baseline totals. These may reflect later runs, but the artifact lineage is not recorded.

Required correction: every chart and table must be generated from a versioned experiment manifest containing code commit, data snapshot, configuration, and seed set.

### 9. The Bayesian bandit study is a separate synthetic experiment

Historical cap-rate values seed priors, but `TRUE_THETA` is manually specified and Bernoulli outcomes are simulated. This can be retained as a teaching module but should not be presented as empirical borough investment performance or as direct evidence for complaint dispatch.

## Real-data feasibility check

On 2026-07-06, the official 311 API returned 782 records where:

- agency is `DOB`;
- problem is `AHV Inspection Unit`; and
- detail is `After Hours Work - With An AHV Permit`.

The observed status/resolution groups included 723 closed with no further action, 8 with an OATH summons, 7 with an after-hours stop-work order, 5 open, and smaller referred, duplicate, reviewed, inaccessible, or stop-work-order-removal groups. These counts change as the source updates.

This means a real pipeline is feasible. It also shows why labels must be multi-class first and only later collapsed under a documented research definition.

## Portfolio narrative

The honest narrative is stronger than the original claim:

> I began with a course prototype, audited its data and validation assumptions, found that the apparent backtest was synthetic and in-sample, and rebuilt the project as a reproducible decision-science platform with operationally valid actions, temporal evaluation, explicit uncertainty, and an interactive policy simulator.
