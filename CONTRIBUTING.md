# Contributing to OpenV

OpenV is a working reference implementation, with one aircraft domain and explicit extension points. Useful contributions include better sourced component data, independent verifiers, reproducible failing cases, CAD and assembly checks, and clearer evidence inspection.

Start with [AGENTS.md](AGENTS.md), the [documentation index](docs/README.md) and [verification philosophy](docs/VERIFICATION_PHILOSOPHY.md). The [execution plan](docs/EXECUTION_PLAN.md) records completed work and remaining scope; [decisions](docs/DECISIONS.md) explain architectural choices.

## Development

Follow [Getting started](docs/GETTING_STARTED.md). Run the backend on port 8000 and `npm run dev --prefix web` for the Vite development server; Vite proxies engineering API/artifact requests to the backend.

```sh
python -m pytest -q
npm test --prefix web
npm run build --prefix web
```

Use the explicit offline proposer for reproducible local work. It runs actual CAD and engineering calculations without an Astra call. Live model and Dalus credentials belong in your local environment, never a patch or screenshot. An offline proposer does not automatically override the selected engineering store: set `OPENV_STORE=local` for fully account-free operation.

## Engineering changes

The proposal agent cannot decide PASS, edit protected contracts, or generate its own accepted evidence. A new verifier must declare inputs/dependencies, version, units, admissible scope and assumptions. Include a known failing design and an input-change invalidation case. Missing data or methods must remain UNKNOWN.

Keep domain-specific behavior behind the [domain contract](docs/DOMAIN_PACKS.md). Review `tests/test_pipeline.py` for a minimal second-domain regression using the real orchestration loop. It is an extension example, not a supported production bracket domain.

A CAD/component change may alter mass, CG, interference, insertion access, procurement and flight calculations. Regenerate and re-verify dependent artifacts; preserve old design/evidence records. Keep manufacturer facts sourced and distinguish envelopes from detailed vendor CAD.

## Pull requests

Describe the concrete before/after behavior, relevant checks and remaining limitations. Update the execution plan for completed work and the decision log for meaningful architectural changes. Keep the application runnable, and avoid unrelated file moves or formatting changes in engineering patches.

For UI changes, check desktop/mobile layout, historical version selection and evidence provenance. A visualization or successful tool call does not create a verification PASS. Document third-party asset and dependency provenance; OpenV application code is MIT licensed and dependency licenses remain separate.
