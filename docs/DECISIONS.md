# Accepted Decisions

This file records decisions already made in product/architecture discussion. Change them intentionally and document why.

## D001 - Verification is the core product

**Decision:** The project is verification-first, not CAD-first.

Generated CAD is only a hypothesis until external evidence closes requirements.

## D002 - General hardware pipeline, aircraft reference implementation

**Decision:** The open-source framework must be generic. The RC motor glider is the first domain pack and demo, not the core abstraction.

Use names like `HardwareProject`, not `AircraftDesigner`, in generic layers.

## D003 - Agentic engineering V-model

**Decision:** The pipeline should embody the engineering V-model:

user need -> requirements -> architecture -> detailed design -> implementation -> component/subsystem/system verification -> validation.

**Clarification (user reaffirmation, 2026-09-08):** The V is the governing execution and traceability model. Define verification contracts while decomposing requirements and interfaces; pair each left-side level with its corresponding right-side evidence in Dalus through MCP. Failures return to the responsible design level, invalidate affected artifacts/evidence, and trigger re-verification. Parent/system/mission claims require their own evidence and cannot pass solely because child component checks pass. Preserve one simple orchestrator rather than introducing an agent/service for each V stage.

## D004 - Astra cannot mark its own work PASS

**Decision:** Astra may propose verification plans and interpret failures, but deterministic/runtime code or an external verifier determines PASS/FAIL/UNKNOWN.

## D005 - Dalus is the engineering system of record

**Decision:** Dalus is a strategically important external integration for requirements, architecture, interfaces, parameters, analyses/test cases, verification state/evidence references, and traceability.

The hackathon repo stays open source. Dalus itself is not reimplemented or open-sourced.

Provide a simplified local fallback backend.

## D006 - Canonical engineering state is not CAD

**Decision:** Keep a structured, machine-readable design/system state as canonical. Generate CAD from it.

This makes iteration, diffing, verification dependency tracking, and multi-tool output more reliable.

## D007 - Thin harness, one main orchestrator

**Decision:** Prefer a simple explicit loop with one Astra orchestrator over a large multi-agent swarm or complex orchestration graph.

Add specialists only when they solve a concrete problem.

## D008 - TextToCAD/build123d is preferred for autonomous CAD generation

**Decision:** Use local/code-driven parametric CAD for the core loop because it is easier to automate, version, validate, render, and iterate.

Onshape is valuable as an optional final/native CAD handoff and professional engineering workspace, but should not block the core verification loop.

## D009 - AeroSandbox is the reference aircraft physics backend

**Decision:** Use AeroSandbox (plus simple deterministic calculations where useful) for the aircraft reference implementation rather than integrating heavy CFD for the hackathon.

## D010 - RMFG is a manufacturing verifier

**Decision:** RMFG should answer questions such as:

- can this part be manufactured using this material/process?
- what DFM issues exist?
- what does it actually cost?

RMFG manufacturability is not evidence that the part will survive functional loads.

## D011 - Real component data over model invention

**Decision:** Prefer exact sourced component data (manufacturer, part number, dimensions, mass, ratings, price, vendor CAD) over LLM-created physical specifications.

Assumed values must be marked.

## D012 - Interface contracts before delegation

**Decision:** Mechanical, electrical, thermal, software, and load interfaces should be explicit before independently designing subsystems.

## D013 - Evidence invalidation is a first-class feature

**Decision:** Design changes should mark affected verification evidence stale. Do not leave previously green evidence looking valid after dependent inputs change.

## D014 - Iterations are experiments

**Decision:** Record the problem, hypothesis, change, expected effect, invalidated evidence, and measured outcome for each design iteration.

## D015 - UNKNOWN is a legitimate outcome

**Decision:** If a requirement cannot currently be proven, show UNKNOWN rather than manufacturing confidence.

## D016 - Robustness is separate from nominal verification

**Decision:** After nominal PASS, run challenge scenarios when feasible and report known weaknesses separately.

## D017 - Assembly output must also be verified

**Decision:** Do not trust an AI-generated assembly animation by default. Validate insertion paths, collisions, fastener/tool access, and ordering where possible.

## D018 - One assembly source drives web, video, and PDF

**Decision:** Use one canonical `assembly.json` (or equivalent structured plan) to drive:

- interactive assembly experience
- assembly animation/video
- illustrated PDF manual

