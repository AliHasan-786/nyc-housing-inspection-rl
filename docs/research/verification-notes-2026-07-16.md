# Independent Verification Notes — 2026-07-16

An external review directly queried the 782-row silver cohort, ran the six baseline policies at
capacities one and two, and ran the Python test suite. This note records the follow-up code review.

## Confirmed

- The cohort has 16 actionable administrative outcomes. It is a highly imbalanced research target;
  raw accuracy is not a useful triage benchmark.
- At the initial capacity settings, policies can have identical total inspection throughput and
  identical eventual actionable discoveries after the queue drains. The calibration note already
  reports this negative result. Future comparisons must foreground actionable-discovery timing,
  delay distributions, service coverage, and stress scenarios—not a single aggregate reward.
- The former browser-local Policy Lab values were hand-authored calculations, not simulator output.
  They have been removed from the metric display. When the API is unavailable, metrics are now
  withheld rather than approximated.

## Clarified, not diagnosed as a defect

`permit_overlap` is calculated intentionally as same-BBL and complaint timestamp contained within
an after-hours-variance permit interval. Its low prevalence is therefore not evidence of a broken
join. It remains a narrow operational feature whose value and sensitivity need explicit analysis
before it supports any triage claim.

## Next benchmark requirements

1. Use temporal splits and leakage checks for every predictive baseline.
2. Report prevalence, precision-recall, calibration, and uncertainty—not accuracy alone.
3. Evaluate capacity stress tests and report time-sensitive discovery/delay metrics.
4. Export all public charts from versioned artifacts; no decorative curve may imply an observed or
   simulated result it does not represent.
