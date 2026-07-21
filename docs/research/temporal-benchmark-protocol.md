# Temporal RL Benchmark Protocol

## Purpose

This protocol evaluates the first learned policies without confusing simulation learning with
historical prediction or causal evidence. It implements the Sprint 3 requirements in
[`SPRINT3_SPEC.md`](../SPRINT3_SPEC.md).

## Two data tracks

The 782-record AHV slice spans 2020-10 through 2026-06 and contains 16 actionable administrative
outcomes. It is sufficient for a small, reproducible simulator-policy experiment but is not
sufficient for a portfolio headline about predictive effectiveness. The profiled 3,106,954-row DOB
universe is the provenance anchor for selecting a wider predictive cohort once its checksummed raw
export is locally available.

## Temporal boundary

`configs/experiments/ahv_temporal_rl_v1.json` declares a strict cutoff: complaints created on or
before 2024-06-30 train learned policies; complaints created on or after 2024-07-01 evaluate them.
No random row split is permitted for a headline result. Features must be available by complaint
creation time. Building repetition is reported as a diagnostic rather than hidden as independence.

## Policies and scenarios

FIFO, random, transparent risk-tier, and Safety Floor are operational baselines. The first learned
policies are a contextual bandit and tabular Q-learning policy. Both are trained only on the earlier
slice and evaluated under each declared capacity/access scenario and seed.

## Metrics and uncertainty

Each run records total actionable discoveries, missed deferred actionables, delay, actionable-case
delay, queue depth, and borough service-rate/delay slices. Bootstrap 95% intervals are calculated
across the declared seeds. Borough is an operational geography slice, not a demographic attribute,
fairness finding, or demographic proxy.

## Release gate

Every table/chart must originate from an experiment manifest and row-level artifacts. A private
Decision Brief must record whether learned policies outperform a transparent operational baseline,
where they fail, and why the result does or does not merit public-facing treatment.
