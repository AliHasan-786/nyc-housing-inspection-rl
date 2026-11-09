"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  BENCHMARK_INDEX_BYTES,
  BENCHMARK_INDEX_PATH,
  BENCHMARK_INDEX_SHA256,
} from "@/data/benchmark-explorer-manifest";
import {
  eventDayPosition,
  eventDayTicks,
  eventGeometry,
  ReplayLoader,
  replayMetrics,
  replayState,
} from "@/lib/replay";

import "./replay.css";

type Policy =
  | "fifo_routine"
  | "random"
  | "risk_tier"
  | "safety_floor"
  | "contextual_bandit"
  | "tabular_q_learning";
type Metric = { mean: number | null; ci95_low: number | null; ci95_high: number | null };
type Run = {
  run_id: string;
  policy: Policy;
  seed: number;
  daily_capacity: number;
  access_probability: number;
  actionable_found: number;
  actionable_unfound: number;
  actionable_deferred: number;
  latent_actionable_total: number;
  mean_delay_days: number | null;
};
type Scenario = {
  policy: Policy;
  daily_capacity: number;
  access_probability: number;
  metrics: Record<string, Metric>;
};
type Day = {
  event_day: number;
  admitted: number;
  deferred: number;
  inspection_attempts: number;
  ending_backlog: number;
};
type Replay = { run: Run; daily_event_series: Day[] };
type ReplayIndex = { run_id: string; path: string; sha256: string; bytes: number };
type Index = {
  scope: {
    declared_seeds: number[];
    evaluation_complaints: number;
    evaluation_actionables: number;
    train_complaints: number;
    repeated_buildings: number;
  };
  scenarios: Scenario[];
  seed_runs: Run[];
  replays: ReplayIndex[];
  provenance: { config_sha256: string; source_tree_sha256: string };
};

const policyCopy: Record<Policy, { title: string; label: string; detail: string }> = {
  fifo_routine: {
    title: "FIFO / routine",
    label: "Baseline",
    detail: "Routes each complaint in arrival order.",
  },
  random: {
    title: "Random",
    label: "Stress baseline",
    detail: "Makes declared actions without a learned score.",
  },
  risk_tier: {
    title: "Risk tier",
    label: "Transparent rule",
    detail: "Escalates repeat, nighttime, unpermitted signals.",
  },
  safety_floor: {
    title: "Safety floor",
    label: "Guardrailed",
    detail: "Prevents deferral for declared high-severity signals.",
  },
  contextual_bandit: {
    title: "Contextual bandit",
    label: "Learned",
    detail: "Small simulator baseline, not a deployment candidate.",
  },
  tabular_q_learning: {
    title: "Tabular Q-learning",
    label: "Learned",
    detail: "Small simulator baseline, not a deployment candidate.",
  },
};

async function sha(text: string) {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function pct(value: number) {
  return `${(value * 100).toFixed(0)}%`;
}

function aggregate(metric: Metric, unit = "") {
  if (metric.mean === null) return "Not comparable";
  const format = (value: number) => (unit === "%" ? pct(value) : `${value.toFixed(2)}${unit}`);
  return `${format(metric.mean)} [${format(metric.ci95_low!)}, ${format(metric.ci95_high!)}]`;
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="metric">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{note}</span>
    </article>
  );
}

function MarkerLegend({ kind, children }: { kind: "backlog" | "admit" | "attempt" | "defer"; children: string }) {
  return (
    <span>
      <svg aria-hidden="true" className={`legend-marker ${kind}`} viewBox="0 0 18 18">
        {kind === "backlog" && <path d="M 1 9 H 17" />}
        {kind === "admit" && <rect x="5" y="5" width="8" height="8" />}
        {kind === "attempt" && <circle cx="9" cy="9" r="4" />}
        {kind === "defer" && <path d="M 9 4 L 14 14 H 4 Z" />}
      </svg>
      {children}
    </span>
  );
}

