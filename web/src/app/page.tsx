"use client";

import { useState } from "react";

import { type PolicyResult, runPolicyScenario } from "@/lib/policy-api";

type Policy = "fifo" | "risk" | "safety";

const policyCopy: Record<Policy, { title: string; label: string; detail: string }> = {
  fifo: { title: "FIFO / routine", label: "Baseline", detail: "Routes each complaint in arrival order." },
  risk: { title: "Risk tier", label: "Transparent rule", detail: "Escalates repeat, nighttime, unpermitted signals." },
  safety: { title: "Safety floor", label: "Guardrailed", detail: "Prevents deferral for declared high-severity signals." },
};

const apiPolicy: Record<Policy, "fifo_routine" | "risk_tier" | "safety_floor"> = {
  fifo: "fifo_routine", risk: "risk_tier", safety: "safety_floor",
};

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="metric"><p>{label}</p><strong>{value}</strong><span>{note}</span></article>;
}

export default function Home() {
  const [capacity, setCapacity] = useState(2);
  const [priority, setPriority] = useState(65);
  const [policy, setPolicy] = useState<Policy>("safety");
  const [remoteResult, setRemoteResult] = useState<PolicyResult | null>(null);
  const [activeSignature, setActiveSignature] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "error">("idle");
  const scenarioSignature = `${apiPolicy[policy]}-${capacity}-${priority}`;
  const resultIsCurrent = remoteResult?.policy === apiPolicy[policy] && activeSignature === scenarioSignature;
  const displayed = resultIsCurrent ? {
    found: `${remoteResult.actionableFound} / 16`,
    delay: `${remoteResult.meanDelayDays.toFixed(1)} days`,
    coverage: `${(remoteResult.inspected / 782 * 100).toFixed(0)}%`,
    review: `${remoteResult.actionableMissed}`,
  } : { found: "—", delay: "—", coverage: "—", review: "—" };
  async function runConnectedScenario() {
    setRunStatus("running");
    try {
      setRemoteResult(await runPolicyScenario({ snapshotDate: "2026-07-06", dailyCapacity: capacity, accessProbability: 1, safetyPriority: priority / 100, policy: apiPolicy[policy], seed: 0 }));
      setActiveSignature(scenarioSignature);
      setRunStatus("idle");
    } catch { setRunStatus("error"); }
  }
  return <main>
    <nav><a className="brand" href="#top">CIVIC <em>INSPECTION LAB</em></a><div><a href="#lab">Policy Lab</a><a href="#trust">Safety</a><a href="#evidence">Evidence</a></div></nav>
    <section id="top" className="hero"><div><p className="eyebrow">RESEARCH → PRODUCT → RESPONSIBLE AI</p><h1>Make public-service tradeoffs <i>visible.</i></h1><p className="lede">An interactive policy laboratory for exploring how staffing, triage rules, and safety guardrails shape municipal inspection queues.</p><div className="cta"><a href="#lab">Open Policy Lab <span>↓</span></a><a className="text-link" href="#evidence">Read the evidence</a></div></div><aside className="hero-card"><p>THE QUESTION</p><h2>How should a city use limited inspection capacity without making inequity invisible?</h2><dl><div><dt>782</dt><dd>verified AHV complaints</dd></div><div><dt>16</dt><dd>actionable outcomes</dd></div><div><dt>1</dt><dd>decision lab, not deployment</dd></div></dl></aside></section>
    <section className="thesis"><p className="section-label">THE PRODUCT CASE</p><h2>Technical systems are only useful when people can inspect their assumptions.</h2><p>Built from Ali Hasan&apos;s published municipal complaint-classification research and a reproducible NYC 311 data pipeline, Civic Inspection Lab turns RL concepts into a product decision surface for operators, policy reviewers, and community stakeholders.</p></section>
    <section id="lab" className="lab"><div className="section-head"><div><p className="section-label">INTERACTIVE POLICY LAB</p><h2>Change the policy. See the tradeoff.</h2></div><span className="sim-badge">{resultIsCurrent ? "VERSIONED POLICY RUN" : "RUN REQUIRED"}</span></div><div className="lab-grid"><aside className="controls"><label>Daily inspection capacity <output>{capacity} teams</output><input type="range" min="1" max="6" value={capacity} onChange={(event) => setCapacity(Number(event.target.value))} /></label><label>Safety priority <output>{priority}%</output><input type="range" min="20" max="100" value={priority} onChange={(event) => setPriority(Number(event.target.value))} /></label><fieldset><legend>Policy posture</legend>{(Object.keys(policyCopy) as Policy[]).map((item) => <button key={item} className={policy === item ? "selected" : ""} onClick={() => setPolicy(item)}><span>{policyCopy[item].label}</span>{policyCopy[item].title}</button>)}</fieldset><button className="run-scenario" onClick={runConnectedScenario} disabled={runStatus === "running"}>{runStatus === "running" ? "Running scenario…" : "Run versioned scenario"}</button>{runStatus === "error" && <p className="connection-note">Policy API unavailable. Metrics are withheld rather than approximated.</p>}<div className="assumption"><b>What this scenario assumes</b><p>Capacity and outcome behavior are scenario inputs. It is not a live city system or causal forecast.</p></div></aside><div className="results"><div className="result-title"><div><p>{resultIsCurrent ? `ARTIFACT ${remoteResult.artifactId}` : "SELECT CONTROLS, THEN RUN"}</p><h3>{policyCopy[policy].title}</h3><span>{policyCopy[policy].detail}</span></div><button className="review">Human review required</button></div><div className="metric-grid"><Metric label="Actionable findings" value={displayed.found} note="simulated discovery"/><Metric label="Average queue delay" value={displayed.delay} note="service responsiveness"/><Metric label="Coverage signal" value={displayed.coverage} note="operational group slice"/><Metric label="Cases for review" value={displayed.review} note="not auto-decided"/></div><div className="queue-chart"><div className="chart-label"><span>{resultIsCurrent ? "Queue chart follows the selected scenario" : "Queue chart available with a versioned scenario run"}</span><b>Capacity {capacity} teams/day</b></div><svg viewBox="0 0 700 170" role="img" aria-label="Illustrative queue pressure curve"><path d="M0 135 C65 108 75 133 126 91 S208 100 263 56 S355 118 421 66 S530 74 578 39 S650 80 700 27" fill="none" stroke="currentColor" strokeWidth="4"/><path d="M0 135 C65 108 75 133 126 91 S208 100 263 56 S355 118 421 66 S530 74 578 39 S650 80 700 27 L700 170 L0 170Z" fill="currentColor" opacity=".08"/></svg><div className="chart-scale"><span>DAY 1</span><span>DAY 15</span><span>DAY 30</span></div></div><div className="action-log"><p>EXPLAINABLE ACTION LOG</p><div><span className="tag urgent">EXPEDITE</span><b>Repeat complaint, nighttime context</b><small>Human confirmation before dispatch</small></div><div><span className="tag routine">ROUTINE</span><b>Known permit overlaps complaint window</b><small>Keep visible; do not silently dismiss</small></div></div></div></div></section>
    <section id="trust" className="trust"><div><p className="section-label">TRUST &amp; SAFETY BY DESIGN</p><h2>Optimization is not the same as permission.</h2></div><div className="guardrails"><article><b>01</b><h3>Human-in-the-loop</h3><p>No automated enforcement, closure, or legal action. Recommendations require accountable review.</p></article><article><b>02</b><h3>Fairness is audited</h3><p>Group coverage and delay are shown alongside efficiency. Borough is not treated as a demographic proxy.</p></article><article><b>03</b><h3>Uncertainty stays visible</h3><p>Historical outcomes are observational. Simulator output is labeled as counterfactual, not causal evidence.</p></article></div></section>
    <section id="evidence" className="evidence"><p className="section-label">EVIDENCE &amp; PROVENANCE</p><div><h2>From published research to a reproducible product case study.</h2><ul><li><b>Published foundation</b><span>Ali Hasan is a co-author of <i>Scaling the Queue</i>, arXiv:2605.06482.</span></li><li><b>Data lineage</b><span>Official NYC sources, checksummed snapshots, audited record linkage.</span></li><li><b>Technical depth</b><span>MDP formulation, Gymnasium simulator, baselines, policy logs, and planned RL benchmarks.</span></li></ul></div></section>
    <footer><span>© 2026 ALI HASAN</span><span>CIVIC AI / POLICY PRODUCT / RESPONSIBLE SYSTEMS</span></footer>
  </main>;
}
