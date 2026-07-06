# Learning and Interview Guide

This document will grow after every sprint. It is the explanation layer for discussing the project without memorizing implementation details.

## Thirty-second version

I rebuilt a reinforcement-learning course project into a reproducible civic decision-science platform. The system studies how NYC could prioritize building complaints under limited inspector capacity while making safety, delay, cost, and equity tradeoffs visible. I began by auditing the original prototype, found that its reported backtest used synthetic data and in-sample evaluation, and redesigned the project around real public-data ingestion, point-in-time features, temporal validation, an operational queue simulator, simple baselines, constrained RL, and an interactive policy lab.

## Why RL might be appropriate

Inspection allocation is sequential: using capacity now changes the queue, delays, future capacity, and information available later. A supervised model can estimate risk for one complaint, but it does not by itself decide how to allocate a changing resource over time.

RL is only useful if it beats simpler scheduling and risk-ranking baselines under realistic dynamics. That comparison is a design requirement, not a foregone conclusion.

## The most important modeling correction

The original action `aggressive enforcement` mixed a dispatch decision with an inspector/legal outcome. The rebuilt action is priority: defer, routine, or expedited. Summonses and stop-work orders are stochastic outcomes. This makes the MDP correspond to a decision an actual manager could take.

## What can and cannot be claimed

Can claim:

- how policies behave in a documented simulator;
- predictive performance on held-out historical outcomes;
- robustness to declared simulated shifts; and
- tradeoffs under explicit stakeholder assumptions.

Cannot claim from this project alone:

- the causal effect of dispatching an inspector;
- that a simulator policy will improve NYC outcomes in deployment;
- that equal borough allocation is legally or substantively fair; or
- that simulated landlords represent actual landlord behavior.

## Questions to expect

**Why not just use supervised learning?**  
Risk prediction is a component. The allocation problem also has queue aging, finite capacity, delayed outcomes, and future opportunity cost. We benchmark both.

**How do you prevent leakage?**  
Every feature has an `available_at` concept. Complaint resolution, inspection date, and later violations are excluded from the decision state. Headline splits are chronological.

**How do you evaluate fairness?**  
We report need-adjusted allocation, delay, error-rate, and calibration gaps with uncertainty. We do not treat borough as a protected class or bury fairness inside one reward penalty.

**Why build a simulator?**  
Historical data does not contain outcomes for actions not taken. A simulator makes assumptions explicit and allows stress tests, but its results remain model-based counterfactuals.

**What was the hardest engineering judgment?**  
Separating attractive presentation claims from what the data actually supports, then redesigning the action, validation, and artifact lineage so every public number is reproducible.
