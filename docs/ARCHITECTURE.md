# Target Architecture

## Design goals

The architecture must support a generic hardware pipeline while allowing domain-specific engineering tools and verification methods.

Priorities:

1. reliable verification loop
2. explicit engineering state
3. auditability/provenance
4. pluggable domain tools
5. fast hackathon implementation
6. polished release experience only after the core loop works

## High-level system

```text
User
  ↓
Astra orchestrator
  ↓
Canonical HardwareProject state
  ├─ requirements
  ├─ architecture
  ├─ interfaces
  ├─ parameters
  ├─ components/BOM
  ├─ design versions
  ├─ experiments
  ├─ verification contracts
  └─ evidence
  ↓
Tool adapters
  ├─ CAD
  ├─ sourcing
  ├─ engineering solvers
  ├─ manufacturing
  └─ assembly
  ↓
Verification engine
  ↓
PASS / FAIL / UNKNOWN (stale applicability means UNKNOWN / NEEDS RE-VERIFY)
  ↓
Selected engineering backend: Dalus through MCP / explicit local fallback
  + immutable artifact storage (not a second engineering authority)
  ↓
Release pipeline
  ├─ interactive 3D
  ├─ build package
  ├─ assembly guide
  ├─ video
  └─ PDF
```

## Canonical engineering state

Do not make CAD files the primary source of truth.

Use a structured `HardwareProject` model, conceptually:

```json
{
  "project_id": "...",
  "mission": {},
  "requirements": [],
  "architecture": {},
  "interfaces": [],
  "parameters": {},
  "components": [],
  "design": {},
  "design_version": "v17",
  "verification_contracts": [],
  "evidence": [],
  "experiments": [],
  "release": {}
}
```

The exact schema should stay simple for the hackathon. It can evolve later.

## Dalus adapter and local backend

Per D021, all Dalus integration uses its MCP connection exclusively. Inspect the server's actual capabilities before mapping the operations below; these are internal semantic interfaces, not assumed MCP tool names. Dalus is central to the P0 live demo. The local fallback supports account-free development and tests but cannot stand in for a claimed live Dalus integration. The runtime mediates writes so that Astra cannot author authoritative verification verdicts or evidence.

Expose a backend interface such as:

```ts
interface EngineeringBackend {
  getProjectState(projectId: string): Promise<HardwareProject>;
  upsertRequirement(...): Promise<void>;
  upsertArchitectureElement(...): Promise<void>;
  upsertInterface(...): Promise<void>;
  recordExperiment(...): Promise<void>;
  recordEvidence(...): Promise<void>;
  recordEvaluation(...): Promise<void>;
}
```

These are internal runtime operations, not unrestricted model tools. Only the trusted evaluator may record evaluations or authoritative evidence. The model submits validated proposals; the runtime applies permitted engineering changes through MCP. Baselines and design/evidence references pin revisions, and a candidate commit publishes dependent invalidation together with the design. Preserve a completion marker when remote writes cannot be atomic.

Implement:

- `DalusBackend`
- `LocalBackend` (JSON/SQLite)

Dalus should remain the rich system-of-record integration. The local backend exists for open-source accessibility and tests.

## Astra orchestrator

Prefer one primary orchestrator.

Responsibilities:

- understand mission
- propose requirement decomposition
- propose architecture
- plan verification
- choose next experiment based on failed/stale/unknown evidence
- request tool execution
- explain results
- create assembly/manufacturing plans after verification

The orchestrator must not directly set PASS.

## Thin harness loop

Execution order (conceptual; not implemented yet):

1. Persist the mission, reviewed requirement/interface/verification baseline, and initial design proposal.
2. Run the initial design through tools, persist raw evidence, check admissibility, and evaluate contracts deterministically.
3. If required work remains, give Astra the actual evidence, relevant current state, interfaces, and recent experiments. Request a structured experiment proposal.
4. Validate both schema and engineering authority: allowed changes, fixed baseline/scenario/source facts, expected design revision, and applicable bounds. Reject no-op or cycling changes under the run policy.
5. Record the hypothesis and expected effects; create a new immutable design; compute actual transitive invalidations; commit the candidate and invalidated applicability together.
6. Generate affected CAD/analysis artifacts, rerun affected tools, persist evidence, evaluate, and record measured experiment effects. Late results retain their originating versions.
7. Repeat only within explicit experiment/retry/time/call limits. Stop on scoped completion, unresolved missing evidence, no progress, error, cancellation, or budget exhaustion. The stop reason is separate from the evidence-derived verdict.
8. Export a candidate package with its actual gate status. Manufacturing/physical release claims require their own admissible evidence; an UNKNOWN item is never hidden to terminate the loop.

Initial default: at most five redesign experiments and two repair attempts per invalid proposal, with configurable API/tool and total-run time/call limits. Final scoped analysis completion is distinct from build/physical validation. The method implementation and evaluator are fixed trusted runtime code, not writable by the design agent.

## Tool surface

Keep tools semantic and limited.

Model-facing semantic actions:

- `get_system_state`
- propose requirements/architecture/interfaces for the baseline workflow
- query the available sourced component catalog
- propose an engineering experiment and allowed design patch
- request registered CAD/analysis/verification runs against a pinned design

Keep evidence persistence, verdict writes, protected contract/scenario/catalog updates, and release-policy changes runtime-owned. Requests to execute checks carry design/method references; model-authored metrics or PASS claims are not accepted as results. The internal tool router can still implement `build_cad`, `run_analysis`, manufacturing, assembly, and export operations behind that boundary.

