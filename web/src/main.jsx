import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import Scene from "./scene.jsx";

import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Download,
  ExternalLink,
  Layers3,
  LoaderCircle,
  Maximize2,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import "./style.css";

const url = (run, path) => `/artifacts/${run}/${path}`;
const human = (s) => s?.replaceAll("-", " ") || "";
const number = (n, d = 2) => (Number.isFinite(n) ? n.toFixed(d) : "—");
const api = async (path, options) => {
  const r = await fetch(path, options);
  if (!r.ok) {
    let message;
    try {
      message = (await r.json()).detail;
    } catch {
      message = r.statusText;
    }
    throw new Error(message);
  }
  return r.json();
};

function Badge({ status, children }) {
  return (
    <span className={`badge ${status?.toLowerCase()}`}>
      {status === "PASS" ? (
        <Check size={11} />
      ) : status === "FAIL" ? (
        <X size={11} />
      ) : (
        <span className="badge-dot" />
      )}
      {children || status}
    </span>
  );
}

function Chart({ aero }) {
  const points = aero?.envelope;
  if (!points?.length)
    return <p className="muted">A current solver run is needed.</p>;
  const w = 260,
    h = 95,
    max = Math.max(...points.map((p) => p.lift_n), aero.weight_n) * 1.08;
  const path = points
    .map(
      (p, i) =>
        `${i ? "L" : "M"}${12 + ((p.speed_mps - 8) / 10) * (w - 24)},${h - 12 - (p.lift_n / max) * (h - 24)}`,
    )
    .join(" ");
  const y = h - 12 - (aero.weight_n / max) * (h - 24);
  return (
    <div className="chart">
      <svg
        viewBox={`0 0 ${w} ${h}`}
        aria-label="Calculated lift versus speed at fixed trim attitude"
      >
        {[0.25, 0.5, 0.75].map((v) => (
          <line
            key={v}
            x1="12"
            x2={w - 12}
            y1={h * v}
            y2={h * v}
            stroke="#dee3d9"
          />
        ))}
        <line
          x1="12"
          x2={w - 12}
          y1={y}
          y2={y}
          stroke="#c18b59"
          strokeDasharray="3 3"
        />
        <path d={path} fill="none" stroke="#467a62" strokeWidth="2.2" />
        {points.map((p) => (
          <circle
            key={p.speed_mps}
            cx={12 + ((p.speed_mps - 8) / 10) * (w - 24)}
            cy={h - 12 - (p.lift_n / max) * (h - 24)}
            r="2.5"
            fill="#467a62"
          />
        ))}
      </svg>
      <div className="chart-axis">
        <span>8 m/s</span>
        <span>13 m/s</span>
        <span>18 m/s</span>
      </div>
      <p className="tiny">
        Calculated lift · dashed line: weight
        <br />
        Fixed trim attitude, not a stall envelope.
      </p>
    </div>
  );
}

function VTrace({ stage, gate, onClick }) {
  const labels = ["Intent", "Requirements", "Design", "Verify", "Release"];
  const done =
    {
      mission: 0,
      requirements: 1,
      design: 2,
      verify: 3,
      evaluated: 3,
      redesign: 2,
      invalidated: 2,
      "experiment-complete": 3,
      package: 4,
      complete: 4,
    }[stage] ?? 0;
  return (
    <button
      className="v-trace"
      onClick={onClick}
      title="Inspect the engineering V and evidence"
    >
      <svg viewBox="0 0 252 38">
        <path
          d="M14 9 L70 24 L126 34 L182 24 L238 9"
          fill="none"
          stroke="#ced6c9"
          strokeWidth="1"
        />
        {labels.map((_, i) => (
          <circle
            key={i}
            cx={14 + 56 * i}
            cy={[9, 24, 34, 24, 9][i]}
            r="3"
            fill={
              i === 4
                ? gate === "PASS"
                  ? "#315d49"
                  : gate === "FAIL"
                    ? "#b06c55"
                    : "#b2a266"
                : i <= done
                  ? "#315d49"
                  : "#d1d7cb"
            }
          />
        ))}
      </svg>
      <div>
        {labels.map((s, i) => (
          <span key={s}>{i === 4 && gate !== "PASS" ? "Release open" : s}</span>
        ))}
      </div>
    </button>
  );
}

