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

## Realistic viewer and operating-condition comparisons

Published on 2026-09-08. The viewer now uses material-specific printed, carbon,
plywood and metal surfaces, cosmetic component-envelope labels, internal callouts,
connection concepts, a detail camera and separate airflow, load-bench and flight
scenes. Geometry remains the generated CAD. Wiring, fixture and terrain graphics
are explicitly illustrative.

Four verification-only branches preserve the exact sourced-component aircraft;
these are independent checks of the earlier Astra proposal, not new Astra calls.
Each branch was defined and evaluated through Dalus MCP. Each package contains
63 verified file hashes, including the exact design's `simulation.json` diagnostic.

| Case | Public run | Trim angle | Static margin | Spar tip | PASS / FAIL / UNKNOWN |
| --- | --- | --- | --- | --- | --- |
| 12 m/s, sea level, 2.5 g | [Cruise](https://openv-kohl.vercel.app/?run=run-11489fb9d56e) | 1.84° | 21.29% | 21.66 mm | 10 / 0 / 7 |
| 8 m/s, sea level, 2.5 g | [Slow flight](https://openv-kohl.vercel.app/?run=run-9fd73d9de5d6) | 9.47° | 4.43% | 21.66 mm | 8 / 2 / 7 |
| 12 m/s, 2,000 m, 2.5 g | [Altitude](https://openv-kohl.vercel.app/?run=run-b876623930b6) | 2.94° | 23.37% | 21.66 mm | 10 / 0 / 7 |
| 12 m/s, sea level, 4 g | [Load](https://openv-kohl.vercel.app/?run=run-ca815bfb5566) | 1.84° | 21.29% | 34.66 mm | 10 / 0 / 7 |

Slow flight fails both the 8° trim-angle limit and the 5% minimum static margin.
The 4 g spar result is just inside the 35 mm deflection limit; this does not
establish joint or full-airframe strength. Release is FAIL for slow flight and
UNKNOWN for the other cases.

VLM computes 160 panels and 45 streamlines per case, with finite no-penetration
residuals below 1e-5. The panel colors represent normal force per area, not upper/
lower surface pressure or CFD. VLM uses the recorded AeroBuildup trim without
independent retrimming; the lift disagreement is shown. No visualization grants
PASS. Old runs remain immutable and display no flow field unless they contain
matching diagnostic data.

The UI switches instantly to an existing case only when parameters, components,
contracts and all other scenario inputs match. Otherwise presets remain drafts
and use the existing mission-amendment pipeline. A browser check exercises the
transition into a queued job without exposing stale scene results as recomputed.
