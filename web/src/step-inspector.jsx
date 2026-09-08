import React, { useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { ReferenceImage } from "./component-reference.jsx";
export function StepInspector({
  state,
  url,
  selected,
  geometry,
  edges,
  setEdges,
  isolate,
  setIsolate,
  section,
  setSection,
  sectionZ,
  setSectionZ,
  explode,
  setExplode,
  retry,
  onSelect,
  hidden,
  onVisibility,
  dimensions,
  setDimensions,
  onFrame,
  onReset,
}) {
  const [query, setQuery] = useState("");
  const ready = state.status === "ready";
  const components =
    geometry?.parts
      .filter((p) => p.process === "purchase")
      .filter(
        (p, i, a) =>
          a.findIndex((q) => q.component?.id === p.component?.id) === i,
      ) || [];
  return (
    <section className="step-inspector">
      <div className="panel-heading">
        <span>FULL SYSTEM CAD</span>
        <span className={`step-reader-state ${state.status}`}>
          {ready
            ? "STEP loaded"
            : state.status === "error"
              ? "Import failed"
              : "Loading STEP"}
        </span>
      </div>
      <div className="cad-display-controls">
        <label><input type="checkbox" checked={dimensions} disabled={!selected} onChange={(e) => setDimensions(e.target.checked)} /> Dimensions</label>
        <button className="text-button" disabled={!selected} onClick={onFrame}>Frame selected</button>
        <button className="text-button" onClick={onReset}>Reset view</button>
      </div>
      {dimensions && selected && <p className="tiny">Overall CAD bounds in mm; not a tolerance or clearance measurement.</p>}
      <p className="tiny">
        Inspect the exported solid geometry. Custom parts retain their CAD
        detail; purchased components remain explicitly labeled envelopes.
      </p>
      {ready ? (
        <div className="step-file-summary">
          <b>{state.geometry.parts.length} parts</b>
          <span>{state.faces.toLocaleString()} CAD faces</span>
          <span>{(state.bytes / 1048576).toFixed(1)} MB STEP</span>
        </div>
      ) : (
        <p className="step-progress">
          {state.error || state.stage || "Preparing the assembly…"}
        </p>
      )}
      {state.status === "error" && (
        <button className="repair-button" onClick={retry}>
          <RefreshCw size={12} /> Retry STEP import
        </button>
      )}
      <div className="cad-display-controls">
        <label>
          <input
            type="checkbox"
            checked={edges}
            onChange={(e) => setEdges(e.target.checked)}
          />{" "}
          CAD edges
        </label>
        <label>
          <input
            type="checkbox"
            checked={isolate}
            disabled={!selected}
            onChange={(e) => setIsolate(e.target.checked)}
          />{" "}
          Isolate selected
        </label>
        <label>
          <input
            type="checkbox"
            checked={section}
            onChange={(e) => setSection(e.target.checked)}
          />{" "}
          Section cut
        </label>
      </div>
      <label className="experiment-slider">
        <span>Exploded view <b>{Math.round(explode * 100)}%</b></span>
        <input aria-label="CAD exploded view" type="range" min="0" max="1" step="0.01" value={explode} onChange={(e) => setExplode(+e.target.value)} />
      </label>
      {section && (
        <label className="experiment-slider">
          <span>
            Section height <b>{Math.round(sectionZ * 1000)} mm</b>
          </span>
          <input
            aria-label="Section height"
            type="range"
            min="-0.08"
            max="0.3"
            step="0.001"
            value={sectionZ}
            onChange={(e) => setSectionZ(+e.target.value)}
          />
          <small>Display cut only; cut faces are not capped.</small>
        </label>
      )}
      {url && (
        <a className="step-download" href={url}>
          <Download size={13} /> Download this assembly STEP
        </a>
      )}
      {selected && (
        <p className="tiny">
          {selected.process === "purchase"
            ? "Component envelope"
            : "Custom CAD"}
          {selected.stepFaceCount
            ? ` · ${selected.stepFaceCount} STEP faces`
            : ""}
          . Use Isolate selected to inspect it closely.
        </p>
      )}
      <details className="cad-parts">
        <summary>Assembly parts · {geometry?.parts.length || 0}{hidden.length ? ` · ${hidden.length} hidden` : ""}</summary>
        <input aria-label="Search assembly parts" placeholder="Search parts or manufacturer…" value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="cad-part-list">
          {(geometry?.parts || []).filter((p) => `${p.name} ${p.group} ${p.component?.manufacturer || ""} ${p.component?.part_number || ""}`.toLowerCase().includes(query.toLowerCase())).map((part) => (
            <div className={selected?.id === part.id ? "active" : ""} key={part.id}>
              <input type="checkbox" checked={!hidden.includes(part.id)} aria-label={`Show ${part.name}`} onChange={() => onVisibility(part.id)} />
              <button onClick={() => onSelect(part)}><b>{part.name}</b><small>{part.process === "purchase" ? "Component envelope" : part.process === "provided" ? "Payload envelope" : "Custom / stock CAD"}</small></button>
            </div>
          ))}
        </div>
      </details>
      {!selected && components.length > 0 && (
        <>
          <span className="tiny-label">
            PURCHASED COMPONENTS / PHOTO REFERENCES
          </span>
          <div className="component-gallery">
            {components.map((part) => (
              <button
                key={part.id}
                onClick={() => onSelect(part)}
                aria-label={`Inspect ${part.name}`}
              >
                <ReferenceImage part={part} />
                <b>{part.component?.name || part.name}</b>
              </button>
            ))}
          </div>
        </>
      )}
      {ready && (
        <details className="step-import-details">
          <summary>STEP source & reader</summary>
          <p className="tiny">
            Browser tessellation at 0.15 mm linear deflection. Names, scale and
            placement checked against the captured assembly for display; this
            adds no engineering PASS.
          </p>
          <p className="tiny">{state.cached ? "Saved geometry reused after rechecking the downloaded STEP hash." : "Read directly from STEP; saved locally for faster reloads when browser storage is available."}</p>
          <code>{state.hash}</code>
          <a href="/cad-kernel/NOTICE.txt" target="_blank" rel="noreferrer">
            Open-source reader & license ↗
          </a>
        </details>
      )}
    </section>
  );
}
