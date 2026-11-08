import assert from "node:assert/strict";

const visible = (selected, replay, error) =>
  error ? "unavailable" : replay?.run_id === selected ? "verified" : "pending";

assert.equal(visible("new", { run_id: "old" }), "pending");
assert.equal(visible("new", undefined, "hash failed"), "unavailable");
assert.equal(visible("aggregate", undefined), "pending");
assert.equal(visible("new", { run_id: "new" }), "verified");
assert.equal(visible("missing", undefined, "index missing"), "unavailable");

const position = (day, min, max, width = 100) => (day - min) / (max - min) * width;
assert.equal(position(1, 1, 37), 0);
assert.equal(position(37, 1, 37), 100);
assert.ok(position(3, 1, 37) - position(1, 1, 37) < position(37, 1, 37) - position(3, 1, 37));
console.log("replay-state frontend regressions: pass");