function QueuePlot({ days }: { days: Day[] }) {
  const width = 700;
  const left = 50;
  const right = 18;
  const top = 18;
  const height = 150;
  const baseline = top + height;
  const geometry = eventGeometry(days, width - left - right);
  const maxCount = Math.max(
    1,
    ...days.flatMap((day) => [day.ending_backlog, day.admitted, day.inspection_attempts, day.deferred]),
  );
  const y = (value: number) => top + (1 - value / maxCount) * height;
  const x = (eventDay: number) => left + (eventDayPosition(geometry, eventDay, width - left - right) ?? 0);
  const backlogGuide = geometry.points
    .map((point: Day & { x: number }, index: number) => `${index ? "L" : "M"} ${left + point.x} ${y(point.ending_backlog)}`)
    .join(" ");
  const ticks = eventDayTicks(geometry);

  return (
    <>
      <div className="chart-legend" aria-label="Chart legend">
        <MarkerLegend kind="backlog">ending backlog (observed EOD)</MarkerLegend>
        <MarkerLegend kind="admit">admissions</MarkerLegend>
        <MarkerLegend kind="attempt">inspection attempts</MarkerLegend>
        <MarkerLegend kind="defer">deferrals</MarkerLegend>
      </div>
      <svg
        className="replay-plot"
        viewBox={`0 0 ${width} 242`}
        role="img"
        aria-label={`Sparse event-day chart. The horizontal axis is observed simulator event day ${geometry.min} through ${geometry.max}; the vertical axis is 0 through ${maxCount} cases per observed event day.`}
      >
        <text x="4" y={top + 4}>{maxCount}</text>
        <text x="26" y={baseline + 4}>0</text>
        <text x="4" y={top - 6}>cases</text>
        <path className="axis" d={`M ${left} ${top} V ${baseline} H ${width - right}`} />
        <path className="backlog-guide" d={backlogGuide} />
        {geometry.points.map((day: Day & { x: number }) => {
          const eventX = left + day.x;
          const triangleY = y(day.deferred);
          return (
            <g key={day.event_day}>
              <title>{`Event day ${day.event_day}: ${day.admitted} admissions, ${day.inspection_attempts} attempts, ${day.deferred} deferrals, ending backlog ${day.ending_backlog}.`}</title>
              <rect className="admission-mark" x={eventX - 7} y={y(day.admitted) - 3} width="6" height="6" />
              <circle className="attempt-mark" cx={eventX + 3} cy={y(day.inspection_attempts)} r="3" />
              <path
                className="deferral-mark"
                d={`M ${eventX + 10} ${triangleY - 4} L ${eventX + 14} ${triangleY + 3} H ${eventX + 6} Z`}
              />
              <circle className="backlog-mark" cx={eventX} cy={y(day.ending_backlog)} r="3" />
            </g>
          );
        })}
        {ticks.map((eventDay: number) => (
          <g key={eventDay}>
            <path className="tick" d={`M ${x(eventDay)} ${baseline} V ${baseline + 5}`} />
            <text x={x(eventDay)} y={baseline + 19} textAnchor="middle">{eventDay}</text>
          </g>
        ))}
        <text x={width / 2} y="218" textAnchor="middle">observed simulator event day (sparse; not calendar time)</text>
        <text x={width / 2} y="235" textAnchor="middle">marker height = cases per observed event day</text>
      </svg>
    </>
  );
}

