import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { ContactShadows, Html, Line, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
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
const point = ([x, y, z]) => [y, z, -x + 0.45];
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

function Part({ part, explode, inside, selected, onSelect, stepGroups }) {
  const ref = useRef();
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const a = part.mesh.positions;
    const p = [];
    for (let i = 0; i < a.length; i += 3) p.push(...point(a.slice(i, i + 3)));
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    g.setIndex(part.mesh.indices);
    g.computeVertexNormals();
    return g;
  }, [part]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  const side = Math.sign(part.centroid_m[1]);
  const offset = {
    wing: [side * 0.25, 0.08, 0],
    tail: [side * 0.1, 0.17, -0.12],
    fuselage: [0, -0.08, 0],
    structure: [0, 0.08, 0],
    power: [0.16, 0.24, 0.02],
    payload: [-0.18, 0.15, 0.08],
    controls: [side * 0.16, 0.25, 0],
  }[part.group] || [0, 0, 0];
  useFrame((_, delta) => {
    if (ref.current)
      ref.current.position.lerp(
        new THREE.Vector3(...offset.map((v) => v * explode)),
        1 - Math.exp(-8 * delta),
      );
  });
  const faded = inside && ["wing", "fuselage", "tail"].includes(part.group);
  const inactive = stepGroups && !stepGroups.includes(part.group);
  return (
    <mesh
      ref={ref}
      geometry={geometry}
      castShadow
      receiveShadow
      onClick={(e) => {
        e.stopPropagation();
        onSelect(part);
      }}
    >
      <meshStandardMaterial
        color={selected === part.id ? "#ca8150" : part.color}
        roughness={0.68}
        metalness={part.process === "cut-carbon" ? 0.18 : 0.04}
        transparent={faded || inactive}
        opacity={inactive ? 0.12 : faded ? 0.18 : 1}
        depthWrite={!faded && !inactive}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

function Camera({ preset, controls }) {
  const { camera } = useThree();
  useEffect(() => {
    const positions = {
      perspective: [1.85, 1.38, 2.28],
      top: [0, 3.1, 0.001],
      side: [3.1, 0.22, 0],
    };
    camera.position.set(...positions[preset]);
    camera.lookAt(0, 0.08, 0);
    controls.current?.update();
  }, [preset]);
  return null;
}

function AnalysisOverlay({ evidence, parameters }) {
  const aero = evidence.find((e) => e.method === "aero")?.output?.raw;
  const structure = evidence.find((e) => e.method === "structure")?.output?.raw;
  if (!aero?.cg_m) return null;
  const cg = point(aero.cg_m);
  const np = point([aero.x_np, 0, aero.cg_m[2]]);
  return (
    <group>
      <mesh position={cg}>
        <sphereGeometry args={[0.009, 20, 20]} />
        <meshBasicMaterial color="#d89050" depthTest={false} />
      </mesh>
      <Html position={[cg[0], cg[1] + 0.07, cg[2]]} center>
        <span className="scene-label amber">CENTER OF GRAVITY</span>
      </Html>
      <Line
        points={[
          [np[0] - 0.2, np[1] + 0.02, np[2]],
          [np[0] + 0.2, np[1] + 0.02, np[2]],
        ]}
        color="#38806b"
        lineWidth={1.5}
        dashed
        dashSize={0.015}
        gapSize={0.012}
      />
      <Html position={[0.21, np[1] + 0.05, np[2]]} center>
        <span className="scene-label">NEUTRAL POINT</span>
      </Html>
      <Line
        points={[cg, [cg[0], cg[1] + 0.32, cg[2]]]}
        color="#3e7c68"
        lineWidth={2}
      />
      <mesh position={[cg[0], cg[1] + 0.33, cg[2]]}>
        <coneGeometry args={[0.015, 0.035, 12]} />
        <meshBasicMaterial color="#3e7c68" />
      </mesh>
      <Html position={[cg[0] + 0.1, cg[1] + 0.32, cg[2]]} center>
        <span className="scene-label">L {number(aero.L, 1)} N</span>
      </Html>
      {structure?.spanwise &&
        [-1, 1].map((sign) => (
          <Line
            key={sign}
            points={structure.spanwise.map((s) => [
              sign * s.y_m,
              0.115 + 0.05 * s.y_m + s.deflection_m * 4,
              0.45 - (0.28 + 0.3 * parameters.chord_m),
            ])}
            color="#c38252"
            lineWidth={2}
          />
        ))}
    </group>
  );
}

function Scene({
  geometry,
  explode,
  inside,
  selected,
  onSelect,
  mode,
  evidence,
  preset,
  autoRotate,
  stepGroups,
}) {
  const controls = useRef();
  return (
    <Canvas
      shadows
      camera={{ position: [1.55, 1.15, 1.9], fov: 36, near: 0.01, far: 50 }}
      dpr={[1, 2]}
      onPointerMissed={() => onSelect(null)}
    >
      <color attach="background" args={["#eef0e8"]} />
      <ambientLight intensity={0.6} />
      <hemisphereLight args={["#ffffff", "#a5b2a1", 0.9]} />
      <directionalLight
        position={[-2, 4, 3]}
        intensity={1.7}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <directionalLight position={[2, 1, -2]} intensity={0.6} />
      <Suspense fallback={null}>
        <group>
          {geometry?.parts.map((part) => (
            <Part
              key={part.id}
              {...{ part, explode, inside, onSelect, stepGroups }}
              selected={selected?.id}
            />
          ))}
        </group>
        {mode === "Simulate" && geometry && (
          <AnalysisOverlay
            evidence={evidence}
            parameters={geometry.parameters}
          />
        )}
        <ContactShadows
          position={[0, -0.1, 0]}
          opacity={0.25}
          scale={5}
          blur={3}
          far={2}
          resolution={512}
          frames={Infinity}
        />
      </Suspense>
      <gridHelper
        args={[5, 50, "#e5e8df", "#e8ebe2"]}
        position={[0, -0.115, 0]}
      />
      <OrbitControls
        ref={controls}
        target={[0, 0.07, 0]}
        minDistance={0.5}
        maxDistance={5}
        enablePan
        autoRotate={autoRotate}
        autoRotateSpeed={0.5}
        maxPolarAngle={Math.PI * 0.48}
      />
      <Camera preset={preset} controls={controls} />
    </Canvas>
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

function VTrace({ stage, onClick }) {
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
            fill={i <= done ? "#315d49" : "#d1d7cb"}
          />
        ))}
      </svg>
      <div>
        {labels.map((s) => (
          <span key={s}>{s}</span>
        ))}
      </div>
    </button>
  );
}

