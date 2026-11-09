import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const css = await readFile(new URL("../src/app/globals.css", import.meta.url), "utf8");
const requiredTokens = [
  "paper",
  "surface",
  "ink",
  "accent-text",
  "annotation-on-light",
  "queue-text",
  "focus-on-light",
  "focus-on-dark",
];
const tokens = Object.fromEntries(requiredTokens.map((name) => {
  const match = css.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`));
  assert.ok(match, `missing production CSS token --${name}`);
  return [name, match[1]];
}));

function relativeLuminance(hex) {
  const rgb = [0, 2, 4].map((index) => Number.parseInt(hex.slice(index + 1, index + 3), 16) / 255);
  const linear = rgb.map((value) => (value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4));
  return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2]);
}

function contrast(foreground, background) {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

for (const [foreground, background, label] of [
  [tokens["accent-text"], tokens.paper, "small accent text on paper"],
  [tokens["annotation-on-light"], tokens.surface, "status text on white"],
  [tokens["queue-text"], "#eef4ef", "chart text on queue panel"],
]) {
  assert.ok(contrast(foreground, background) >= 4.5, `${label} must meet 4.5:1`);
}

for (const [foreground, background, label] of [
  [tokens["focus-on-light"], tokens.paper, "focus ring on paper"],
  [tokens["focus-on-dark"], tokens.ink, "focus ring on dark controls"],
]) {
  assert.ok(contrast(foreground, background) >= 3, `${label} must meet 3:1`);
}

assert.match(css, /\.eyebrow,[\s\S]*?color: var\(--accent-text\)/);
assert.match(css, /\.result-title p,[\s\S]*?color: var\(--annotation-on-light\)/);

console.log("production contrast token checks: pass");
