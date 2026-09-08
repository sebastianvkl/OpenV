# OpenV submission materials

**Demo:** https://openv-kohl.vercel.app

**Video:** https://openv-kohl.vercel.app/demo/openv-demo.mp4

**Open-source repository:** https://github.com/sebastianvkl/OpenV

## Description

AI-generated hardware is a hypothesis. OpenV is an open-source engineering V
pipeline that turns a plain-English hardware mission into requirements, design,
CAD, external verification evidence, engineering experiments and candidate
manufacturing outputs. Astra proposes. Independent tools produce measurements.
Deterministic contracts decide PASS, FAIL or UNKNOWN. Dalus is the structured
engineering system of record through MCP only.

The RC motor-glider reference demonstrates a real public mission: an initial
spar fails deflection, Astra sees the measured failure and proposes a larger
tube, affected evidence becomes stale, CAD and solvers rerun, and the modeled
check passes. The website exposes real CAD, simulation outputs, experiment
history, assembly guidance and version-matched downloads. Visitors can launch
supported missions through the same bounded runtime.

## Built during the event

OpenV's reusable runtime, proposal/store/domain adapters, evidence admission and
invalidation, Dalus MCP mapping, aircraft reference CAD/calculations, candidate
packaging, tests, public API and interactive website.

Preexisting dependencies/services: OpenAI Astra, Dalus, AeroSandbox,
build123d/OpenCascade, React, Three.js and related libraries. Manufacturer facts
and UIUC propeller measurements retain source references. The supplied assembly
explorer inspired the interaction; no reference assets were copied.

## Video timeline

- 0–8 s: actual initial hypothesis and mission targets.
- 8–15 s: requirements and evidence trace in Dalus through MCP.
- 15–24 s: external spar-deflection failure, 46.3 mm versus 32.5 mm maximum.
- 24–34 s: actual 8-to-10 mm spar proposal and fresh 22.2 mm result.
- 34–42 s: engineering experiment, invalidation and measured outcome.
- 42–50 s: assembly candidate with unresolved verification visible.
- 50–60 s: CAD/manufacturing candidate, evidence-backed status and credits.

The captioned recording uses real run `run-38f998e18d41`; execution waits are
removed. That run took 293 seconds and produced ten scoped PASS results and
eight UNKNOWN requirements. The newer sourced-component example is
`run-626e87d14855`. Neither example is a complete manufacturing or physical
flight release. See DEMO_STATUS.md for exact evidence and limitations.