function App() {
  const [config, setConfig] = useState({});
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState("");
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
        if (!runId && r.length) setRunId(r[0].id);
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
    if (run?.assembly_file)
      api(url(runId, run.assembly_file))
        .then(setAssembly)
        .catch(() => {});
    else setAssembly(null);
  }, [runId, run?.assembly_file]);
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
        if (key === "payload_kg") mission_changes[key] = value;
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
      <section className="workspace">
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
                preset,
                autoRotate,
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
          <VTrace stage={run?.stage} onClick={() => showEvidence(null)} />
          {run && (
            <div className="run-note">
              <span className="tiny-label">THIS RUN</span>
              <p>{run.provider}</p>
              <small>
                {isRunning ? (
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
                  Download part STL <Download size={13} />
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
              <div className="metric">
                <span>Longitudinal static margin</span>
                <strong>
                  {number(aero?.static_margin * 100, 1)}
                  <small>% MAC</small>
                </strong>
                <button onClick={() => showEvidence("stability-min")}>
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
                    fresh evidence. Payload changes amend the mission baseline.
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
              ? "ACTUAL SOLVER OUTPUTS / VERSION-BOUND"
              : mode === "Assemble"
                ? "ASSEMBLY SEQUENCE / VERIFICATION OPEN"
                : "PARAMETRIC CAD / CANONICAL ENGINEERING STATE"}
          </span>
        </div>
      </section>
      <section className="run-strip">
        <div className="strip-label">
          <span className="tiny-label">ENGINEERING EXPERIMENTS</span>
          <span>{run?.experiments?.length || 0} recorded changes</span>
        </div>
        <div className="version-list">
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
                  ? "Initial hypothesis"
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
          {run?.package_file ? (
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
              <details className="dalus-trace">
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
