# Demo status and honest presentation

Updated September 8, 2026. This records implementation evidence, not engineering release.

- Repository: https://github.com/sebastianvkl/OpenV
- Vercel website: https://openv-kohl.vercel.app
- One-minute recording: https://openv-kohl.vercel.app/demo/openv-demo.mp4

## Completed acceptance evidence

`run-38f998e18d41` started as a fresh public plain-English mission. Two actual
`gpt-6-astra` responses produced the initial design and a failure-driven spar
change from 8 to 10 mm. External deflection fell from 46.34 to 22.25 mm against
a 32.5 mm limit. Five dependent evidence records were invalidated; original
compatible electrical evidence was reused. Final state: 10 PASS, 0 FAIL,
8 UNKNOWN. Dalus MCP read-back was evaluated. All 55 package manifest entries
matched their downloaded file hashes. Runtime: 293 seconds. This is the video run.

`run-626e87d14855` is the newer public example using manufacturer-sourced motor
mass/dimensions and strengthened STEP identity, centroid, bounds and validity
checks. It has 43 CAD parts and 1.1443 kg modeled mass; 10 PASS, 0 FAIL, 7 UNKNOWN.
Its initial Astra proposal needed no repair. All 61 package hashes match. The
Dalus model is `d38e0d63-a066-496c-882b-853cb22dfaab`.

`astra-payload-repair-001` records the authorized payload amendment from 150 to
350 g on an older frozen component baseline. Astra proposed thinner shells and
a payload shift, then a thinner spar wall. Actual mass fell from 1.321 to 1.2215
to 1.1994 kg; static-margin failure was also repaired. All modeled checks passed;
release remained UNKNOWN. This is a historical experiment using the original
estimated 60 g motor, not the newer manufacturer's 70 g value. Do not transfer
its narrow mass margin to the newer component baseline. All 57 package hashes
match. Earlier interrupted runs remain inspectable and have no final package.

Twenty-nine automated tests pass, including a non-aircraft domain through the
same runtime, closed model schemas, actual SDK parsing, OAuth refresh,
forbidden changes, stale/conflicting evidence, immutable branch baselines,
package mass accounting and deliberate STEP translation/identity corruption.
Desktop/mobile rendering was inspected; no browser errors or mobile horizontal
overflow were observed. Public API and package responses use `no-store`.
Credential-pattern scans found no secrets in tracked files or the checked public
package. Credentials remain in restricted backend/local files.

## Remaining manufacturing work

CAD/fabrication outputs remain candidates. Hinges/linkages, fastening/joints,
retention, remaining vendor selections and process details remain open. The
current output is not a complete flight-ready manufacturing definition. Full
structural strength, assembly access/sequence, installed propulsion/endurance
and physical flight validation remain UNKNOWN. A solver PASS applies only to
its stated contract and assumptions; overall release remains blocked.

The video is a captioned recording of actual versioned results, with execution
waits removed. It is not a claim that the pipeline takes one minute. Credit
preexisting Astra/OpenAI, Dalus, AeroSandbox, build123d/OpenCascade and frontend
libraries; OpenV's pipeline, adapters, evidence handling and generated example
are the new project work.
