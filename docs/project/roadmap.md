# Portfolio Roadmap

Each sprint ends with passing checks, an updated changelog and learning guide, a tagged Git commit, and a push to the portfolio repository.

## Sprint 0 - Truth, scope, and foundation

Deliverables:

- clean repository separated from coursework and third-party materials;
- evidence audit and corrected project narrative;
- research methodology and validation boundary;
- source/join plan and system architecture;
- typed domain vocabulary, unit tests, and a prepared CI definition; and
- recruiter-facing learning guide.

Acceptance: local tests, lint, and type checks pass; public repository contains no course PDFs or raw data.

## Sprint 1 - Reproducible NYC data foundation

- paginated Socrata client with caching, retries, and retrieval manifests;
- snapshot the AHV 311 cohort, DOB complaints/dispositions, and AHV permits;
- typed raw/bronze schemas and data-quality tests;
- point-in-time join with match audit and cohort flow;
- exploratory report and data card; and
- CLI commands for fetch, validate, build, and summarize.

Acceptance: a clean run recreates the same checksummed analytical table from a pinned snapshot.

## Sprint 2 - Operational simulator and baseline policies

- queue/shift discrete-event model with persistent capacity;
- stochastic inspection delay, access, and disposition models;
- defer/routine/expedited action semantics;
- FIFO, random, oldest-first, always/never, and rule-based baselines;
- Gymnasium compliance tests and deterministic toy fixtures; and
- simulator calibration and limitation report.

Acceptance: conservation/capacity invariants pass and toy scenarios have analytically known outcomes.

## Sprint 3 - Predictive triage and rigorous historical evaluation

- leakage-safe feature pipeline;
- calibrated logistic/tree risk models;
- rolling temporal evaluation and building leakage diagnostics;
- capacity-constrained precision-recall and delay curves;
- uncertainty intervals, subgroup slices, and ablations; and
- experiment registry and model card.

Acceptance: all headline predictive results are out-of-time and reproducible across a declared seed set.

## Sprint 4 - RL policy benchmark

- contextual bandit, tabular Q-learning, DQN, and PPO candidates;
- categorical encodings and reward/observation normalization;
- hyperparameter protocol separated from final evaluation;
- repeated-seed comparison against simple baselines; and
- failure-analysis dashboards.

Acceptance: no RL policy is called better unless its confidence interval and robustness checks support that claim.

## Sprint 5 - Constrained and multi-objective decision-making

- explicit safety, capacity, service, and chosen equity constraints;
- Lagrangian/constrained policy variants;
- Pareto policy set across safety, cost, delay, and disparity;
- reward and label sensitivity analysis; and
- stakeholder policy-selection interface contract.

Acceptance: constraints are measured independently of scalar reward and Pareto dominance is tested from machine-readable metrics.

## Sprint 6 - Adaptive landlords and distribution shift

- agent-based landlord archetypes derived from literature, clearly marked as simulated;
- PettingZoo-style multi-agent environment;
- strategic adaptation, reporting suppression, and policy-shift scenarios;
- domain randomization and worst-case stress tests; and
- comparison of static versus adaptive policies.

Acceptance: MARL results are presented as stress tests, never as measured landlord behavior.

## Sprint 7 - Interactive policy laboratory

- high-quality Next.js experience and FastAPI service;
- NYC map, complaint timeline, capacity controls, and live simulation playback;
- policy/reward/constraint comparison and Pareto explorer;
- example-case explainability and data-lineage drawer;
- keyboard, color, mobile, and performance testing; and
- recruiter-friendly guided mode plus expert mode.

Acceptance: a new user can understand the question, run a scenario, compare policies, and find the limitations without reading the paper.

## Sprint 8 - Research and portfolio release

- complete technical report and reproducibility appendix;
- architecture diagrams, demo video, screenshots, and resume bullets;
- CI/CD, deployed application, observability, and cost controls;
- security/privacy review and dependency audit; and
- v1.0 release with archived experiment artifacts.

Acceptance: clean-clone reproduction works, deployed demo passes end-to-end checks, and every public claim links to evidence.