Avoid exposing dozens of low-level calculation primitives to the model if normal code can compose them.

## Tool registry

Each tool should declare capabilities so the pipeline can select verification methods.

Example:

```yaml
name: aerosandbox
capabilities:
  - aerodynamic_analysis
  - stability_analysis
  - mission_analysis
inputs:
  - geometry
  - mass_properties
  - propulsion
outputs:
  - stall_speed
  - endurance
  - static_margin
```

Example:

```yaml
name: rmfg
capabilities:
  - manufacturing_feasibility
  - dfm_feedback
  - quote
inputs:
  - step_geometry
  - material
  - process
outputs:
  - findings
  - manufacturable
  - price
```

## Domain packs

Keep domain knowledge separate from the generic runtime.

Suggested structure:

```text
domains/
  generic/
    geometry/
    cost/
    assembly/
    manufacturability/
  aircraft/
    requirements/
    aerodynamics/
    propulsion/
    stability/
    structures/
    verification/
  electronics/
  robotics/
```

The aircraft domain pack is P0. Other directories can remain placeholders until the framework is proven.

## Aircraft tool path

For the reference implementation:

```text
Canonical HardwareProject / DesignVersion
  ├─ Aircraft CAD mapping -> build123d -> STEP / STL / web meshes
  ├─ Aircraft analysis mapping -> AeroSandbox + supporting calculations
  └─ Component / geometry / manufacturing / assembly checks
        ↓
Version-consistent artifacts and evidence
        ↓
Evidence admission -> deterministic requirement evaluator
```

CAD and analysis are derived from the same canonical geometry, components, units, and reference frames. Validate their consistency; a visually similar mesh does not prove that the simulated aircraft matches the exported one. TextToCAD remains an optional future proposal adapter.

Onshape is optional for final native CAD handoff, not required for the first verification loop.

## Manufacturing path

RMFG should be treated as a manufacturing verifier/plugin, not a functional verifier.

Example:

```text
Custom metal part STEP
  ↓
RMFG
  ↓
DFM findings + quote
  ↓
verification evidence
  ↓
FAIL -> redesign
PASS -> cost/manufacturing evidence
```

## Evidence model

Conceptual record:

```json
{
  "evidence_id": "SIM-0283",
  "requirement_id": "REQ-014",
  "design_version": "v17",
  "method": "mission_simulation",
  "tool": "aerosandbox",
  "tool_version": "...",
  "inputs": {},
  "assumptions": {},
  "raw_result": {},
  "metric": "endurance_min",
  "value": 27.3,
  "dependencies": ["battery", "mass", "wing_geometry", "propulsion"]
}
```

This conceptual record contains tool results, not an authoritative verdict. Store raw artifact references/hashes, input/source/scenario revisions, transitive dependency fingerprints, run timestamps, and diagnostics. A separate runtime-owned evaluation references admitted evidence plus requirement/contract/design revisions and records PASS / FAIL / UNKNOWN with a reason. Evidence for an old design remains immutable; its applicability to a changed design can become STALE.

## Dependency / invalidation graph

For the hackathon, this can be simple and explicit rather than a general symbolic dependency engine.

Example aircraft mappings:

- battery -> mass, CG, endurance, electrical
- wing geometry -> mass, aero, stability, structure, printability
- motor -> thrust, electrical, mass, mount loads, cost
- material -> mass, structure, manufacturability

When a dependency changes, mark the matching evidence STALE.

## Design lineage

Represent design versions and experiments explicitly.

```text
v1
 ├─ v2
 │   ├─ v3
 │   └─ v4
 └─ v5
```

The first hackathon version can stay mostly linear, but the schema should not make branching impossible.

## Component sourcing

Use structured component records:

```json
{
  "type": "motor",
  "manufacturer": "...",
  "part_number": "...",
  "source": "...",
  "price": 0,
  "mass_g": 0,
  "dimensions": {},
  "ratings": {},
  "cad_ref": "...",
  "data_quality": "sourced"
}
```

Do not silently mix model-estimated values with sourced values.

## Interface contracts

Interfaces should be explicit records before subsystem delegation.

Examples:

```json
{
  "id": "IF-MOTOR-MOUNT",
  "type": "mechanical",
  "between": ["motor", "motor_mount"],
  "constraints": {
    "bolt_pattern": "...",
    "max_envelope_mm": [0,0,0],
    "axial_load_n": 0
  }
}
```

## Assembly model

Use one canonical structured file such as `assembly.json`.

Example:

```json
{
  "step": 7,
  "title": "Install elevator servo",
  "parts": ["servo_elevator", "rear_fuselage"],
  "hardware": [{"part": "M2x8", "qty": 2}],
  "tools": ["2 mm driver"],
  "motion": {
    "part": "servo_elevator",
    "type": "translate",
    "axis": [0, -1, 0],
    "distance_mm": 35
  },
  "checks": ["servo horn faces trailing edge"]
}
```

The same data should drive:

- interactive assembly
- MP4 rendering
- illustrated PDF

## Final release application

Target navigation:

- Overview
- Verify
- Exploded
- Assembly
- BOM
- Manufacturing
- Files

The Verify view should be visually prominent and every status should expose evidence.

## Technology direction

Favor speed and reliability:

- Next.js / React
- Three.js or react-three-fiber
- OpenAI Responses API / Agents SDK for Astra
- Python service for engineering tools if convenient
- JSON/SQLite for local state
- Dalus adapter
- build123d/TextToCAD
- AeroSandbox
- RMFG adapter/MCP

Do not let framework choice delay the first functioning verification loop.
