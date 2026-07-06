# ADR 0001: Separate Prediction, Historical Evaluation, and Simulation Claims

- Status: accepted
- Date: 2026-07-06

## Context

Complaint data is observational and lacks counterfactual outcomes for unchosen dispatch actions. The course prototype evaluated policies on the same constructed records used for training.

## Decision

Every result is classified as one of:

1. descriptive historical fact;
2. held-out predictive result;
3. historical policy estimate under named off-policy assumptions; or
4. simulator counterfactual.

The UI, report, and artifact manifest must display this class. Simulator results cannot be worded as observed policy effects.

## Consequences

The project makes narrower causal claims, gains auditability, and requires separate evaluation paths for prediction and control.