## D019 - Final UI should feel like a released product

**Decision:** The final experience should be a polished, interactive hardware page with:

- Overview
- Verify
- Exploded
- Assembly
- BOM
- Manufacturing
- Files

Verification should be visually prominent, not buried.

## D020 - Reference aircraft materials

**Decision:** Initial motor-glider concept should use a pragmatic mixed manufacturing strategy, likely:

- Bambu PLA Aero for lightweight custom printed geometry
- carbon tube/rod for high-efficiency structural reinforcement
- COTS electronics/propulsion
- metal/plywood only where loads/process make sense

Do not force every part to be printed.

## D021 - Dalus integration is exclusively through MCP

**Decision (user clarification, 2026-09-08):** Dalus must play a major role in the live hackathon experience, and the OSS runtime must connect to it only through MCP.

The user-provided MCP endpoint is `https://app.dalus.io/api/mcp`. Read-only discovery confirms an OAuth-protected service; authenticated tool access still needs to be established.

Requirements, engineering state, experiments, verification evidence references, and traceability should be mapped to the capabilities actually exposed by the Dalus MCP server. Do not substitute direct REST or database access, invent tool methods, or recreate Dalus locally. The minimal local fallback remains useful for account-free development and tests; it does not satisfy the live Dalus demonstration requirement.

The runtime must mediate model actions so that MCP access does not let Astra author authoritative verification verdicts or fabricate evidence. Deterministic verifiers and evaluators remain the only source of PASS.

## D022 - Today's demo prioritizes visual engineering repair and model capability

**Decision (user clarification, 2026-09-08):** The September 8 demo should look polished, address the verification gap in AI-generated hardware/CAD, challenge Astra's engineering reasoning, and make Dalus central. Target completion is approximately 4:00 p.m. Pacific.

Prefer one compelling visible failure/redesign/re-verification workflow over broad platform infrastructure. Preserve verification invariants while reducing the number of integrations and implemented abstractions. The proposed implementation details and checkpoint schedule are in `EXECUTION_PLAN.md` and still await implementation approval.

## D023 - Real CAD, a manufacturing package, and visual aircraft simulation are core deliverables

**Decision (user clarification, 2026-09-08):** Today's requested result is a CAD and manufacturing package for the aircraft, not physical fabrication and flight testing. The experience must visualize simulations and show what fails when design parameters or the mission change.

Real parametric CAD/export, a full-reference-system BOM and fabrication/assembly information, aircraft analysis, and a mission/design-change demonstration belong in P0. A schematic-only model and a few component-level checks do not satisfy this scope. Reduce platform breadth by supporting one bounded conventional motor-glider configuration, while retaining generic runtime boundaries.

CAD, the simulation model, the web scene, and manufacturing outputs must derive from the same canonical version and expose any modeling simplifications. Plot or animate only results supported by the actual method; do not fabricate CFD, fracture, or flight-test evidence.

Simulation PASS applies to its explicit contracts, modeled conditions, and admitted inputs. Manufacturing release requires its own evidence gates. Physical manufactured quality and real flight validation remain UNKNOWN until measured. Candidate packages may be exported with an explicit unresolved-requirement manifest; export success must not be presented as engineering release.

## D024 - Final aircraft experience follows the supplied assembly-explorer reference