export default function Home() {
  const [index, setIndex] = useState<Index | null>(null);
  const [indexError, setIndexError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [capacity, setCapacity] = useState(1);
  const [access, setAccess] = useState(1);
  const [policy, setPolicy] = useState<Policy>("safety_floor");
  const [seed, setSeed] = useState<number | "aggregate">("aggregate");
  const [replay, setReplay] = useState<Replay | null>(null);
  const [replayError, setReplayError] = useState<string | null>(null);
  const replayLoader = useRef(new ReplayLoader());

  useEffect(() => {
    let alive = true;
    setIndex(null);
    setIndexError(null);
    replayLoader.current.invalidate();
    setReplay(null);
    setReplayError(null);

    fetch(BENCHMARK_INDEX_PATH)
      .then(async (response) => {
        if (!response.ok) throw new Error(`index request failed (${response.status})`);
        const text = await response.text();
        if ((await sha(text)) !== BENCHMARK_INDEX_SHA256) throw new Error("index hash mismatch");
        return JSON.parse(text) as Index;
      })
      .then((value) => alive && setIndex(value))
      .catch(() => alive && setIndexError("Verified benchmark index unavailable. No estimates are shown."));

    return () => {
      alive = false;
    };
  }, [retry]);

  const scenario = useMemo(
    () => index?.scenarios.find((item) => item.policy === policy && item.daily_capacity === capacity && item.access_probability === access),
    [access, capacity, index, policy],
  );
  const run = useMemo(
    () => (seed === "aggregate" ? null : index?.seed_runs.find((item) => item.policy === policy && item.daily_capacity === capacity && item.access_probability === access && item.seed === seed)),
    [access, capacity, index, policy, seed],
  );

  useEffect(() => {
    const loader = replayLoader.current;
    const controller = new AbortController();

    setReplay(null);
    setReplayError(null);

    if (!index || !run) {
      loader.invalidate();
      return () => controller.abort();
    }

    const entry = index.replays.find((item) => item.run_id === run.run_id);
    loader
      .load(
        run.run_id,
        entry,
        async () => {
          const response = await fetch(entry?.path ?? "", { signal: controller.signal });
          if (!response.ok) throw new Error(`replay request failed (${response.status})`);
          return response.text();
        },
        async (text: string) => JSON.parse(text) as Replay,
        async (text: string, expectedHash: string) => (await sha(text)) === expectedHash,
        () => controller.signal.aborted,
      )
      .then((result: { stale: boolean; value: Replay | null; error: string | null }) => {
        if (result.stale || controller.signal.aborted) return;
        setReplay(result.value);
        setReplayError(result.error);
      });

    return () => controller.abort();
  }, [index, run]);

  const evidenceState = replayState(run?.run_id ?? null, replay, replayError) as "aggregate" | "pending" | "unavailable" | "verified";
  const days = evidenceState === "verified" ? replay!.daily_event_series : null;
  const seedMetrics = replayMetrics(evidenceState, replay, index?.scope.evaluation_complaints ?? 0) as Record<string, string>;
  const shown = run
    ? seedMetrics
    : scenario
      ? {
          found: aggregate(scenario.metrics.actionable_found),
          unfound: aggregate(scenario.metrics.actionable_unfound),
          service: aggregate(scenario.metrics.service_rate, "%"),
          delay: aggregate(scenario.metrics.mean_delay_days, " days"),
          deferrals: aggregate(scenario.metrics.actionable_deferred),
        }
      : { found: "—", unfound: "—", service: "—", delay: "—", deferrals: "—" };
  const statusLabel = evidenceState === "verified" ? "VERIFIED REPLAY" : evidenceState === "unavailable" ? "REPLAY UNAVAILABLE" : "REPLAY PENDING";

  return (
    <main>
      <nav>
        <a className="brand" href="#top">CIVIC <em>INSPECTION LAB</em></a>
        <div>
          <a href="#lab">Explorer</a>
          <a href="#methods">Methods</a>
          <a href="#provenance">Provenance</a>
        </div>
      </nav>
      <section id="top" className="hero">
        <div>
          <p className="eyebrow">RESEARCH → PRODUCT → RESPONSIBLE AI</p>
          <h1>Make public-service tradeoffs <i>inspectable.</i></h1>
          <p className="lede">A static, artifact-backed explorer of a frozen NYC inspection-triage benchmark—not a live city system.</p>
          <div className="cta">
            <a href="#lab">Explore evidence <span>↓</span></a>
            <a className="text-link" href="https://github.com/AliHasan-786/nyc-housing-inspection-rl">Source repository</a>
          </div>
        </div>
        <aside className="hero-card">
          <p>THE QUESTION</p>
          <h2>Does learned triage improve discovery without quietly abandoning service?</h2>
          <dl>
            <div><dt>120</dt><dd>declared simulator runs</dd></div>
            <div><dt>0</dt><dd>automated enforcement actions</dd></div>
            <div><dt>100%</dt><dd>static, reviewable evidence</dd></div>
          </dl>
        </aside>
      </section>
      <section className="thesis">
        <p className="section-label">THE PRODUCT CASE</p>
        <h2>Technical systems are only useful when people can inspect their assumptions.</h2>
        <p>Choose only frozen, evaluated cells. Aggregate results show seed-only uncertainty; a selected replay loads its verified event-day record.</p>
      </section>
      <section id="lab" className="lab">
        <div className="section-head">
          <div>
            <p className="section-label">FROZEN ARTIFACT EXPLORER</p>
            <h2>Compare policies. Inspect the failure mode.</h2>
          </div>
          <span className="sim-badge">{index ? `${(BENCHMARK_INDEX_BYTES / 1024).toFixed(0)} KB INDEX` : indexError ? "INDEX UNAVAILABLE" : "LOADING INDEX"}</span>
        </div>
        <div className="lab-grid">
          <aside className="controls">
            <fieldset>
              <legend>Daily capacity — evaluated only</legend>
              <div className="choice-row">
                {[1, 2].map((value) => <button disabled={!index} key={value} className={capacity === value ? "selected" : ""} aria-pressed={capacity === value} onClick={() => setCapacity(value)}>{value} team{value === 1 ? "" : "s"}</button>)}
              </div>
            </fieldset>
            <fieldset>
              <legend>Inspection access assumption</legend>
              <div className="choice-row">
                {[1, 0.8].map((value) => <button disabled={!index} key={value} className={access === value ? "selected" : ""} aria-pressed={access === value} onClick={() => setAccess(value)}>{pct(value)}</button>)}
              </div>
            </fieldset>
            <fieldset>
              <legend>Policy</legend>
              {(Object.keys(policyCopy) as Policy[]).map((value) => <button disabled={!index} key={value} className={policy === value ? "selected" : ""} aria-pressed={policy === value} onClick={() => setPolicy(value)}><span>{policyCopy[value].label}</span>{policyCopy[value].title}</button>)}
            </fieldset>
            <fieldset>
              <legend>Evidence view</legend>
              <button disabled={!index} className={seed === "aggregate" ? "selected" : ""} aria-pressed={seed === "aggregate"} onClick={() => setSeed("aggregate")}><span>All declared seeds</span>Aggregate + 95% seed CI</button>
              {index?.scope.declared_seeds.map((value) => <button key={value} className={seed === value ? "selected" : ""} aria-pressed={seed === value} onClick={() => setSeed(value)}><span>One verified replay</span>Seed {value}</button>)}
            </fieldset>
            {indexError ? <div className="assumption"><b>Unavailable</b><p>{indexError}</p><button onClick={() => setRetry((value) => value + 1)}>Retry index</button></div> : <div className="assumption"><b>Frozen choices only</b><p>No API, credentials, reward tuning, or policy execution occurs in this browser.</p></div>}
          </aside>
          <div className="results">
            <div className="result-title">
              <div>
                <p>{run ? `SEED ${run.seed} · ${statusLabel}` : index ? "AGGREGATE · FIVE DECLARED SEEDS" : indexError ? "VERIFIED INDEX UNAVAILABLE" : "LOADING VERIFIED INDEX"}</p>
                <h3>{policyCopy[policy].title}</h3>
                <span>{policyCopy[policy].detail}</span>
              </div>
              <span className="review">Counterfactual simulator</span>
            </div>
            <div className="metric-grid">
              <MetricCard label="Actionables found" value={shown.found} note={run ? "of latent actionables; withheld until verified" : "mean [95% seed CI]"} />
              <MetricCard label="Actionables unfound" value={shown.unfound} note="deferred + inaccessible + unserved" />
              <MetricCard label="Service rate" value={shown.service} note={run ? "inspection attempts / 82; withheld until verified" : "mean [95% seed CI]"} />
              <MetricCard label="Mean delay" value={shown.delay} note={run ? "served attempts only; withheld until verified" : "mean [95% seed CI]"} />
            </div>
            <div className="queue-chart">
              <div className="chart-label"><span>Event-day queue record</span><b>{run ? statusLabel : "SELECT A SEED"}</b></div>
              {days ? <>
                <p>Markers are observed end-of-event-day counts; dashed connections are visual guides only. Exact intra-day maxima and unobserved calendar days are unavailable and are not invented.</p>
                <QueuePlot days={days} />
                <div className="timeline" tabIndex={0}>
                  <table>
                    <caption>Accessible event-day source table; sparse observed event days only.</caption>
                    <thead><tr><th scope="col">Day</th><th scope="col">Admit</th><th scope="col">Attempt</th><th scope="col">Defer</th><th scope="col">End backlog</th></tr></thead>
                    <tbody>{days.map((day) => <tr key={day.event_day}><th scope="row">{day.event_day}</th><td>{day.admitted}</td><td>{day.inspection_attempts}</td><td>{day.deferred}</td><td>{day.ending_backlog}</td></tr>)}</tbody>
                  </table>
                </div>
              </> : <p>{replayError ?? (run ? "Loading selected replay; stale responses are discarded and hash mismatches are withheld." : "Select a declared seed to inspect its event-day record. Aggregate mode never draws an illustrative queue curve.")}</p>}
            </div>
            <div className="action-log">
              <p>INTERPRETATION CHECK</p>
              <div><span className="tag urgent">DEFER ≠ SUCCESS</span><b>{run ? shown.deferrals : scenario ? aggregate(scenario.metrics.actionable_deferred) : "—"}</b><small>Low end-of-day backlog can reflect cases never admitted to service.</small></div>
              <div><span className="tag routine">MISSING ≠ ZERO</span><b>Unfound includes inaccessible and queued/unserved actionables</b><small>Zero-service delay is not comparable, not a good-looking zero.</small></div>
            </div>
          </div>
        </div>
      </section>
      <section id="methods" className="trust">
        <div><p className="section-label">TRUST &amp; SAFETY BY DESIGN</p><h2>Optimization is not permission—and a low queue is not automatically good service.</h2></div>
        <div className="guardrails">
          <article><b>01</b><h3>Counterfactual only</h3><p>No predictive, causal, field-effectiveness, or deployment claim is made from these simulations.</p></article>
          <article><b>02</b><h3>Limits stay visible</h3><p>{index ? `${index.scope.train_complaints} train / ${index.scope.evaluation_complaints} evaluation complaints, ${index.scope.evaluation_actionables} actionables, ${index.scope.repeated_buildings} repeated buildings.` : "Verified index loading."}</p></article>
          <article><b>03</b><h3>No proxy fairness claim</h3><p>Seed-only intervals are not population inference. Operational geography is not a demographic fairness measure or proxy.</p></article>
        </div>
      </section>
      <section id="provenance" className="evidence">
        <p className="section-label">EVIDENCE &amp; PROVENANCE</p>
        <div>
          <h2>From coursework prototypes to a constrained, reproducible case study.</h2>
          <ul>
            <li><b>Original coursework</b><span>Earlier coursework included synthetic, in-sample prototypes; this release does not treat them as real-world validation.</span></li>
            <li><b>Methods</b><span><a href="https://github.com/AliHasan-786/nyc-housing-inspection-rl/blob/main/docs/research/temporal-benchmark-v1_1-correction.md">Correction protocol</a> · <a href="https://github.com/AliHasan-786/nyc-housing-inspection-rl/blob/main/docs/research/methodology.md">Methodology</a></span></li>
            <li><b>Provenance</b><span><a href="https://github.com/AliHasan-786/nyc-housing-inspection-rl/blob/main/docs/research/ahv-temporal-benchmark-v1_1.md">Corrected results</a> · config {index?.provenance.config_sha256.slice(0, 12) ?? "loading"}…</span></li>
          </ul>
        </div>
      </section>
      <footer>
        <a href="https://ali-hasan-ai.vercel.app">Return to Ali Hasan portfolio</a>
        <a href="https://github.com/AliHasan-786">Ali Hasan · Evidence Labs</a>
        <a href="https://github.com/AliHasan-786/nyc-housing-inspection-rl">Source</a>
      </footer>
    </main>
  );
}
