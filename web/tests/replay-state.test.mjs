import assert from "node:assert/strict";
import {
  eventDayPosition,
  eventDayTicks,
  eventGeometry,
  ReplayLoader,
  replayMetrics,
  replayState,
} from "../src/lib/replay-core.js";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

const baseRun = {
  run_id: "seed-new",
  actionable_found: 2,
  actionable_unfound: 1,
  latent_actionable_total: 3,
  mean_delay_days: 1.5,
};
const validReplay = JSON.stringify({
  run: baseRun,
  daily_event_series: [
    { event_day: 1, admitted: 1, deferred: 0, inspection_attempts: 1, ending_backlog: 0 },
  ],
});
const entry = { sha256: "expected" };
const parse = async (text) => JSON.parse(text);
const verified = async () => true;

assert.equal(replayState(null, null, null), "aggregate");
assert.equal(replayState("seed-new", null, null), "pending");
assert.equal(replayState("seed-new", null, "failed"), "unavailable");
assert.equal(replayState("seed-new", { run: baseRun }, null), "verified");
assert.deepEqual(replayMetrics("pending", null, 82), {
  found: "Replay pending",
  unfound: "Replay pending",
  service: "Replay pending",
  delay: "Replay pending",
  deferrals: "Replay pending",
});
assert.equal(replayMetrics("unavailable", null, 82).service, "Unavailable");
assert.equal(replayMetrics("verified", JSON.parse(validReplay), 82).service, "1%");

const irregular = eventGeometry([
  { event_day: 1, admitted: 0, deferred: 0, inspection_attempts: 0, ending_backlog: 0 },
  { event_day: 3, admitted: 0, deferred: 0, inspection_attempts: 0, ending_backlog: 0 },
  { event_day: 37, admitted: 0, deferred: 0, inspection_attempts: 0, ending_backlog: 0 },
], 100);
assert.deepEqual(irregular.points.map((point) => point.x), [0, 100 / 18, 100]);
assert.deepEqual(eventDayTicks(irregular), [1, 19, 37]);
assert.equal(eventDayPosition(irregular, 1, 100), 0);
assert.equal(eventDayPosition(irregular, 3, 100), 100 / 18);
assert.equal(eventDayPosition(irregular, 19, 100), 50);
assert.equal(eventDayPosition(irregular, 37, 100), 100);
assert.deepEqual(eventGeometry([], 100), { min: null, max: null, points: [] });
assert.equal(eventDayPosition(eventGeometry([], 100), 5, 100), null);
const singleton = eventGeometry([{ event_day: 5 }], 100);
assert.deepEqual(singleton.points.map((point) => point.x), [0]);
assert.equal(eventDayPosition(singleton, 5, 100), 0);
assert.deepEqual(eventDayTicks(singleton), [5]);

const httpLoader = new ReplayLoader();
const httpFetch = deferred();
const httpFailurePromise = httpLoader.load(
  "seed-new",
  entry,
  () => httpFetch.promise,
  parse,
  verified,
);
httpFetch.reject(new Error("HTTP 503"));
const httpFailure = await httpFailurePromise;
assert.match(httpFailure.error, /Replay unavailable/);
assert.equal(httpFailure.value, null);

const hashLoader = new ReplayLoader();
const hashCheck = deferred();
const hashFailurePromise = hashLoader.load(
  "seed-new",
  entry,
  async () => validReplay,
  parse,
  () => hashCheck.promise,
);
await Promise.resolve();
hashCheck.resolve(false);
const hashFailure = await hashFailurePromise;
assert.match(hashFailure.error, /integrity/);
assert.equal(hashFailure.value, null);

const missingLoader = new ReplayLoader();
const missing = await missingLoader.load("seed-new", null, async () => validReplay, parse, verified);
assert.match(missing.error, /index entry unavailable/);
assert.equal(missing.value, null);

const seedSwitchLoader = new ReplayLoader();
const oldFetch = deferred();
const oldSeed = seedSwitchLoader.load("seed-old", entry, () => oldFetch.promise, parse, verified);
const newSeed = seedSwitchLoader.load("seed-new", entry, async () => validReplay, parse, verified);
oldFetch.resolve(JSON.stringify({ run: { ...baseRun, run_id: "seed-old" }, daily_event_series: [] }));
assert.equal((await oldSeed).stale, true);
assert.equal((await newSeed).value.run.run_id, "seed-new");

const hashRaceLoader = new ReplayLoader();
const oldHash = deferred();
const oldAfterFetch = hashRaceLoader.load("seed-old", entry, async () => JSON.stringify({ run: { ...baseRun, run_id: "seed-old" }, daily_event_series: [] }), parse, () => oldHash.promise);
await Promise.resolve();
const latestAfterHash = hashRaceLoader.load("seed-new", entry, async () => validReplay, parse, verified);
oldHash.resolve(true);
assert.equal((await oldAfterFetch).stale, true);
assert.equal((await latestAfterHash).value.run.run_id, "seed-new");

const aggregateLoader = new ReplayLoader();
const aggregateFetch = deferred();
const priorSeed = aggregateLoader.load("seed-new", entry, () => aggregateFetch.promise, parse, verified);
aggregateLoader.invalidate();
aggregateFetch.resolve(validReplay);
const staleAggregate = await priorSeed;
assert.equal(staleAggregate.stale, true);
assert.equal(staleAggregate.value, null);

console.log("production replay-core regressions: pass");
