# OpenV

**AI-generated hardware is a hypothesis.** OpenV runs the engineering V: intent → requirements → design → independent verification → failure → engineering experiment → redesign → evidence-backed status.

The first domain is a conventional electric RC motor-glider. Astra proposes; the runtime evaluates measurements from AeroSandbox, CAD geometry checks and deterministic calculations. Requirements use PASS / FAIL / UNKNOWN. Changing a design invalidates dependent evidence. Dalus is the live engineering system of record through MCP exclusively.

[Public demo](https://openv-kohl.vercel.app) · [One-minute video](https://openv-kohl.vercel.app/demo/openv-demo.mp4) · [Execution status](docs/EXECUTION_PLAN.md)

Published examples identify their proposer. Live Astra requires server credentials; an offline fixture is not an Astra run.

## Recorded engineering results

The [fresh public mission](https://openv-kohl.vercel.app/?run=run-38f998e18d41) ran actual Astra → Dalus MCP → CAD → verification → failure → Astra repair → re-verification. Excessive spar deflection prompted an 8-to-10 mm diameter change. The external calculation changed from 46.3 to 22.2 mm against a 32.5 mm limit. Five dependent evidence records were invalidated; unchanged electrical evidence was reused. The final ten modeled checks passed; eight requirements remained UNKNOWN.

The [current sourced-component example](https://openv-kohl.vercel.app/?run=run-626e87d14855) has 43 CAD parts and 1.1443 kg modeled mass, uses the updated manufacturer motor dimensions/mass, and passes the stronger STEP identity/position/dimension checks. It has ten PASS and seven UNKNOWN results. It needed no redesign; the earlier recorded run demonstrates that loop. Its [candidate package](https://openv-kohl.vercel.app/artifacts/run-626e87d14855/candidate-package.zip) includes STEP, printable-part STLs, cut-stock definitions, BOM, assembly sequence, source and evidence; all 61 manifest hashes were checked.

## Run locally

Python 3.12 and Node 20.19+ (or 22.12+) are required. CAD dependencies include native OpenCascade wheels.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m pytest -q
python -m openv.cli --offline --run-id first-example
cd web
npm ci
npm run build
cd ..
uvicorn openv.server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. The offline example runs actual CAD generation and engineering calculations with a **labeled deterministic fixture proposer**. It does not call Astra or decompose arbitrary mission text. Its reference mission is 150 g payload, 20 minutes and 12 m/s cruise. The first example exposes excessive spar deflection, changes the spar diameter, invalidates dependent evidence and verifies again.

For Astra, copy `.env.example` to `.env`, set `OPENAI_API_KEY`, then:

```sh
python -m openv.cli 'Build a conventional RC motor-glider carrying a 150 g camera for 20 minutes.'
```

No model can write verification status, change the verifier, or relax a frozen requirement. API/server runs are bounded. Public fixture execution is disabled unless `OPENV_ALLOW_FIXTURES=1` is explicitly set.

## Dalus through MCP

```sh
python -m openv.dalus login
```

Open the displayed OAuth URL. Tokens are stored in ignored `.openv/` files with restricted permissions. The client discovers the actual tools at `https://app.dalus.io/api/mcp`. Engineering writes must use discovered MCP capabilities; no REST/database bypass is provided. Set `OPENV_STORE=dalus` and `DALUS_TEAM_ID` in `.env` to use the live store. Requirements, components/variables, interfaces, test cases, evidence references and experiments are written through MCP and read back. An incomplete or mismatched remote commit blocks progress. `OPENV_STORE=local` is the explicit account-free fallback.

## What exists now

- A small domain-independent verification engine, frozen contracts, versioned evidence, dependency fingerprints and experiments.
- One shared CLI/service pipeline with Astra and explicit offline proposer adapters.
- Parametric STEP/STL candidates and meshes from the same CAD geometry used for mass properties and aircraft analysis inputs.
- AeroSandbox trim/static stability, idealized spar bending, cell-allocation compatibility, solid validity and print-envelope checks.
- Explore / Simulate / Assemble viewer, historical design selection, raw evidence, experiment log and candidate-package downloads.
- Simulation controls for wingspan, battery position and payload: verify an explicit change, or run checks and let Astra attempt repairs. A new run preserves the parent and its frozen requirements; payload changes explicitly amend the mission baseline.
- Candidate BOM accounts for every modeled mass, including installation allowances; cut-stock parts include individual STEP files and dimensions. Packages include regeneration source and a hash manifest.

The current CAD package is **a candidate, not a complete manufacturing release**. Hinge/linkage selections, fastening/joints, exact remaining vendor selections, access checks and process calibration still need work. The candidate includes split control surfaces, spar bores, ribs, access hatches and mounting candidates. UIUC wind-tunnel data for the APC Thin Electric 8x4 supports a bounded exploratory power estimate when required thrust lies inside the measured range; missing motor/ESC efficiency and battery discharge evidence still keep endurance UNKNOWN. The beam model uses declared material assumptions and does not prove full-airframe strength. Physical flight validation remains UNKNOWN. See `geometry.json`, `manifest.json`, and `FABRICATION.md` in each package for its exact coverage.

## Architecture

`openv/core.py` owns contracts and evaluation without aircraft formulas. `openv/aircraft.py` supplies the first domain's schema, reviewed methods and geometry mapping. `openv/cad.py` creates the manufacturing candidate. `openv/engineer.py` contains proposal-only model adapters. `openv/pipeline.py` is the public orchestration entry point. `openv/server.py` serves the same pipeline and its artifacts.

A replacement verifier must declare its version, dependencies, units and admissible measurement scope. Replacing a tool changes evidence fingerprints; a successful call alone cannot make a requirement pass. Unsupported domains/claims remain explicit rather than inheriting aircraft methods.

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md), [decisions](docs/DECISIONS.md), [verification philosophy](docs/VERIFICATION_PHILOSOPHY.md) and [execution plan](docs/EXECUTION_PLAN.md) for the source-of-truth design and remaining work.

## License and provenance

OpenV code is MIT licensed. Dalus and OpenAI are external services, not included in this repository. Dependency licenses remain their own. Manufacturer facts retain source links in the component catalog; estimated and assumed values are labeled. The example geometry is generated by this repository. The assembly-explorer reference inspired the interface; none of its assets were copied.

## Interactive analysis environments

The [computed cruise case](https://openv-kohl.vercel.app/?run=run-11489fb9d56e) adds actual VLM streamlines and panel normal loads to the sourced-component aircraft. In **Simulate**, switch between Airflow, Load bench and Flight, then select a computed operating condition. Presets reuse matching published results or prepare an explicit mission amendment for fresh checks. The [8 m/s case](https://openv-kohl.vercel.app/?run=run-9fd73d9de5d6) fails the trim-angle and minimum-static-margin requirements.

The flow artifact is bound to the exact trim evidence, design and inputs and included in the candidate-package hash manifest. VLM is a coarse inviscid lifting-surface diagnostic; the UI exposes its disagreement with the AeroBuildup trim model. It is not CFD, a stall prediction or physical flight validation. Structural views use the recorded idealized spar calculation; flight scenery and wiring routes are illustrative. None of these rendering improvements changes a requirement verdict.

The [animated 3D world](https://openv-kohl.vercel.app/?run=run-11489fb9d56e&view=flight) places the actual CAD aircraft in valley, coastal or mountain scenery. Choose Chase, Wing or Survey; pause, restart or change playback speed. Its prescribed circuit is illustrative and never supplies flight-verification evidence.
