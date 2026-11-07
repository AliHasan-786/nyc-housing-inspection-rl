# Temporal Benchmark v1.1 Correction Protocol

**Date:** 2026-11-07  
**Status:** pre-registered implementation correction; no data, reward, policy, seed, or scenario tuning is permitted.

## Why v1.1 exists

The frozen v1 configuration and its local artifacts are retained unchanged. A coordinator audit found
four accounting/provenance issues that make v1's aggregate tables provisional:

1. The final simulator transition added its pre-drain reward twice.
2. `actionable_missed` counted only explicit deferrals, omitting latent actionables that were
   inaccessible after dispatch or left unserved in a bounded drain.
3. Zero-inspection policies represented delay as `0.0`, which can look better than no service.
4. The implementation digest omitted execution dependencies, and `evaluation_start` was declared
   without validation.

## Fixed elements

- The exact v1 temporal boundary, data snapshot, policy list, training hyperparameters, seeds, and
  scenario grid are copied into `ahv_temporal_rl_v1_1.json`.
- A terminal transition contributes to total reward exactly once.
- Every latent actionable is partitioned into **found**, **deferred**, **inaccessible**, or
  **queued/unserved**. `actionable_unfound` is the sum of the latter three; the retained
  `actionable_missed` field now means this complete unfound count.
- Delay metrics with no served denominator are recorded as `null` / not comparable, never zero.
- The manifest records a deterministic fingerprint of every Python source file under
  `src/nyc_housing_rl`, including relative path, byte count, per-file SHA256, aggregate SHA256,
  and clean/dirty Git provenance.
- `evaluation_start` is parsed and validated; dates between the training and evaluation windows
  cause the run to fail rather than being silently assigned.

## Decision rule

Rerun the same local grid once. Report whether the policy ranking on actionable discovery changes.
Do not claim improvement from the correction. Retain the negative result if learned policies still
do not beat transparent baselines while satisfying service constraints.

## Boundaries

This correction does not widen the cohort, make predictive or causal claims, construct demographic
proxies, deploy a model, use hosted compute, or alter the simulator's reward/policy parameters.
