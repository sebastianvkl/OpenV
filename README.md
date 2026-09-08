# OpenV

**AI-generated hardware is a hypothesis.** OpenV runs the engineering V: intent → requirements → design → independent verification → failure → engineering experiment → redesign → evidence-backed status.

The first domain is a conventional electric RC motor-glider. Astra proposes; the runtime evaluates measurements from AeroSandbox, CAD geometry checks and deterministic calculations. Requirements use PASS / FAIL / UNKNOWN. Changing a design invalidates dependent evidence. Dalus is the intended live engineering system of record through MCP exclusively.

## Run locally

Python 3.12 and Node 20+ are required. CAD dependencies include native OpenCascade wheels.

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

The current CAD package is **a candidate, not a complete manufacturing release**. Hinge/linkage selections, fastening/joints, exact remaining vendor selections, access checks and process calibration still need work. The candidate includes split control surfaces, spar bores, ribs, access hatches and mounting candidates. APC manufacturer-predicted propeller data supports a drag-dependent power estimate; missing motor/ESC efficiency and battery discharge evidence still keep endurance UNKNOWN. The beam model uses declared material assumptions and does not prove full-airframe strength. Physical flight validation remains UNKNOWN. See `geometry.json`, `manifest.json`, and `FABRICATION.md` in each package for its exact coverage.

## Architecture

`openv/core.py` owns contracts and evaluation without aircraft formulas. `openv/aircraft.py` supplies the first domain's schema, reviewed methods and geometry mapping. `openv/cad.py` creates the manufacturing candidate. `openv/engineer.py` contains proposal-only model adapters. `openv/pipeline.py` is the public orchestration entry point. `openv/server.py` serves the same pipeline and its artifacts.

A replacement verifier must declare its version, dependencies, units and admissible measurement scope. Replacing a tool changes evidence fingerprints; a successful call alone cannot make a requirement pass. Unsupported domains/claims remain explicit rather than inheriting aircraft methods.

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md), [decisions](docs/DECISIONS.md), [verification philosophy](docs/VERIFICATION_PHILOSOPHY.md) and [execution plan](docs/EXECUTION_PLAN.md) for the source-of-truth design and remaining work.

## License and provenance

OpenV code is MIT licensed. Dalus and OpenAI are external services, not included in this repository. Dependency licenses remain their own. Manufacturer facts retain source links in the component catalog; estimated and assumed values are labeled. The example geometry is generated by this repository. The assembly-explorer reference inspired the interface; none of its assets were copied.
