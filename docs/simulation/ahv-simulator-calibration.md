# AHV Simulator Calibration and Limitations

The simulator models inspection-triage choices under explicit daily capacity. It supports the
future Policy Lab; it is not a claim about what NYC would do or what would occur under another
dispatch action.

## Initial scenario

The 782-row 2026-07-06 AHV cohort is run with daily capacity of one and access probability of
one. Outcome labels remain latent until simulated inspection; no policy receives them as input.

| Policy | Inspected | Actionable findings | Mean delay | Maximum backlog |
|---|---:|---:|---:|---:|
| FIFO/routine | 782 | 16 | 7.21 days | 29 |
| Risk tier | 782 | 16 | 7.21 days | 29 |
| Never inspect | 0 | 0 | N/A | 0 |

The risk tier expedited 392 cases but did not change aggregate throughput. This is useful
negative evidence: prioritization must be evaluated on safety timing, group delay, and stress
scenarios, not just total cases served.

## Limits and testable invariants

- Labels are observed administrative outcomes, not counterfactual response models.
- Access probability, capacity, reward values, and drain horizon are explicit assumptions.
- The initial risk score uses only time of day, point-in-time prior count, and permit overlap;
  it is not a trained or calibrated risk model.
- Borough is an operational slice, not a protected-class fairness audit.
- Tests enforce capacity conservation, expedite-before-routine service, missed deferred
  actionable cases, and inspectable decision/outcome logs.
