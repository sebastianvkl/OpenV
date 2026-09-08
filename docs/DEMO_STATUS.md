# Demo status and honest presentation

Updated September 8, 2026. This is implementation evidence, not engineering release.

- Public repository: https://github.com/sebastianvkl/OpenV
- Public website: https://openv-kohl.vercel.app
- `dalus-reference-002`: labeled offline proposer, actual Dalus MCP, actual CAD,
  AeroSandbox and beam calculations. Initial 8 mm spar deflection fails; a 10 mm
  spar passes the explicitly modeled deflection check. Final release UNKNOWN.
- `run-4fa3f06063ca`: explicit user experiment from that accepted version. Wingspan
  increases from 1.3 to 1.7 m; the exact original baseline is preserved. Static
  margin and spar deflection fail. Dalus commit read-back is evaluated. The
  package has 57 hash-checked entries, including individual cut-part STEP files,
  printable-part STLs, stock dimensions, BOM, evidence and regeneration source.
- 29 automated tests pass, including a second minimal domain through the shared
  runtime, forbidden changes, stale/conflicting evidence, branch baselines and
  package mass accounting.

## Still required for acceptance

Astra credentials are provisioned and the API has returned actual proposals, including a geometry rejection and a corrected proposal. The accepted proposal generated a 39-part candidate through actual Dalus MCP and engineering tools. A public payload amendment produced mass/static-margin failures; Astra moved the payload 70 mm aft and the static-margin verifier returned PASS (0.319 to 0.191). The next rebuild exceeded the original runtime cap, so that run remains interrupted without a final package. A full completed repair package and fresh public plain-English mission are being validated. Do not describe fixtures or explicit user experiments as Astra runs.

CAD/fabrication outputs remain a candidate: hardware selections, joints,
retention, controls/hinges/linkages and manufacturing details remain open. The
current output is not a complete flight-ready manufacturing definition. Full
structural strength, assembly access/sequence, installed propulsion/endurance
and physical flight validation remain UNKNOWN. A solver PASS is scoped to its
contract; the overall release remains blocked.

The one-minute submission video should be captured after the actual Astra
trajectory is available. Show the mission, Dalus trace, real failure, experiment,
changed geometry, re-verification and matching package. Credit preexisting
Dalus, OpenAI, AeroSandbox, build123d/OpenCascade and frontend libraries; identify
the OpenV pipeline/adapters/generated candidate as today's new work.
