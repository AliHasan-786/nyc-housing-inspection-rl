# Spec: NYC Housing Inspection RL — Sprint 3+ (continue the existing plan)

**Repo:** `AliHasan-786/nyc-housing-inspection-rl`. **Tier 1 — continue.** At Sprint 2 of 8: coursework audit, data pipeline, simulator, and baselines done; **no RL policies yet**; web alpha undeployed and using hardcoded preview formulas. Anchored on arXiv:2605.06482 (Ali is one of 27 co-authors) and ORIE 5570 coursework (`/Users/alihasan/Downloads/Career Directory/Cornell Tech/Semester 2 - Spring 2026/ORIE 5570 Reinforcement Learning with Operations Research Applications/` — use its lecture materials for method grounding).

## Why this project (purpose)

This is the "AI for public-interest allocation" chapter: equitable building-inspection allocation with a real published-paper anchor. Its credibility risk is the current gap between framing ("RL for equity") and substance (no policies trained). Sprint 3's job is to close that gap or state it honestly.

## Tasks (Sprint 3–4 scope)

1. **Land the July 11 PR** (3,106,954-complaint DOB-universe profile + data card) after the same one-day audit pattern; the data card becomes the repo's provenance anchor.
2. **First policies:** train the planned RL baselines (per the existing sprint plan — e.g., contextual bandit / tabular or small-network policy against the simulator) and evaluate against the existing non-RL baselines (priority-score, random, greedy). **The honest headline is whatever the numbers say** — if RL doesn't beat the operational baseline yet, that result is published with analysis, crypto-lab style. Equity metrics (per-borough / per-demographic coverage) reported alongside efficiency, since the project's thesis is the tradeoff.
3. **Kill the hardcoded preview formulas** in the web alpha — either wire it to real simulator outputs or clearly label it "illustrative mock" until Sprint 5. No silent fake numbers anywhere, ever.
4. **Interactive centerpiece (design now, build Sprint 4-5):** "you are the allocator" — visitor adjusts the equity-efficiency dial and watches which buildings get inspected and who bears the risk. This is the piece that makes the project legible to non-RL audiences.
5. Deployment deferred until the interactive centerpiece has real numbers behind it.

**Requires Ali:** PR-audit sign-off; sprint-plan confirmation; review of the equity-metric definitions (a judgment call, not a code call); compute budget if policies need more than a laptop (likely not at this scale).

## Acceptance

Data card merged; at least two trained policies with seeds + manifests; an evaluation table with CIs comparing RL vs. baselines on efficiency AND equity metrics; no hardcoded result anywhere in the web code (`rg` check); README states exactly which sprint the project is in and what is not yet built.
