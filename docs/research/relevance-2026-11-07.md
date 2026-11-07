# November 2026 Relevance and Contribution Brief

## Useful decision

The project asks whether a learning policy can improve **constrained inspection allocation** beyond
strong transparent policies while preserving service obligations. The relevant user is an operations
and policy reviewer deciding whether a triage proposal merits further evaluation—not a system that
automatically enforces building rules.

## Current public context, reviewed November 7, 2026

NYC’s official DOB complaint dataset is updated daily and contains complaint, inspection, and
disposition fields; the public page identifies it as the universe of complaints received by DOB,
including 311 and staff-entered complaints. [NYC Open Data: DOB Complaints Received](https://data.nyc.gov/Housing-Development/DOB-Complaints-Received/eabe-havv)

DOB describes complaint-driven inspections as part of enforcing building and zoning rules. A NYC
Comptroller audit reports that DOB triages complaints to appropriate units and notes access and
reinspection limitations, which makes queue/service design—not merely a classifier score—a live
operational concern. [NYC Comptroller audit](https://comptroller.nyc.gov/reports/audit-of-the-new-york-city-department-of-buildings-enforcement-of-building-codes/)

The scope also belongs in a public-accountability context: NYC’s ADS Task Force checklist treats
resource allocation and law-enforcement-adjacent decisions as potentially consequential automated
decision uses. This project therefore retains human review, logs, scenario/version identifiers, and
separate service metrics. [NYC ADS Task Force checklist](https://www.nyc.gov/assets/adstaskforce/downloads/pdf/ADS-TF-Checklist-for-Determining-ADS-Agency.pdf)

## What this extension does and does not contribute

The original course work had synthetic/in-sample evidence. This extension adds a reproducible
public-data pipeline, explicit queue MDP, capacity/access stress conditions, temporal separation,
artifact hashes, learned-policy manifests, operational geography slices, and a negative result
against transparent baselines.

It does **not** rebrand a contextual bandit as state-of-the-art RL. The current tabular bandit and
Q-learning policies are deliberately small falsification baselines. They are useful because they
expose that a sparse-outcome reward plus a defer action can fail a service obligation. They are not
a claim of methodological novelty or real-world effectiveness.

## Stronger next baselines and experiment

Before a more capable RL algorithm is justified, the wider verified DOB cohort should support:

1. calibrated logistic and tree-based risk ranking with temporal validation;
2. a transparent non-deferral/service-floor policy and constrained optimization baseline;
3. a capacity-aware greedy ranking baseline with the same action semantics; and
4. a holdout protocol reporting calibration, precision-recall, service, actionable timing, and
   distributional results across capacity/access shifts.

The substantive next experiment is a pre-registered wider-cohort, temporally held-out comparison
of those baselines against a constrained learned policy. It should fail if learning does not improve
actionable discovery/timing **while meeting** the declared service floor, or if its intervals do not
separate from transparent baselines. It should also fail if label/source mapping, building leakage,
or operational constraints cannot be documented.

## Feasible gates

No paid compute or hosted model calls are required for the next step. Required gates are a
checksummed local DOB-universe export, reviewed outcome mapping, fixed protocol before training,
and laptop-scale calibrated baselines. Geographic slices remain operational only; demographic
fairness requires appropriate authorized demographic data and a separately reviewed design.