function App() {
  const [config, setConfig] = useState({});
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState(
    () => new URLSearchParams(window.location.search).get("run") || "",
  );
  const [run, setRun] = useState(null);
  const [geometry, setGeometry] = useState(null);
  const [versionId, setVersionId] = useState("");
  const [historical, setHistorical] = useState(null);
  const [mode, setMode] = useState("Explore");
  const [explode, setExplode] = useState(0);
  const [inside, setInside] = useState(false);
  const [selected, setSelected] = useState(null);
  const [preset, setPreset] = useState("perspective");
  const [autoRotate, setAutoRotate] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [detail, setDetail] = useState(null);
  const [missionOpen, setMissionOpen] = useState(false);
  const [mission, setMission] = useState(
    "Build a conventional electric RC motor-glider carrying a 150 g camera for 20 minutes at 12 m/s.",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [assembly, setAssembly] = useState(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [perturbation, setPerturbation] = useState({});
  const [environment, setEnvironment] = useState("airflow");
  const [labels, setLabels] = useState(true);
  const [wiring, setWiring] = useState(true);
  const [flow, setFlow] = useState(null);
  useEffect(() => {
    setFlow(null);
    if (!runId || !selectedVersionForFlow()) return;
    let cancelled = false;
    api(url(runId, `${selectedVersionForFlow()}/simulation.json`))
      .then((value) => {
        if (!cancelled && value.design_id === selectedVersionForFlow())
          setFlow(value);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
    function selectedVersionForFlow() {
      return versionId || run?.current_design_id;
    }
  }, [runId, versionId, run?.current_design_id, run?.visualization_file]);
  useEffect(() => {
    if (!runId) return;
    const address = new URL(window.location.href);
    address.searchParams.set("run", runId);
    window.history.replaceState(null, "", address);
  }, [runId]);
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const [c, r] = await Promise.all([
          api("/api/config"),
          api("/api/runs"),
        ]);
        if (cancelled) return;
        setConfig(c);
        setRuns(r);
        setError((previous) =>
          /Failed to fetch|NetworkError/.test(previous) ? "" : previous,
        );
        if (!runId && r.length) {
          const published =
            r.find(
              (item) =>
                item.status === "complete" &&
                item.visualization_file &&
                item.scenario?.cruise_mps === 12 &&
                item.scenario?.altitude_m === 0 &&
                item.scenario?.load_factor === 2.5,
            ) ||
            r.find(
              (item) =>
                item.status === "complete" &&
                item.current_design_id &&
                item.provider === "Astra",
            ) ||
            r.find(
              (item) => item.status === "complete" && item.current_design_id,
            ) ||
            r[0];
          setRunId(published.id);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      }
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId]);
  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await api(`/api/runs/${runId}`);
        if (!cancelled) setRun(r);
      } catch (e) {
        if (!cancelled && e.message !== "Not Found") setError(e.message);
      }
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId]);
  const selectedVersion = versionId || run?.current_design_id;
  const version = run?.versions?.find((v) => v.id === selectedVersion);
  const geometryFile = version?.geometry_file;
  useEffect(() => setPerturbation({}), [runId, selectedVersion]);
  useEffect(() => {
    if (!geometryFile || !runId) {
      setGeometry(null);
      return;
    }
    let cancel = false;
    api(url(runId, geometryFile))
      .then((g) => {
        if (!cancel) {
          setGeometry(g);
          setSelected(null);
        }
      })
      .catch((e) => setError(e.message));
    return () => {
      cancel = true;
    };
  }, [runId, geometryFile]);
  useEffect(() => {
    if (!versionId || !runId) {
      setHistorical(null);
      return;
    }
    let cancel = false;
    api(url(runId, `${versionId}/verification.json`))
      .then((r) => {
        if (!cancel) setHistorical(r);
      })
      .catch(() => setHistorical(null));
    return () => {
      cancel = true;
    };
  }, [runId, versionId]);
  useEffect(() => {
    let cancelled = false;
    if (run?.assembly_file && !versionId)
      api(url(runId, run.assembly_file))
        .then((value) => {
          if (!cancelled) setAssembly(value);
        })
        .catch(() => {});
    else setAssembly(null);
    return () => {
      cancelled = true;
    };
  }, [runId, run?.assembly_file, versionId]);
  useEffect(() => {
    if (!playing || !assembly) return;
    const id = setInterval(
      () =>
        setStep((n) => {
          if (n >= assembly.steps.length - 1) {
            setPlaying(false);
            return n;
          }
          return n + 1;
        }),
      4500,
    );
    return () => clearInterval(id);
  }, [playing, assembly]);
  const data = versionId ? historical : run;
  const evaluations = data?.evaluations || [];
  const staleIds = new Set(
    evaluations.flatMap((e) => e.stale_evidence_ids || []),
  );
  const evidence = (data?.evidence || []).filter((e) => !staleIds.has(e.id));
  const counts = {
    PASS: evaluations.filter((e) => e.status === "PASS").length,
    FAIL: evaluations.filter((e) => e.status === "FAIL").length,
    UNKNOWN: evaluations.filter((e) => e.status === "UNKNOWN").length,
  };
  const aero = evidence.find((e) => e.method === "aero")?.output?.raw;
  const structure = evidence.find((e) => e.method === "structure")?.output?.raw;
  const isRunning = run?.status === "running";
  const caseKey = runs.find((item) => item.id === runId)?.comparison_key;
  const recordedCases =
    !versionId && caseKey
      ? runs.filter(
          (item) =>
            item.status === "complete" &&
            item.visualization_file &&
            item.comparison_key === caseKey,
        )
      : [];
  const validFlow =
    flow?.design_id === selectedVersion &&
    flow?.trim_output_hash ===
      evidence.find((e) => e.method === "aero")?.output_hash
      ? flow
      : null;
  const stepInfo = assembly?.steps[step];
  const submit = async (offline = false) => {
    setBusy(true);
    setError("");
    try {
      const r = await api("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mission, offline }),
      });
      setRunId(r.id);
      setRun(null);
      setVersionId("");
      setGeometry(null);
      setMissionOpen(false);
      setMode("Explore");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const showEvidence = (id) => {
    setDetail(id);
    setDrawer(true);
  };
  const runExperiment = async (repair = false) => {
    setBusy(true);
    setError("");
    try {
      const parameter_changes = {};
      const mission_changes = {};
      for (const [key, value] of Object.entries(perturbation)) {
        if (
          ["payload_kg", "cruise_mps", "altitude_m", "load_factor"].includes(
            key,
          )
        )
          mission_changes[key] = value;
        else parameter_changes[key] = value;
      }
      const next = await api("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mission: run.system.mission,
          source_run_id: runId,
          source_design_id: selectedVersion,
          parameter_changes,
          mission_changes,
          verify_only: !repair,
        }),
      });
      setRunId(next.id);
      setRun(null);
      setGeometry(null);
      setVersionId("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const chooseRun = (id) => {
    setRunId(id);
    setVersionId("");
    setRun(null);
    setGeometry(null);
    setStep(0);
  };
  const selectCondition = (changes) => {
    if (!run?.system) return;
    const desired = { ...run.system.scenario, ...perturbation, ...changes };
    const designDraft = Object.keys(perturbation).some(
      (key) => !["cruise_mps", "altitude_m", "load_factor"].includes(key),
    );
    const cached =
      !designDraft &&
      recordedCases.find((item) =>
        ["cruise_mps", "altitude_m", "load_factor"].every(
          (key) => item.scenario[key] === desired[key],
        ),
      );
    if (cached) {
      setPerturbation({});
      chooseRun(cached.id);
    } else setPerturbation((p) => ({ ...p, ...changes }));
  };
  return (
    <main>
      <header>
        <a href="/" className="brand">
          <span className="brand-mark">∨</span>open
          <span className="brand-v">v</span>
          <span className="brand-tag">ENGINEERING, WITH EVIDENCE.</span>
        </a>
        <nav>
          {["Explore", "Simulate", "Assemble"].map((m, i) => (
            <button
              key={m}
              className={mode === m ? "active" : ""}
              onClick={() => {
                setMode(m);
                setSelected(null);
                if (m === "Assemble") setExplode(0.7);
                else setExplode(0);
                if (m === "Simulate") setInside(false);
              }}
            >
              <span>0{i + 1}</span>
              {m}
            </button>
          ))}
        </nav>
        <a
          className="source-link"
          href="https://github.com/sebastianvkl/OpenV"
          target="_blank"
          rel="noreferrer"
        >
          Open source <ArrowUpRight size={15} />
        </a>
      </header>
      <section
        className={`workspace ${mode === "Simulate" ? (environment !== "flight" ? "dark-simulation" : "flight-simulation") : ""}`}
      >
        <div className="canvas-wrap">
          {geometry ? (
            <Scene
              {...{
                geometry,
                explode,
                inside,
                selected,
                mode,
                evidence,
                evaluations,
                preset,
                autoRotate,
                labels,
                wiring,
                environment,
                flow: validFlow,
              }}
              onSelect={setSelected}
              stepGroups={mode === "Assemble" ? stepInfo?.groups : null}
            />
          ) : (
            <div className="empty-scene">
              <span className="large-v">∨</span>
              <p>
                {isRunning
                  ? "Engineering a first hypothesis…"
                  : "Every design starts as a hypothesis."}
              </p>
            </div>
          )}
        </div>
        <aside className="intro">
          <div className="eyebrow">
            <span className="live-dot" /> OPEN ENGINEERING / AIRCRAFT 01
          </div>
          <h1>
            {mode === "Explore" ? (
              <>
                A hypothesis.
                <br />
                Made tangible.
              </>
            ) : mode === "Simulate" ? (
              <>
                What happens
                <br />
                when it changes?
              </>
            ) : (
              <>
                See how it
                <br />
                comes together.
              </>
            )}
          </h1>
          <p className="intro-copy">
            {mode === "Explore"
              ? "From a mission to a design you can inspect. Every part has a purpose. Every claim needs evidence."
              : mode === "Simulate"
                ? "Change the mission. Follow the forces. Let independent engineering tools challenge the design."
                : "One design, one set of parts, one assembly sequence. Open checks stay visible at every step."}
          </p>
          <button className="primary" onClick={() => setMissionOpen(true)}>
            <Plus size={16} />{" "}
            {run ? "Define a new mission" : "Start a mission"}
            <ArrowUpRight size={15} />
          </button>
          <VTrace
            stage={run?.stage}
            gate={data?.gate}
            onClick={() => showEvidence(null)}
          />
          {run && (
            <div className="run-note">
              <span className="tiny-label">
                {isRunning
                  ? "LIVE ENGINEERING RUN"
                  : "RECORDED ENGINEERING RUN"}
              </span>
              <p>{run.provider}</p>
              {run.dalus && (
                <button
                  className="text-button"
                  onClick={() => showEvidence("dalus")}
                >
                  Dalus MCP · {run.dalus.commit} <ArrowUpRight size={12} />
                </button>
              )}
              {run.system?.scenario && (
                <p className="mission-facts">
                  {number(run.system.scenario.payload_kg * 1000, 0)} g payload
                  {" · "}
                  {number(run.system.scenario.cruise_mps, 0)} m/s
                  {" · "}
                  {number(run.system.scenario.endurance_min, 0)} min target
                </p>
              )}
              <small>
                {versionId ? (
                  "Historical design · evidence from this version"
                ) : isRunning ? (
                  <>
                    <LoaderCircle size={11} className="spin" />{" "}
                    {human(run.stage)}
                  </>
                ) : (
                  run.stop_reason?.replaceAll("_", " ")
                )}
              </small>
            </div>
          )}
        </aside>
        <div className="scene-top">
          <span>ALBATROSS / MOTOR-GLIDER</span>
          <span className="draft-label">CAD CANDIDATE</span>
        </div>
        {geometry && (
          <div className="scene-controls">
            <button
              className={preset === "perspective" ? "active" : ""}
              onClick={() => setPreset("perspective")}
            >
              Perspective
            </button>
            <button
              className={preset === "top" ? "active" : ""}
              onClick={() => setPreset("top")}
            >
              Top
            </button>
            <button
              className={preset === "side" ? "active" : ""}
              onClick={() => setPreset("side")}
            >
              Side
            </button>
            <button
              className={preset === "detail" ? "active" : ""}
              onClick={() => {
                setPreset("detail");
                setInside(true);
              }}
            >
              Detail
            </button>
            <button
              aria-label="Toggle auto rotation"
              className={autoRotate ? "active" : ""}
              onClick={() => setAutoRotate(!autoRotate)}
            >
              <RotateCcw size={13} />
            </button>
          </div>
        )}
        <aside className="inspector">
          {selected ? (
            <>
              <div className="panel-heading">
                <span>PART DETAILS</span>
                <button
                  onClick={() => setSelected(null)}
                  aria-label="Close part details"
                >
                  <X size={15} />
                </button>
              </div>
              <span className="tiny-label">{human(selected.group)}</span>
              <h2>{selected.name}</h2>
              <div className="part-specs">
                <div>
                  <span>Process</span>
                  <b>{human(selected.process)}</b>
                </div>
                <div>
                  <span>Modeled mass</span>
                  <b>{number(selected.mass_kg * 1000, 1)} g</b>
                </div>
                <div>
                  <span>Bounds</span>
                  <b>
                    {selected.dimensions_m
                      .map((v) => number(v * 1000, 0))
                      .join(" × ")}{" "}
                    mm
                  </b>
                </div>
              </div>
              <p className="small-copy">
                {selected.note || "Generated from canonical design parameters."}
              </p>
              <p className="tiny muted">{selected.mass_quality}</p>
              {selected.file && (
                <a
                  className="text-link"
                  href={url(runId, `${selectedVersion}/${selected.file}`)}
                  download
                >
                  Download part{" "}
                  {selected.file.endsWith(".step") ? "STEP" : "STL"}{" "}
                  <Download size={13} />
                </a>
              )}
            </>
          ) : mode === "Explore" ? (
            <>
              <div className="panel-heading">
                <span>THE DESIGN, UNPACKED</span>
                <Layers3 size={15} />
              </div>
              <div className="segmented">
                <button
                  className={!inside && explode === 0 ? "active" : ""}
                  onClick={() => {
                    setInside(false);
                    setExplode(0);
                  }}
                >
                  Assembled
                </button>
                <button
                  className={inside ? "active" : ""}
                  onClick={() => setInside(!inside)}
                >
                  Inside
                </button>
                <button
                  className={explode > 0 ? "active" : ""}
                  onClick={() => {
                    setInside(false);
                    setExplode(explode ? 0 : 1);
                  }}
                >
                  Exploded
                </button>
              </div>
              <div className="slider-label">
                <span>Explode distance</span>
                <span>{Math.round(explode * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1.5"
                step=".01"
                value={explode}
                onChange={(e) => setExplode(+e.target.value)}
                aria-label="Explode distance"
              />
              <div className="view-toggles">
                <label>
                  <input
                    type="checkbox"
                    checked={labels}
                    onChange={(e) => setLabels(e.target.checked)}
                  />{" "}
                  Part labels
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={wiring}
                    onChange={(e) => setWiring(e.target.checked)}
                  />{" "}
                  Wiring concept
                </label>
              </div>
              {(inside || explode > 0) && (
                <p className="tiny">
                  Colored routes illustrate connections; routing, connectors and
                  access remain unverified. Purchased parts are dimensional
                  envelopes.
                </p>
              )}
              <div className="model-stats">
                <div>
                  <b>
                    {geometry ? number(geometry.parameters.span_m, 2) : "—"}
                    <small>m</small>
                  </b>
                  <span>Wingspan</span>
                </div>
                <div>
                  <b>
                    {geometry
                      ? number(geometry.mass_properties.mass_kg, 2)
                      : "—"}
                    <small>kg</small>
                  </b>
                  <span>Modeled mass</span>
                </div>
                <div>
                  <b>{geometry?.parts.length || "—"}</b>
                  <span>CAD parts</span>
                </div>
              </div>
              <p className="tiny">
                Drag to orbit · scroll to zoom
                <br />
                Select any part to inspect its definition.
              </p>
            </>
          ) : mode === "Simulate" ? (
            <>
              <div className="panel-heading">
                <span>INDEPENDENT ANALYSIS</span>
                <Settings2 size={15} />
              </div>
              <div
                className="environment-tabs"
                aria-label="Analysis environment"
              >
                {[
                  ["airflow", "Airflow"],
                  ["structure", "Load bench"],
                  ["flight", "Flight"],
                ].map(([id, name]) => (
                  <button
                    key={id}
                    className={environment === id ? "active" : ""}
                    onClick={() => setEnvironment(id)}
                  >
                    {name}
                  </button>
                ))}
              </div>
              <div className="condition-presets">
                {[
                  [
                    "Cruise",
                    { cruise_mps: 12, altitude_m: 0, load_factor: 2.5 },
                  ],
                  [
                    "Slow flight",
                    { cruise_mps: 8, altitude_m: 0, load_factor: 2.5 },
                  ],
                  [
                    "High altitude",
                    { cruise_mps: 12, altitude_m: 2000, load_factor: 2.5 },
                  ],
                  ["4 g load", { load_factor: 4 }],
                ].map(([name, changes]) => (
                  <button
                    key={name}
                    disabled={!run?.system || !version}
                    onClick={() => selectCondition(changes)}
                  >
                    {name}
                  </button>
                ))}
              </div>
              {run?.system &&
                Object.keys(perturbation).some((k) =>
                  ["cruise_mps", "altitude_m", "load_factor"].includes(k),
                ) && (
                  <div className="condition-draft">
                    <b>Draft condition · results below are unchanged</b>
                    <p>
                      {perturbation.cruise_mps ??
                        run.system.scenario.cruise_mps}{" "}
                      m/s ·{" "}
                      {perturbation.altitude_m ??
                        run.system.scenario.altitude_m}{" "}
                      m ASL ·{" "}
                      {perturbation.load_factor ??
                        run.system.scenario.load_factor}{" "}
                      g
                    </p>
                    <button
                      className="primary"
                      disabled={busy || config.busy || isRunning}
                      onClick={() => runExperiment(false)}
                    >
                      Run condition checks <ArrowRight size={12} />
                    </button>
                  </div>
                )}
              {recordedCases.length > 0 && (
                <label className="recorded-cases">
                  OPEN A COMPUTED CONDITION
                  <select
                    aria-label="Computed condition"
                    value={
                      recordedCases.some((c) => c.id === runId) ? runId : ""
                    }
                    onChange={(e) => chooseRun(e.target.value)}
                  >
                    <option value="" disabled>
                      Select computed results
                    </option>
                    {recordedCases.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.scenario.cruise_mps} m/s · {c.scenario.altitude_m} m
                        · {c.scenario.load_factor} g · {c.gate}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <div className="simulation-summary">
                <span className="tiny-label">RECORDED CONDITIONS</span>
                <div className="case-verdicts">
                  <Badge status="PASS">{counts.PASS} PASS</Badge>
                  <Badge status="FAIL">{counts.FAIL} FAIL</Badge>
                  <Badge status="UNKNOWN">{counts.UNKNOWN} UNKNOWN</Badge>
                </div>
                <b>
                  {number(run?.system?.scenario?.cruise_mps, 0)} m/s ·{" "}
                  {number(run?.system?.scenario?.altitude_m, 0)} m ASL ·{" "}
                  {number(run?.system?.scenario?.load_factor, 1)} g structural
                  load
                </b>
                {environment === "airflow" ? (
                  <>
                    <p>
                      {validFlow?.status === "COMPUTED"
                        ? `${flow.panel_count} VLM panels · ${flow.streamlines_m.length} computed streamlines`
                        : validFlow?.reason ||
                          "No computed flow field for this version. Run checks below to generate it."}
                    </p>
                    {validFlow?.status === "COMPUTED" && (
                      <>
                        <a
                          className="text-link"
                          href={url(
                            runId,
                            `${selectedVersion}/simulation.json`,
                          )}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Inspect solver data <ArrowUpRight size={12} />
                        </a>
                        <div className="load-legend" />
                        <small>
                          Normal load color scale ·{" "}
                          {number(
                            -Math.max(
                              ...flow.panels.map((p) =>
                                Math.abs(p.normal_load_pa),
                              ),
                            ),
                            0,
                          )}{" "}
                          to{" "}
                          {number(
                            Math.max(
                              ...flow.panels.map((p) =>
                                Math.abs(p.normal_load_pa),
                              ),
                            ),
                            0,
                          )}{" "}
                          Pa
                        </small>
                        <p>
                          VLM lift {number(flow.lift_n, 1)} N · trim model{" "}
                          {number(flow.aero_buildup_lift_n, 1)} N. Difference{" "}
                          {number(flow.lift_difference_n, 1)} N.
                        </p>
                      </>
                    )}
                    <small>
                      Inviscid lifting surfaces, not CFD. No separation, body
                      blockage or propwash. Tracer animation is illustrative.
                    </small>
                  </>
                ) : environment === "structure" ? (
                  <>
                    <p>
                      Euler–Bernoulli spar bending ·{" "}
                      {number(structure?.stress_pa / 1e6, 1)} MPa root stress.
                    </p>
                    <small>
                      Deflection displayed 4×. Color shows bending moment.
                      Fixture illustrates ideal restraint; joints and full
                      airframe remain UNKNOWN.
                    </small>
                  </>
                ) : (
                  <>
                    <p>
                      Steady level trim at the recorded speed and atmospheric
                      altitude.
                    </p>
                    <small>
                      Terrain is illustrative, not surveyed or simulated. This
                      is a static trim solution, not a flight trajectory or
                      flight clearance.
                    </small>
                  </>
                )}
              </div>
              <div className="metric">
                <span>
                  {environment === "structure"
                    ? "Spar tip deflection"
                    : "Longitudinal static margin"}
                </span>
                <strong>
                  {number(
                    environment === "structure"
                      ? structure?.tip_deflection_m * 1000
                      : aero?.static_margin * 100,
                    1,
                  )}
                  <small>{environment === "structure" ? "mm" : "% MAC"}</small>
                </strong>
                <button
                  onClick={() =>
                    showEvidence(
                      environment === "structure"
                        ? "deflection"
                        : "stability-min",
                    )
                  }
                >
                  Inspect evidence <ArrowUpRight size={12} />
                </button>
              </div>
              <div className="part-specs">
                <div>
                  <span>Trim angle</span>
                  <b>{number(aero?.alpha_deg, 1)}°</b>
                </div>
                <div>
                  <span>Elevator</span>
                  <b>{number(aero?.elevator_deg, 1)}°</b>
                </div>
                <div>
                  <span>Spar tip deflection</span>
                  <b>{number(structure?.tip_deflection_m * 1000, 1)} mm</b>
                </div>
              </div>
              <Chart aero={aero} />
              {version && (
                <div className="experiment-controls">
                  <div className="panel-heading">
                    <span>WHAT IF YOU CHANGE…</span>
                  </div>
                  {[
                    [
                      "cruise_mps",
                      "Airspeed",
                      8,
                      22,
                      1,
                      "m/s",
                      run.system.scenario.cruise_mps,
                    ],
                    [
                      "altitude_m",
                      "Atmospheric altitude",
                      0,
                      2500,
                      100,
                      "m ASL",
                      run.system.scenario.altitude_m,
                    ],
                    [
                      "load_factor",
                      "Structural load factor",
                      1,
                      4,
                      0.1,
                      "g",
                      run.system.scenario.load_factor,
                    ],
                    [
                      "span_m",
                      "Wingspan",
                      0.9,
                      2,
                      0.05,
                      "m",
                      version.parameters.span_m,
                    ],
                    [
                      "battery_x_m",
                      "Battery position",
                      0.12,
                      0.46,
                      0.01,
                      "m aft of nose",
                      version.parameters.battery_x_m,
                    ],
                    [
                      "payload_kg",
                      "Mission payload",
                      0,
                      0.5,
                      0.025,
                      "kg",
                      run.system.scenario.payload_kg,
                    ],
                  ].map(([key, label, min, max, step, unit, original]) => (
                    <label className="experiment-slider" key={key}>
                      <span>
                        {label}
                        <b>
                          {number(perturbation[key] ?? original, 3)} {unit}
                        </b>
                      </span>
                      <input
                        type="range"
                        min={min}
                        max={max}
                        step={step}
                        value={perturbation[key] ?? original}
                        onChange={(e) =>
                          setPerturbation((p) => ({
                            ...p,
                            [key]: Number(e.target.value),
                          }))
                        }
                      />
                    </label>
                  ))}
                  <p className="tiny">
                    Draft values. Run checks to generate a new CAD version and
                    fresh evidence. Condition and payload changes amend the
                    mission baseline. The scene above retains recorded results
                    until checks finish.
                  </p>
                  <button
                    className="primary"
                    disabled={busy || config.busy || isRunning}
                    onClick={() => runExperiment(false)}
                  >
                    Run checks <ArrowUpRight size={14} />
                  </button>
                  <button
                    className="repair-button"
                    disabled={
                      busy || config.busy || isRunning || !config.astra_ready
                    }
                    onClick={() => runExperiment(true)}
                  >
                    Run + ask Astra to repair
                  </button>
                </div>
              )}
              <p className="tiny">
                AeroSandbox + analytical beam model.
                <br />
                Deflection overlay exaggerated 4×.
                <br />
                Each result applies to its recorded assumptions.
              </p>
            </>
          ) : (
            <>
              <div className="panel-heading">
                <span>GUIDED ASSEMBLY</span>
                <Badge status="UNKNOWN">UNCHECKED</Badge>
              </div>
              <span className="step-number">
                {String(step + 1).padStart(2, "0")}
                <small>/ {assembly?.steps.length || "—"}</small>
              </span>
              <h2>
                {stepInfo?.title || "Assembly is generated with the package."}
              </h2>
              <p className="small-copy">
                {stepInfo?.action ||
                  "Finish a design run to inspect its assembly sequence."}
              </p>
              <div className="assembly-controls">
                <button
                  aria-label="Previous assembly step"
                  onClick={() => {
                    setPlaying(false);
                    setStep(Math.max(0, step - 1));
                  }}
                >
                  <ArrowLeft size={16} />
                </button>
                <button
                  className="primary"
                  disabled={!assembly}
                  onClick={() => setPlaying(!playing)}
                >
                  {playing ? <Pause size={14} /> : <Play size={14} />}{" "}
                  {playing ? "Pause" : "Play sequence"}
                </button>
                <button
                  aria-label="Next assembly step"
                  onClick={() => {
                    setPlaying(false);
                    setStep(
                      Math.min((assembly?.steps.length || 1) - 1, step + 1),
                    );
                  }}
                >
                  <ArrowRight size={16} />
                </button>
              </div>
              <p className="tiny">
                This sequence explains the candidate. Collision, access and
                order checks remain open.
              </p>
            </>
          )}
          <div className="evidence-summary">
            <div className="panel-heading">
              <span>FOLLOW THE EVIDENCE</span>
              <button
                onClick={() => showEvidence(null)}
                aria-label="Open verification evidence"
              >
                <ArrowUpRight size={15} />
              </button>
            </div>
            <div className="status-counts">
              <button onClick={() => showEvidence(null)}>
                <i className="pass-dot" />
                {counts.PASS}
                <span>PASS</span>
              </button>
              <button onClick={() => showEvidence(null)}>
                <i className="fail-dot" />
                {counts.FAIL}
                <span>FAIL</span>
              </button>
              <button onClick={() => showEvidence(null)}>
                <i className="unknown-dot" />
                {counts.UNKNOWN}
                <span>UNKNOWN</span>
              </button>
            </div>
            <p className="tiny">
              Simulation evidence applies to stated conditions. Manufacturing
              and physical flight release remain gated.
            </p>
          </div>
        </aside>
        <div className="scene-caption">
          <span className="crosshair">+</span>
          <span>
            {mode === "Simulate"
              ? environment === "flight"
                ? "RECORDED TRIM / ILLUSTRATIVE TERRAIN"
                : environment === "structure"
                  ? "SPAR BENDING / IDEAL ROOT RESTRAINT"
                  : "COMPUTED VLM / UNBOUNDED INVISCID FLOW"
              : mode === "Assemble"
                ? "ASSEMBLY SEQUENCE / VERIFICATION OPEN"
                : "PARAMETRIC CAD / CANONICAL ENGINEERING STATE"}
          </span>
        </div>
      </section>
      <section className="run-strip">
        <div className="strip-label">
          <span className="tiny-label">ENGINEERING EXPERIMENTS</span>
          <span>
            {(run?.experiments?.length || 0) + (run?.user_experiment ? 1 : 0)}{" "}
            recorded changes
          </span>
        </div>
        <div className="version-list">
          {run?.origin && (
            <button onClick={() => chooseRun(run.origin.run_id)}>
              <ArrowLeft size={12} /> Parent design
            </button>
          )}
          {run?.versions?.map((v, i) => (
            <button
              key={v.id}
              className={selectedVersion === v.id ? "active" : ""}
              onClick={() => {
                setVersionId(i === run.versions.length - 1 ? "" : v.id);
                setSelected(null);
              }}
            >
              <span className="version-dot" />
              <span>V{String(i + 1).padStart(2, "0")}</span>
              <small>
                {i === 0
                  ? run?.origin
                    ? "User experiment"
                    : "Initial hypothesis"
                  : Object.entries(run.experiments[i - 1]?.change || {})
                      .map(([k, v]) => `${human(k)} ${number(v, 3)}`)
                      .join(", ")}
              </small>
              {i < run.versions.length - 1 && <ChevronRight size={12} />}
            </button>
          ))}
        </div>
        <button className="text-button" onClick={() => showEvidence(null)}>
          Open the experiment log <ArrowUpRight size={14} />
        </button>
      </section>
      <footer>
        <div className="footer-thesis">
          Generated is not verified.<span>Evidence makes the difference.</span>
          <a
            className="text-link"
            href="/demo/openv-demo.mp4"
            target="_blank"
            rel="noreferrer"
          >
            Watch the 1-minute demo <ArrowUpRight size={12} />
          </a>
        </div>
        <div className="footer-actions">
          {runs.length > 0 && (
            <select
              aria-label="Select engineering run"
              value={runId}
              onChange={(e) => chooseRun(e.target.value)}
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id} ·{" "}
                  {r.provider?.includes("fixture")
                    ? "offline fixture"
                    : r.status}
                </option>
              ))}
            </select>
          )}
          {versionId ? (
            <a
              className="download"
              href={url(runId, `${versionId}/cad/aircraft.step`)}
              download
            >
              <Download size={15} /> Selected version CAD
              <span>HISTORICAL STEP</span>
            </a>
          ) : run?.package_file ? (
            <a
              className="download"
              href={url(runId, run.package_file)}
              download
            >
              <Download size={15} />
              Candidate package<span>STEP · STL · BOM · EVIDENCE</span>
            </a>
          ) : (
            <span className="tiny">
              Package available after verification runs.
            </span>
          )}
        </div>
      </footer>
      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button aria-label="Dismiss message" onClick={() => setError("")}>
            <X size={15} />
          </button>
        </div>
      )}
      {missionOpen && (
        <div className="modal-backdrop" onClick={() => setMissionOpen(false)}>
          <section
            className="mission-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="panel-heading">
              <span>START WITH INTENT</span>
              <button
                onClick={() => setMissionOpen(false)}
                aria-label="Close mission"
              >
                <X size={18} />
              </button>
            </div>
            <h2>What should it do?</h2>
            <p>
              Describe your aircraft mission. OpenV will propose requirements,
              generate a design, and test it against independent engineering
              methods.
            </p>
            <label htmlFor="mission">Your mission</label>
            <textarea
              id="mission"
              value={mission}
              onChange={(e) => setMission(e.target.value)}
              maxLength={4000}
            />
            <div className="mission-hints">
              <span>01 Requirements</span>
              <span>02 Design</span>
              <span>03 Verify & redesign</span>
            </div>
            <p className="tiny">
              Today’s domain: conventional electric RC motor-gliders.
              Unsupported requirements stay UNKNOWN.
            </p>
            {!config.astra_ready && (
              <p className="availability">
                Live engineering is awaiting Astra credentials. Published
                results remain available to explore.
              </p>
            )}
            <div className="modal-actions">
              {config.fixtures_enabled && (
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => submit(true)}
                >
                  Run labeled offline fixture
                </button>
              )}
              <button
                className="primary"
                disabled={busy || !config.astra_ready || config.busy}
                onClick={() => submit(false)}
              >
                {busy ? (
                  <LoaderCircle className="spin" size={15} />
                ) : (
                  <Sparkles size={15} />
                )}
                Start engineering
                <ArrowRight size={15} />
              </button>
            </div>
          </section>
        </div>
      )}
      {drawer && (
        <div className="drawer-backdrop" onClick={() => setDrawer(false)}>
          <section
            className="evidence-drawer"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="panel-heading">
              <span>THE ENGINEERING RECORD</span>
              <button
                aria-label="Close evidence"
                onClick={() => setDrawer(false)}
              >
                <X size={18} />
              </button>
            </div>
            <h2>
              Every claim.
              <br />
              Its evidence.
            </h2>
            <p className="small-copy">
              {versionId
                ? "Historical design evidence"
                : "Current design evidence"}{" "}
              · {selectedVersion || "No design yet"}
            </p>
            <div className="record-links">
              <Badge status={data?.gate || "UNKNOWN"}>
                RELEASE {data?.gate || "UNKNOWN"}
              </Badge>
              <span>{run?.engineering_store}</span>
            </div>
            {run?.dalus && (
              <details className="dalus-trace" open={detail === "dalus"}>
                <summary>Dalus system of record · {run.dalus.commit}</summary>
                <p className="tiny">
                  Requirements, architecture, parameters, interfaces,
                  verification cases and experiments are committed through MCP.
                  This page displays the exported engineering evidence.
                </p>
                <p className="tiny">
                  Model: <code>{run.dalus.model_id}</code>
                </p>
                <pre>
                  {JSON.stringify(
                    {
                      requirements: run.dalus.requirements,
                      verification_cases: run.dalus.test_cases,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            )}
            {evaluations.map((e) => {
              const requirement = run?.system?.requirements.find(
                (r) => r.id === e.requirement_id,
              );
              const open = detail === e.requirement_id;
              return (
                <article
                  className={`requirement ${open ? "open" : ""}`}
                  key={e.requirement_id}
                >
                  <button
                    className="requirement-title"
                    onClick={() => setDetail(open ? null : e.requirement_id)}
                  >
                    <Badge status={e.status} />
                    <span>
                      {requirement?.statement || human(e.requirement_id)}
                    </span>
                    <ChevronDown size={14} />
                  </button>
                  {open && (
                    <div className="requirement-detail">
                      <span className="tiny-label">
                        {requirement?.level} / {requirement?.owner}
                      </span>
                      {run?.dalus?.requirements?.[e.requirement_id] && (
                        <p className="tiny">
                          Dalus requirement:{" "}
                          <code>
                            {run.dalus.requirements[e.requirement_id]}
                          </code>
                        </p>
                      )}
                      {requirement?.contracts.map((c) => (
                        <p key={c.id}>
                          {c.metric} {c.operator} {c.threshold} {c.unit}
                          <br />
                          <small>{c.scope}</small>
                        </p>
                      ))}
                      {requirement?.contracts.length === 0 && (
                        <p>
                          No verification contract covers this clause yet. Its
                          status remains UNKNOWN.
                        </p>
                      )}
                      {e.reasons.map((reason, i) => (
                        <p key={i}>{reason}</p>
                      ))}
                      {e.stale_evidence_ids?.length > 0 && (
                        <p className="stale">
                          Dependent evidence invalidated. Re-verification
                          required.
                        </p>
                      )}
                      {e.evidence_ids.map((id) => {
                        const item = evidence.find((x) => x.id === id);
                        return (
                          item && (
                            <div key={id} className="evidence-record">
                              <b>{item.method}</b>
                              <small>{item.tool_version}</small>
                              <code>{id}</code>
                              {item.output.assumptions.map((a, i) => (
                                <p key={i}>{a}</p>
                              ))}
                              <details>
                                <summary>
                                  Inputs, raw output and provenance
                                </summary>
                                <pre>{JSON.stringify(item, null, 2)}</pre>
                              </details>
                            </div>
                          )
                        );
                      })}
                    </div>
                  )}
                </article>
              );
            })}
            <h3 className="log-heading">Engineering experiments</h3>
            {[
              ...(run?.user_experiment ? [run.user_experiment] : []),
              ...(run?.experiments || []),
            ].map((exp, i) => (
              <article className="experiment" key={exp.id}>
                <span className="tiny-label">
                  EXPERIMENT {String(i + 1).padStart(2, "0")}
                </span>
                <h3>{exp.problem}</h3>
                <p>{exp.hypothesis}</p>
                <code>{JSON.stringify(exp.change)}</code>
                <p>
                  <b>Expected:</b> {exp.expected_effect}
                </p>
                <small>
                  {exp.invalidated_evidence.length} evidence records invalidated
                </small>
                {Object.entries(exp.actual_effect || {})
                  .filter(
                    ([, effect]) =>
                      effect.before !== effect.after || effect.after === "FAIL",
                  )
                  .map(([id, effect]) => (
                    <div className="experiment-outcome" key={id}>
                      <b>{human(id)}</b>
                      <span>
                        <Badge status={effect.before} /> →{" "}
                        <Badge status={effect.after} />
                      </span>
                      <p>{effect.reasons?.[0]}</p>
                    </div>
                  ))}
                <details>
                  <summary>Actual effect</summary>
                  <pre>{JSON.stringify(exp.actual_effect, null, 2)}</pre>
                </details>
              </article>
            ))}
          </section>
        </div>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
