import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";

const metadata = JSON.parse(await readFile(new URL("../public/portfolio-metadata.json", import.meta.url), "utf8"));
const vercel = JSON.parse(await readFile(new URL("../vercel.json", import.meta.url), "utf8"));
const nextConfig = await readFile(new URL("../next.config.ts", import.meta.url), "utf8");

assert.equal(metadata.id, "rl-housing");
assert.equal(metadata.deployedUrl, null);
assert.match(metadata.evidenceScope, /static explorer/i);
assert.match(metadata.source.repository, /^https:\/\/github\.com\//);
assert.match(metadata.source.frozenBenchmarkSourceTreeSha256, /^[a-f0-9]{64}$/);
assert.match(metadata.source.explorerSourceRevision, /^[a-f0-9]{40}$/);
assert.match(metadata.thumbnail.license, /MIT/);
assert.ok(metadata.methods.every((method) => method.url.startsWith("https://github.com/")));
await access(new URL(`../public${metadata.thumbnail.path}`, import.meta.url));

assert.equal(vercel.framework, "nextjs");
assert.equal(vercel.outputDirectory, "out");
assert.ok(!("functions" in vercel));
assert.ok(!("rewrites" in vercel));
assert.match(nextConfig, /output:\s*"export"/);

console.log("static deployment contract checks: pass");
