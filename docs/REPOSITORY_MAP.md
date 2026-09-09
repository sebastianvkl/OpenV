# Repository map

OpenV keeps one small Python package and one browser application. The integration boundaries are explicit modules; adding folder layers is not required to follow the verification loop.

```text
OpenV/
├── openv/                 Python engineering pipeline and tool adapters
├── web/
│   ├── src/              React workbench, Three.js scenes and STEP inspection
│   ├── scripts/          Build-time preparation of the isolated CAD reader
│   └── public/           Product screenshots, favicon and recorded demo
├── tests/                Engineering, integration-boundary and package regressions
├── docs/                 Design decisions, guides, scope and recording plan
├── deploy/               Python host setup and Vercel deployment guidance
├── .github/              Issue forms and pull-request template
├── AGENTS.md             Project instructions and verification invariants
├── CONTRIBUTING.md       Development and review conventions
└── README.md             Public project entry point
```

## Follow one engineering run

| Responsibility | Source |
|---|---|
| Public CLI | [`openv/cli.py`](../openv/cli.py) |
| HTTP service, admission and run artifacts | [`openv/server.py`](../openv/server.py) |
| Mission → verification → repair orchestration | [`openv/pipeline.py`](../openv/pipeline.py) |
| Contracts, evidence admission, deterministic comparison and invalidation | [`openv/core.py`](../openv/core.py) |
| Astra and explicit fixture proposers | [`openv/engineer.py`](../openv/engineer.py) |
| Static domain registry | [`openv/domains.py`](../openv/domains.py) |
| Dalus MCP sessions and OAuth | [`openv/dalus.py`](../openv/dalus.py) |
| Persistent system model, stable IDs and history | [`openv/dalus_store.py`](../openv/dalus_store.py) |

## Aircraft domain

| Responsibility | Source |
|---|---|
| Domain schema, catalog and verifier bindings | [`openv/aircraft.py`](../openv/aircraft.py) |
| Derived CAD and geometry export | [`openv/cad.py`](../openv/cad.py) |
| Installed-component interference and insertion checks | [`openv/installation.py`](../openv/installation.py) |
| Bounded propulsion analysis | [`openv/propulsion.py`](../openv/propulsion.py) |
| VLM visualization artifacts | [`openv/aircraft_visualization.py`](../openv/aircraft_visualization.py) |
| Point-mass response diagnostics | [`openv/flight_response.py`](../openv/flight_response.py) |
| Aircraft fabrication, assembly and package outputs | [`openv/aircraft_package.py`](../openv/aircraft_package.py) |

## Browser application

[`web/src/main.jsx`](../web/src/main.jsx) binds the workbench to versioned run snapshots. `scene.jsx` and `flight-world.jsx` render CAD and simulation data. `component-details.jsx` exposes frozen specifications and sources. `step-worker.js`, `step-model.mjs` and `step-cache.js` load, admit and cache display meshes; they do not write engineering verdicts. `project-story.jsx` presents a separately labeled recorded case study, and `presentation.css` owns its styling.

## Generated and private data

`artifacts/` contains local immutable runs. `.openv/` contains local operational/authentication data and development captures. `.env`, virtual environments, dependency folders, compiled `web/dist/` and generated CAD-reader binaries are ignored. These are not source directories and must not be committed. The public website references published artifacts; API keys and OAuth files stay on the engineering host.
