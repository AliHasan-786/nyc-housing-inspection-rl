# Simulator Guardrails and Human Oversight

## What the simulator may show

- Counterfactual behavior under explicit capacity, access, and reward assumptions.
- How a documented policy changes queueing and simulated discovery timing.
- Coverage and delay slices for declared operational groups.

## What it may not claim

- That an action causes a real inspection outcome.
- That a borough-level metric proves demographic fairness.
- That the model should autonomously issue summonses, stop-work orders, or close complaints.
- That historical absence of a complaint or finding means absence of harm.

## Required human controls

| Control | Rationale |
|---|---|
| Human confirmation for expedite/defer recommendations | Complaint metadata is incomplete and may encode reporting inequity. |
| Escalation floor for safety signals | A policy may not defer a case that meets separately defined safety criteria. |
| Decision log and reason display | Reviewers need to inspect policy behavior case by case. |
| Group delay/coverage monitoring | Aggregate reward can hide uneven service. |
| Scenario and reward versioning | Product owners must know which assumptions produced a result. |
| Appeal and correction pathway | Residents and staff need a way to challenge bad routing data. |

## Release gate for the web experience

Every scenario displayed publicly must show its data snapshot, simulator assumptions, policy
name, whether the result is observed or simulated, and a plain-language limitation statement.
