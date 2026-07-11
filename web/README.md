# Civic Inspection Lab Web Experience

The Policy Lab is a Next.js case-study experience for Product Management and Trust & Safety
audiences. It makes the simulator's operational choices, assumptions, limitations, and guardrails
legible without presenting a deployment recommendation.

## Run locally

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm build
```

Visit `http://127.0.0.1:3000`.

## Current behavior

The initial version uses a deterministic, browser-local scenario preview to make interaction
immediate. It is visibly labeled as simulated. It does not call an API, process personal data,
or make a recommendation.

## Integration boundary

`src/lib/policy-api.ts` specifies the request/result shape for the future FastAPI service. A
future client should read `NEXT_PUBLIC_POLICY_API_BASE_URL`, submit a declared scenario, and
render only returned artifact-backed results. The product must preserve data-snapshot,
assumption, policy, and counterfactual labels in that transition.
