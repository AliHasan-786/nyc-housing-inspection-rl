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

The default explorer is a cached, public-safe derivative of the corrected v1.1 benchmark. It works
without Python, API credentials, or a live model run. Visitors can only select evaluated
policy/capacity/access/seed cells; the browser does not calculate a new scenario or draw an
illustrative queue. Aggregate results show seed-only confidence intervals; selecting a seed reveals
the artifact-derived event-day backlog table.

The initial `public/data/benchmark-explorer/index.json` and the on-demand files in
`public/data/benchmark-explorer/replays/` contain no complaint, building, address, or borough
identifiers. The generated `src/data/benchmark-explorer-manifest.ts` pins the index hash used by
the browser. Regenerate them only from the verified local artifact set:

```bash
uv run python scripts/export_benchmark_explorer.py \
  --artifact-dir artifacts/benchmarks/ahv_temporal_rl_v1_1_correction \
  --config configs/experiments/ahv_temporal_rl_v1_1.json \
  --repo-root . \
  --output-dir web/public/data/benchmark-explorer \
  --web-manifest web/src/data/benchmark-explorer-manifest.ts
```

The exporter rejects mismatched output/config/source hashes, validates actionable accounting and
daily backlog conservation, and emits deterministic index/replay outputs.

## Integration boundary

`src/app/page.tsx` is the static explorer entry point. `src/lib/policy-api.ts` remains the
separate contract for the bounded local API, but the public-ready explorer does not depend on it.
The product preserves data-snapshot, assumption, policy, and counterfactual labels.

## Static deployment preparation

The web app is configured for a static export only. `next.config.ts` writes the built site to
`out/`, and `vercel.json` declares that directory for a Vercel project whose root directory is
`web/`. It has no server routes, backend dependencies, credentials, environment variables, or
raw-dataset access.

Run the release checks before any preview:

```bash
pnpm build
pnpm test:replay
pnpm test:copy
pnpm test:contrast
pnpm test:deployment
```

The build must contain `out/data/benchmark-explorer/index.json` and the 120 replay files under
`out/data/benchmark-explorer/replays/`. `public/portfolio-metadata.json` is a public-safe handoff
record. Its `deployedUrl` stays `null` until a reviewed deployment exists; its source revision
points to the prior explorer revision rather than to the metadata commit itself.