**Decision (user clarification, 2026-09-08):** Use [S3-PX4 Assembly Explorer](https://s3-px4-assembly.pages.dev/) as the presentation/interaction reference for the final result, alongside actual AeroSandbox simulation visualization.

Provide a model-centered Explore / Simulate / Assemble experience using the same versioned CAD-derived parts: assembled/interior/exploded views, component details, a concise guided assembly sequence, and real simulation overlays/mission-change effects. Preserve the engineering V and Dalus MCP evidence trace. Assembly animations are explanations, and their collision/access/order verification status must remain explicit. Implement the core verification/redesign loop before final presentation polish.

## D025 - The reusable pipeline and adapters are the open-source product

**Decision (user clarification, 2026-09-08):** Future users must be able to provide their own hardware-system mission and run the same engineering V pipeline demonstrated today. Tools must be exchangeable through small explicit adapters; the reference aircraft is the first configured use case.

Keep the generic runtime separate from domain-specific engineering schemas/rules and concrete model/store/CAD/verifier adapters. The live demo must use the public pipeline entry point rather than a separate scripted trajectory. Ship the actual adapters, reference domain pack, setup/configuration instructions, reproducible checks, and extension guidance as part of the OSS repository.

Replacement tools must satisfy the selected verification contracts and preserve evidence provenance, units, applicability, and invalidation. Missing domain methods remain UNKNOWN. Reusability does not mean claiming verified support for arbitrary hardware on day one. Dalus is the reference engineering backend through MCP only; its private implementation is not part of the OSS repo.

## D026 - Publish the reference aircraft as a public interactive website

**Decision (user request, 2026-09-08):** The final aircraft example must live at an accessible public website, in addition to the public open-source repository.

Publish the model-centered Explore / Simulate / Assemble experience, engineering V trace, evidence/experiments, and CAD/manufacturing-package downloads. Use the same pipeline-generated design/artifact bundle as the working demo. The public example must be inspectable without a Dalus account, while Dalus remains the authoritative engineering backend for its generation.

The user subsequently selected a public website that can launch new Astra/solver missions. A static-only deployment does not satisfy this request. Use the same bounded pipeline behind a thin hosted Python API, with server-side credentials, isolated run/engineering records, and explicit execution/usage limits. Keep the published example inspectable while live work executes, and label recorded/precomputed results clearly. Visitors submit validated mission requests; they do not receive arbitrary Dalus MCP write access. Hosting must support the real CAD and analysis dependencies.


## D027 - Aircraft mission numbers are provisional until baselined

**Decision (user clarification, 2026-09-08):** Payload, endurance, size, and budget are flexible for now; the example numbers are not hard requirements. Choose a feasible reference mission during setup and record explicit thresholds, scenarios, and verification methods before the design experiment. Once a run baseline is frozen, Astra cannot relax it to remove failures. Subsequent user mission changes create a new baseline and invalidate dependent evidence.


## D028 - Runnable Python/React vertical slice and explicit fixture path

**Decision (implementation, 2026-09-08):** The project is rooted directly in OpenV. Use Python 3.12, Pydantic, FastAPI, build123d 0.10 and AeroSandbox 4.2, with a React/Three.js viewer. Pin ocp-gordon 0.1.17 with OpenCascade 7.8 because its newer release installs an incompatible OCP API alongside build123d 0.10. OpenV code uses MIT; dependencies and external services retain their terms.

A deterministic fixture proposer enables account-free checks with actual CAD and solvers; artifacts and UI identify it explicitly. It is not Astra acceptance. The first fixture demonstrated excessive spar deflection, an 8-to-10 mm diameter change, evidence invalidation and passing modeled deflection after rerun. Unsupported manufacturing/assembly, complete airframe and physical claims remain UNKNOWN.

## D029 - Dalus discovery and partial batch writes

**Decision (integration, 2026-09-08):** Dalus MCP OAuth is authenticated. Actual tools include listTeams, createModel, searchModel, describeOperations and writeModelChanges. Discover operation schemas before mapping engineering records. Dalus statuses are Incomplete / In Progress / Complete / Failed; OpenV maps UNKNOWN to Incomplete, stale/pending to In Progress, PASS to Complete only with admitted current evidence, and FAIL to Failed. Batches are not atomic: invalid entries are skipped while valid siblings apply. Keep an explicit commit marker incomplete until every intended operation and read-back check succeeds. Never infer verification from a successful MCP request.

## D030 - Explicit user experiments and immutable baselines

**Decision (implementation, 2026-09-08):** Website controls create a new isolated run linked to the selected parent version. Record the hypothesis and invalidation before CAD or verification. Design-only branches carry forward the exact accepted HardwareSystem and contracts; do not reconstruct a baseline from defaults, where integer/float serialization or template edits can change its identity. Numeric mission changes create an explicit baseline amendment; only the affected mission-derived thresholds may change. Preserve all other contracts and uncovered clauses. Branches conservatively recompute evidence; within-run redesign reuses only identical dependency fingerprints. Historical evidence is retained.

## D031 - Source provenance and domain-owned fabrication outputs

**Decision (implementation, 2026-09-08):** Fingerprints include a process-start engineering-source revision to cover cross-module method dependencies. Freeze each method's own source hash at registration. A run refuses packaging if its source tree changes during execution. Packages include regeneration source, dependency lock, canonical state, evidence, experiment history and a file-hash manifest. Aircraft fabrication/assembly knowledge lives in the aircraft domain, not the pipeline. A minimal bracket-domain regression exercises the same public fail/redesign/invalidate/verify/package runtime.

## D032 - Measured propeller data with bounded applicability

**Decision (implementation, 2026-09-08):** The APC prediction download returned HTTP 403. Use the publicly accessible UIUC Propeller Database volume 1, version 3 measurements for APC Thin Electric 8x4 instead. Cache source files privately; evidence records source URLs/hashes and the small airspeed-specific interpolation slice. Never extrapolate beyond measured advance ratios/RPM. Available measurements can support an exploratory shaft-power/energy calculation, but missing installed motor, battery discharge and mission-reserve evidence keeps endurance UNKNOWN. No source-fetch success establishes performance.

## D033 - One public Python host

**Decision (deployment, 2026-09-08):** Use one isolated Ubuntu host in the user's authenticated AWS account, serving FastAPI through Caddy HTTPS and systemd. This supports the native CAD/solver dependencies without introducing a second runtime, database or job framework. One admitted process, daily run quota and hard time/iteration bounds limit public execution. Credentials stay in restricted server-side files. Host resources incur ongoing charges and must be stopped/deleted when no longer needed. The website can show published runs while live credentials are unavailable, with provider labels preserved; this is not acceptance of the live Astra milestone.

## D034 - Vercel website with the existing engineering backend

**Decision (user steering, 2026-09-08):** Deploy the website on Vercel. Keep the native Python CAD/solver worker, artifacts and Dalus session on the existing host. Vercel serves the Vite build and proxies `/api/*` and `/artifacts/*` through external rewrites. Disable caching for changing run/evidence responses. This changes the website host without splitting or replacing the engineering loop. Vercel deployment credentials are separate from Astra/Dalus runtime credentials.

## D035 - Rejected model proposals remain observable engineering attempts

**Decision (live Astra integration, 2026-09-08):** The first live mission proposal violated the spar-to-tip geometry constraint and was rejected. Do not silently clamp such proposals. Permit up to three structured-proposal attempts, returning the exact validator errors and previous proposal to Astra. Retain response IDs, model/usage metadata and acceptance/rejection history even when the SDK's Pydantic parser rejects the output. Tests exercise the real OpenAI SDK parser through an offline HTTP transport. Schema acceptance remains distinct from engineering PASS; CAD and external verification still run independently.

## D036 - Durable Dalus OAuth expiry and refresh

**Decision (live integration, 2026-09-08):** Persist absolute access-token expiry alongside restricted OAuth files. MCP 1.30 reloads tokens without their expiry timestamp and goes directly to interactive authorization after a resource 401. Refresh near-expiry tokens before each short MCP session using the registered issuer's discovered token endpoint. Validate issuer/token origin, do not follow credential-bearing redirects, and preserve a refresh token when the provider omits a replacement. Metadata discovery injects load-balancer cookies; the CLI's refresh-token request must use token authentication without those browser cookies. Real refresh and subsequent authenticated MCP discovery succeeded. Interactive `login` can obtain a new grant when refresh is rejected; ordinary engineering jobs stop with UNKNOWN rather than inventing a connection.

## D037 - Closed proposal wire schema and frozen component inputs

**Decision (live integration, 2026-09-08):** OpenAI strict structured output rejected the redesign's arbitrary parameter dictionary. Use an enumerated list of parameter/value records on the API boundary, reject duplicates, and convert to the existing validated core patch. An SDK transport regression checks every object is closed and the original failure context is preserved. The interrupted run retains its actual mass/stability failures and the schema error; it is not a completed Astra repair.

CAD and regeneration now consume the frozen HardwareSystem component catalog. Updating a supplier reference must not silently change an existing branch's mass, dimensions or mounting geometry. New baselines use EMAX's GT2215 family table (70 g) and dimensional drawing (28.5 mm body, 33.5 mm length, 19/16 mm M3 mounting pattern), with source URLs and a pinned component revision. Legacy baselines keep their estimated properties. Installed variant, screw engagement and support loads still require verification.

STEP round-trip admission checks part identities, centroids, bounding dimensions and imported validity in addition to volume. Translation can preserve volume while corrupting an assembly. The regression deliberately moves a solid and verifies that it cannot support a CAD PASS.
