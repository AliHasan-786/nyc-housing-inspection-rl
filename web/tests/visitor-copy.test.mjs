import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const visitorCopyFiles = [
  "src/app/page.tsx",
  "src/app/layout.tsx",
  "public/og-civic-inspection-lab.svg",
];

for (const file of visitorCopyFiles) {
  const contents = await readFile(new URL(`../${file}`, import.meta.url), "utf8");
  assert.doesNotMatch(contents, /—|&#8212;|&mdash;/i, `${file} contains an em dash`);
}

const page = await readFile(new URL("../src/app/page.tsx", import.meta.url), "utf8");
assert.match(page, /Compare inspection policies under the same constraints\./);
assert.doesNotMatch(page, /Make public-service tradeoffs inspectable/);

console.log("visitor copy regression checks: pass");
