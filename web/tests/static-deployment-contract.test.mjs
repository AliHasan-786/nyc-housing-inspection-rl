import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";

const metadata = JSON.parse(await readFile(new URL("../public/portfolio-metadata.json", import.meta.url), "utf8"));
const vercel = JSON.parse(await readFile(new URL("../vercel.json", import.meta.url), "utf8"));
const nextConfig = await readFile(new URL("../next.config.ts", import.meta.url), "utf8");

assert.equal(metadata.id, "rl-housing");
assert.equal(metadata.status, "published");
assert.equal(metadata.deployedUrl, "https://civic-inspection-lab.vercel.app");
assert.match(metadata.evidenceScope, /static explorer/i);
assert.match(metadata.source.repository, /^https:\/\/github\.com\//);
assert.match(metadata.source.frozenBenchmarkSourceTreeSha256, /^[a-f0-9]{64}$/);
assert.equal(metadata.source.explorerSourceRevision, "2efa76c0b74d03a3b5715acadcb1b4729d4e3422");
assert.equal(metadata.release.provider, "Vercel");
assert.equal(metadata.release.projectId, "prj_wZnMfxL1YIJPTez5BcnAkzeP9OiL");
assert.equal(metadata.release.deploymentId, "dpl_F2nWSCPQBGWm161RNtzGe9vGjBou");
assert.equal(metadata.release.immutableUrl, "https://civic-inspection-4yu3xquzt-ali-hasans-projects-734a68d1.vercel.app");
assert.equal(metadata.release.acceptedSourceRevision, "b28b0b5fd01a2e131dbc1a9f942b1913f4e15280");
assert.notEqual(metadata.release.acceptedSourceRevision, metadata.source.explorerSourceRevision);
assert.match(metadata.thumbnail.license, /MIT/);
assert.ok(metadata.methods.every((method) => method.url.startsWith("https://github.com/")));
await access(new URL(`../public${metadata.thumbnail.path}`, import.meta.url));

assert.equal(vercel.framework, "nextjs");
assert.equal(vercel.outputDirectory, "out");
assert.ok(!("functions" in vercel));
assert.ok(!("rewrites" in vercel));
assert.match(nextConfig, /output:\s*"export"/);

console.log("static deployment contract checks: pass");
