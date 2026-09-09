# Getting started

Use Python 3.12 and Node 20.19+ or 22.12+. The engineering stack includes native OpenCascade libraries; install the Python dependencies in a virtual environment.

## Run without service accounts

```sh
git clone https://github.com/sebastianvkl/OpenV.git
cd OpenV
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
npm ci --prefix web
npm run build --prefix web
OPENV_STORE=local python -m openv.cli --offline --run-id first-example
uvicorn openv.server:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Native CAD generation and solver evaluation take several minutes. `--offline` chooses a labeled deterministic proposal fixture; the CAD and engineering calculations are real. It does not call Astra or interpret arbitrary mission text. `OPENV_STORE=local` also avoids live Dalus access. Choose a fresh run ID each time: historical evidence is never overwritten.

The fixture's reference mission is a 150 g payload, 20-minute endurance target and 12 m/s cruise. It demonstrates actual failure, repair and dependent evidence invalidation. Targets are not guarantees; unsupported claims remain UNKNOWN.

## Use Astra

Copy `.env.example` to `.env`, set `OPENAI_API_KEY` and a model available to your account via `OPENV_MODEL`, then run:

```sh
python -m openv.cli 'Build a conventional RC motor-glider carrying a 150 g camera for 20 minutes.'
```

The reference deployment uses GPT-6 Astra. This requires the corresponding model access. The model proposes requirements and design changes; trusted runtime code owns comparisons and verdicts. Runs have experiment, retry and time limits.

## Connect Dalus through MCP

```sh
python -m openv.dalus login
```

Complete the OAuth flow, then set `OPENV_STORE=dalus` and `DALUS_TEAM_ID` in `.env`. The client discovers capabilities at `https://app.dalus.io/api/mcp`; the integration has no REST/database bypass. An incomplete or mismatched remote commit blocks progress.

One hardware system uses one persistent Dalus model across runs. Preserve `OPENV_AUTH_DIR/dalus-system.json` or the configured `OPENV_DALUS_MAPPING` alongside server state. This restricted file maps stable remote element IDs; it is not a duplicate engineering database. `OPENV_DALUS_MODEL_ID` can pin the model. To adopt an existing OpenV model, supply its mapping first: the adapter refuses an unmapped existing model rather than creating duplicates. Test history is retained while current statuses are invalidated before input updates.

## Develop the website

Keep the backend running on port 8000, then:

```sh
npm run dev --prefix web
```

Vite proxies `/api` and `/artifacts` to the backend. The STEP reader assets are prepared automatically by npm's predev/prebuild script. The website contains no model or Dalus credentials.

## Check changes

```sh
python -m pytest -q
npm test --prefix web
npm run build --prefix web
```

The Python suite covers verifiers, failure/redesign, invalidation, CAD export, packaging, authentication and persistent Dalus behavior. Browser-model unit checks cover STEP identities, units/placement and dimension extents. For visual work, also inspect desktop/mobile layouts and historical design selection in a browser.

## Outputs and viewing

Each run lives under `artifacts/<run-id>/` by default. Its immutable versions contain CAD, raw verifier outputs and visualization artifacts; the completed candidate package includes sourced BOM, fabrication/assembly files and a hash manifest. The package's exact gate and unknowns travel with it.

Assemble → STEP CAD reads the actual exported STEP. The first import can take about a minute. The browser can persist two tessellations and rechecks the source-file hash before reuse. Custom parts show generated CAD; purchased components currently remain labeled envelopes. Dimensions are CAD bounds, not manufacturing tolerance measurements.

The flight view interpolates version-bound point-mass solver samples where available. Historical examples without that artifact use an explicitly illustrative circuit. Neither presentation grants physical-flight verification.

For hosting, see [deployment](../deploy/README.md). Vercel hosts the website; native CAD and solver jobs run on the separate Python host.
