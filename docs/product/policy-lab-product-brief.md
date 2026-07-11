# Policy Lab Product Brief

## User problem

A policy manager needs to understand how limited daily inspection capacity changes service
quality, safety findings, queue delay, and coverage across operational groups. A static model
score is insufficient: a decision today changes tomorrow's backlog.

## Primary users

| User | Need | Product decision supported |
|---|---|---|
| Operations manager | Balance service capacity and urgent cases | Staffing level and triage policy |
| Policy/T&S reviewer | Detect harmful or uneven policy behavior | Guardrail, escalation, and review rules |
| Public-interest stakeholder | Understand tradeoffs without reading code | Whether policy assumptions are acceptable |
| Recruiter | Assess product and technical judgment | How research became a usable system |

## First interactive workflow

1. Select a scenario and daily capacity.
2. Compare a simple baseline with a risk-tier or later RL policy.
3. Inspect safety, queue, and group-coverage metrics together.
4. Open the decision log to see why a complaint was deferred, routed, or expedited.
5. Read limitations and choose whether human review is required.

## Non-goals

- Autonomous enforcement, legal decisions, or live NYC deployment.
- Claiming causal policy effects from the historical cohort.
- Treating borough as a protected class or proving fairness from aggregate parity.
