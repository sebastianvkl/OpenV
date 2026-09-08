# Execution Plan

Updated: 2026-09-08. **Implementation approved by the user ("Go ahead"). Target: demo and submission materials ready by 4:00 p.m. Pacific.**

## Implementation progress

- [x] Approval received; initialized project, dependencies and Git at the workspace root.
- [x] Core verdict/evidence tests pass; fixture end-to-end repair generated CAD, invalidated evidence and reverified an 8-to-10 mm spar change.
- [x] Local React/Three.js viewer built and inspected with actual CAD meshes and evidence.
- [x] Dalus OAuth and typed MCP engineering mapping work end-to-end: requirements, variables/components, delegated interfaces, test cases, evidence references, invalidation and experiments with actual effects.
- [x] Vercel website and public GitHub repository are live; a separate HTTPS Python host runs native CAD/solver jobs. Astra credentials and Dalus OAuth are provisioned.
- [x] User perturbation API and simulation controls added; longer wings expose real stability and deflection failures. Baseline preservation regression added.
- [x] Individual cut-part STEP files, stock dimensions, complete modeled-mass BOM accounting and regeneration source added to candidate packaging.
- [x] Real Astra received measured mass/stability failures and proposed a 70 mm payload shift; external re-verification changed static-margin FAIL to PASS. A later CAD rebuild hit the original ten-minute runtime limit; the interrupted run has no final package.
- [x] STEP round-trip checks cover identity, position, dimensions, validity and volume; frozen component catalogs preserve historical CAD. Twenty-nine automated tests pass.
- [x] Fresh public mission `run-38f998e18d41` completed the real Astra fail/redesign/reverify/package loop in 293 seconds; all 55 package manifest hashes verified.
- [x] Public run `run-626e87d14855` uses the updated sourced motor catalog and stronger export checks: 43 CAD parts, 1.1443 kg modeled mass, 10 PASS / 0 FAIL / 7 UNKNOWN, all 61 manifest hashes verified.
- [ ] Complete manufacturing definition remains open: hinges/linkages, fastening/joints, retention, remaining vendor selections and process details. No manufacturing or flight release is claimed.

The current 43-part sourced-catalog Astra CAD export is a candidate with explicitly listed design gaps; it is not the complete manufacturing package milestone.

## Historical pre-implementation review - 11:04 a.m. Pacific

The following records the initial state before approval; current progress is above.

The architecture is sufficiently defined to begin implementation after the user approves the baseline and access setup. The accumulated P0 deliverables remain the goal, but their breadth is not a credible guarantee of complete aircraft/manufacturing verification by 4:00 p.m. There are roughly five hours left and the workspace still contains documentation only. Do not respond to schedule pressure by weakening evidence rules or silently dropping requested outputs.

Read-only environment check: Python 3.12.2, Node/npm, and GitHub CLI are available. `OPENAI_API_KEY` is not set in the inspected shell; it may exist in another user configuration. build123d, AeroSandbox, and the MCP package are not installed in that Python environment. The Dalus endpoint advertises OAuth but no authenticated tool discovery has occurred. GitHub CLI authentication is confirmed for `sebastianvkl`; `sebastianvkl/OpenV` was not found through that account. Repository creation and hosting access remain pending. Setup is the first implementation checkpoint, not a completed prerequisite.

User answers: aircraft targets are flexible, with no hard numerical requirements yet; the public website must let visitors launch new Astra/solver missions; GitHub connection is requested and the CLI is already authenticated as `sebastianvkl`. Select a feasible provisional reference mission during setup, then freeze explicit testable thresholds before verification/redesign. Flexibility during mission definition does not permit Astra to weaken a frozen baseline after failure. Model credentials, Dalus OAuth, and backend hosting still need setup. Do not repeat settled scope questions.

Implementation choices, pending the original approval to start coding:

- One conventional motor-glider family and one baseline mission, with one selected mission-change scenario and explicitly bounded design variables. Values proposed in the handoff are not automatically accepted hard requirements.
- One React/Three.js interface, one Python runtime, one static adapter configuration, and the public reusable pipeline entry point. Dalus MCP is the live engineering backend; build123d and AeroSandbox are the initial CAD/analysis tools.
- One reviewed method per required claim category initially. Define each exact metric, threshold, scenario, admissible inputs, and limits before using it for a verdict. Claims without adequate methods remain UNKNOWN.
- One reference geometry source feeds CAD, solver inputs, web/assembly assets, and fabrication outputs. Test geometry/units/version correspondence explicitly.
- One versioned candidate package may be complete as an artifact set while its engineering-release gate is blocked. Report those two completion states separately; neither artifact completeness nor a simulation PASS establishes physically validated flight.

Build in runnable slices: setup and capability checks -> initial CAD plus independent failing analysis -> Astra experiment/invalidation/re-analysis through Dalus -> matching package -> visual mission-change/assembly experience -> public deployment/video. These are dependency checkpoints; UI layout and deployment-shell preparation can proceed independently once implementation is authorized. Do not wait until packaging to discover that the hosting account is unavailable.

Protect the final hour for deployment, verification of downloads, a real run recording, and the required one-minute video. At 2:20 p.m., stop adding methods/integrations and expose remaining coverage gaps. A missed milestone stays incomplete; the core loop, Dalus trace, CAD, actual simulation, public example, and package are not silently replaced with mocks or screenshots. Use existing rights-cleared reference data/templates where available, without claiming they were authored during the event.

Onshape is an optional STEP review/handoff today unless an existing working parametric document/automation substantially reduces work. Do not build two CAD-generation paths. Propose MIT for the OSS code unless the user chooses otherwise; record the license decision and separate third-party code/data/asset terms before publication.

## Product and today's scope

AI-generated hardware is a hypothesis. The demo must make that tangible: show a compelling design, independently discover an engineering failure, let Astra propose and apply a meaningful repair, invalidate dependent evidence, and verify again.

The user clarified that the previous plan was too infrastructure-heavy: the experience must look great, Astra should face a demanding engineering problem, and **Dalus must have a major role exclusively through MCP**. Dalus is part of the P0 live experience, not an optional P1 mirror. This plan replaces the previous local-first deadline overlay. Accepted project invariants still apply.

The user further clarified that today's deliverable is a **CAD and manufacturing package**, not a physically fabricated aircraft. Real CAD, a complete system definition, meaningful flight analysis, and visual mission/design perturbations are core scope. A schematic-only demo or a pair of component checks is insufficient. Simplify the software architecture and restrict the first aircraft family instead of removing the engineering outputs.

Build a thin reusable V-model runtime exercised by one conventional motor-glider configuration, one Astra orchestrator, one Dalus MCP adapter, one parametric CAD generator, and one aircraft analysis path with supporting deterministic checks. Aircraft rules stay in a domain module; the motor-glider demonstration must execute the same public pipeline entry point available to future users. Keep extension points small rather than constructing a large plugin platform. The deadline is ambitious; unimplemented CAD, simulation, or Dalus capabilities must be reported as incomplete rather than silently removed from acceptance.

## Open-source product: the reusable engineering pipeline

The user clarified that the enduring OSS value is a usable pipeline and its tool connections. A future user should be able to provide a new hardware mission and run the same V-model workflow built for today's demo. The aircraft package and polished viewer demonstrate that pipeline; they must not become a separate hard-coded application.

Use three simple layers:

| Layer | Reusable responsibility |
| --- | --- |
| **Core runtime** | Mission/baseline workflow, V-level allocations and contracts, proposal validation, design versions, dependency invalidation, evidence admission/evaluation, bounded experiments, gates, and artifact manifest. No aircraft-specific formulas or hard-coded part names. |
| **Domain pack** | Domain requirement/interface templates, design schema and allowable changes, applicable engineering methods, operating scenarios, component/material data, CAD mappings, and manufacturing/assembly knowledge. Aircraft is the first implemented pack. |
| **Tool adapters** | Small interfaces for the engineer, engineering store, CAD generation, analysis/geometry/manufacturing tools, and artifact outputs. Configure the concrete implementations for a run. Astra, Dalus MCP, build123d, and AeroSandbox are today's implementations. |

The core asks for declared capabilities and typed results, not vendor-specific response fields. An adapter declares its ID/version, accepted inputs/units, output metrics/artifacts, dependencies, applicability, and provenance. Keep selection in a static configuration/registry today; a plugin marketplace or dynamic discovery framework is unnecessary.

Tools are replaceable only when their outputs and method scope satisfy the verification contract. Switching a solver does not make methods scientifically equivalent: validate the replacement, record its version/assumptions, invalidate or re-evaluate affected evidence, and keep unsupported claims UNKNOWN. The model provider remains replaceable at the proposal interface, but the live hackathon profile must actually use Astra. Dalus remains the reference engineering system of record, and its adapter uses MCP exclusively; the account-free local backend is a small alternate implementation, not a recreation of Dalus.

A future mission enters the same pipeline: determine applicable domain coverage -> propose requirements/architecture/interfaces -> bind supported verification contracts -> design -> verify -> experiment/redesign -> reverify -> package with explicit gate status. If domain knowledge or a needed verifier is missing, preserve the request, produce the supported requirements/verification plan, and expose missing capabilities/UNKNOWNs. Do not silently run aircraft checks on unrelated hardware or claim arbitrary hardware is already supported.

P0 repository usefulness requires:

- A documented public entry point used by both the live demo and a normal user-supplied mission; no separate scripted repair path for the presentation.
- A small editable run configuration for domain/tool/backend selection, with credentials kept outside the repository.
- Reproducible setup/dependency information, an OSS license before publication, an example mission, and an offline path using real deterministic checks.
- Concise adapter/domain-pack documentation and a small non-aircraft dimensional-check regression through the same core, demonstrating the abstraction without building a second full domain product.
- Portable artifact manifests and source/provenance records; useful failure/missing-capability messages when services or methods are unavailable.

The core loop, concrete adapters, reference aircraft pack, verification tests, and model-driven viewer/assembly/package code are the OSS deliverable. External proprietary services remain external. Do not depend on private Dalus implementation code or undisclosed local scripts for the public quickstart.

## Governing workflow: the engineering V

Per D003 and the user's latest clarification, the application executes the engineering V. Define the intended evidence on the left side as each engineering claim is created; execute the corresponding checks on the right. The Generate / Verify / Repair / Export actions operate within this model.

| Definition and decomposition | Corresponding evidence |
| --- | --- |
| Mission, intended use, and operating conditions | Mission validation against intended-use scenarios; simulated and physical validation remain explicitly distinct. |
| System requirements | System verification: aircraft performance, mass, energy, and other required whole-system checks. |
| Architecture, subsystem allocations, and interfaces | Subsystem/integration verification: propulsion/power/control compatibility, load paths, fit, and interactions. |
| Detailed parts, components, materials, and CAD | Component/part verification: ratings, geometry, dimensions, local loads, and manufacturing constraints. |

At the bottom of the V, canonical detailed design produces the CAD, analysis model, component assignments, and fabrication/assembly definitions. For today's digital package, these are implementation artifacts; physically manufactured hardware is not implied.

Each requirement is allocated to an engineering element and linked through Dalus MCP to a reviewed verification contract, scenario, and evidence references. Create this pairing during decomposition, before detailed design. An unsupported claim retains its planned verification method and UNKNOWN status. Passing all component checks does not automatically prove a subsystem, system, or mission: the corresponding integration/system/validation evidence is still required.

Iteration happens at the appropriate level. A component interference failure sends Astra back to part/layout design; a propulsion integration failure sends it back to interface/component choices; a mission-performance failure can require architecture or sizing changes. Record the experiment, propagate invalidation through affected definitions, CAD/analysis artifacts, and evidence, then rerun the corresponding right-side checks. Astra cannot revise requirements to eliminate a failure.

A user mission change creates a new baseline and propagates through the left-side allocations and their corresponding evidence dependencies. Independent results remain reusable only under the existing fingerprint rules. Keep nominal and alternative scenarios separate.

Show a compact V-shaped progress/trace view beside the aircraft, with selectable linked requirement/check nodes and PASS / FAIL / UNKNOWN. The visible story is decomposition -> digital implementation -> verification -> evidence-driven return to design -> re-verification -> gated package. Keep one orchestrator and the existing small service structure; a V-model does not require a multi-agent graph or separate service per stage.

## Required end artifacts

- Full aircraft assembly STEP and editable parametric source/state, plus individual fabrication files (STL for printed parts; other formats only where actually needed).
- A system BOM covering custom airframe parts and purchased propulsion, power, control, structural, wiring, and fastening items; exact source identities where available and explicit unresolved selections.
- Fabrication notes: process/material, part segmentation, critical dimensions/tolerances, purchased-stock cut lengths, and print assumptions/settings where applicable.
- A concise assembly sequence from the same part identities, with the status of fit, interference, access, and sequence checks exposed. An unchecked sequence is not verified assembly.
- Simulation inputs/results, operating envelope, verification evidence, versioned experiments, and Dalus trace references.
- A package manifest tying every artifact to the same design/baseline and listing passed, failed, and unknown requirements and release-gate status.

The goal is a complete package for a bounded reference aircraft. Missing structural members, hinges/linkages, electronics mounts, fasteners, or wiring cannot be hidden behind a visually complete outer surface. Exporting a candidate package is allowed with visible failures/unknowns; claiming manufacturing release requires its mandatory checks to pass. Actual fabricated quality and flight performance remain unmeasured today. State the flight-analysis claim as passing specific modeled conditions only when the required analyses actually pass.

## Four responsibilities

| Part | Responsibility |
| --- | --- |
| Astra | Decompose the mission, propose architecture/interfaces and a design, interpret actual failure evidence, propose engineering experiments and specific changes. |
| Dalus through MCP | Authoritative requirements, architecture, interfaces, parameters/component assignments, verification methods, evidence references, experiments, and traceability, using the capabilities actually exposed by the server. |
| Trusted engineering tools/runtime | Generate CAD from canonical state; run aircraft analyses and reviewed structural/electrical/geometry/manufacturing checks; admit evidence and determine PASS / FAIL / UNKNOWN. CAD generation success alone is not verification. |
| Polished web experience | Render the actual CAD-derived model, operating conditions and simulation outputs; show failures, engineering changes, before/after results, evidence/Dalus trace, and package downloads. |

Proposed small implementation: React/Three.js for the experience; a thin Python service for Astra, MCP, build123d, AeroSandbox, and deterministic checks; local JSON artifacts/cache. Use a minimal JSON fixture backend for offline development and the account-free fallback required by `AGENTS.md`. Do not build a local engineering database/editor or generic synchronization system. Live acceptance requires the real Dalus MCP path.

Canonical engineering state drives both build123d geometry and the AeroSandbox analysis model. The web scene loads CAD-derived meshes; analysis overlays reference that same design/scenario. Verify that wing/tail geometry, component positions, reference frames, units, masses, and artifact hashes agree across these representations. Label any simplified vendor envelopes. Do not verify one idealized aircraft and export a materially different one.

build123d documents [STEP, STL, and glTF exports](https://build123d.readthedocs.io/en/stable/import_export.html). AeroSandbox's [AeroBuildup](https://aerosandbox.readthedocs.io/en/develop/autoapi/aerosandbox/aerodynamics/aero_3D/aero_buildup/index.html) documents aerodynamic and stability-derivative analysis. These are candidate implementation capabilities, not proof that our aircraft or integration works. Validate the installed methods on known cases before accepting evidence.

## Demo story

1. Enter the motor-glider mission and show requirements and interfaces being created in Dalus through MCP.
2. Generate real parametric CAD for the reference aircraft and display its assembly/components. Label it generated/unverified.
3. Run the aircraft simulation and independent supporting checks; show the modeled conditions and an actual failed constraint, with its number and threshold.
4. Astra receives the failed checks, exact inputs, current design, interfaces, and evidence references. It proposes an experiment with a hypothesis, exact changes, and expected tradeoffs.
5. Apply the change to a new design version through MCP. Show the affected evidence becoming stale before rerunning.
6. Regenerate affected CAD and analysis inputs, rerun the affected checks, and show the changed aircraft and actual simulation results alongside explicit UNKNOWNs.
7. Change payload, mission target, or a supported operating condition; immediately invalidate affected results and show what requirements fail when recomputed. Astra can propose another engineering experiment.
8. Open the requirement -> experiment/design -> evidence trace in Dalus, then download the matching CAD/manufacturing/evidence package.

One controlled mission/design-change demonstration is P0. Record user mission amendments as new baselines; scenario sweeps and candidate previews must not overwrite the nominal design's evidence. Astra must never weaken the baseline itself.

## Engineering challenge

Restrict the first configuration to a conventional wing/tail electric glider and a small component/material catalog. Give Astra meaningful variables such as span/chord, tail sizing, battery/payload placement, and component/spar selection within declared bounds. A geometry change must carry its mass, structural, manufacturing, and fit consequences.

Required verification categories for the requested aircraft package:

- **Mass/CG and aerodynamics:** calculate installed mass properties, lift/drag/trim and longitudinal stability metrics over a small declared operating envelope. A guessed CG interval or successful solver call is insufficient for a stability PASS. Full dynamic controllability is a separate claim.
- **Propulsion and mission energy:** compare required performance with sourced motor/prop/battery capabilities under documented conditions. Missing propulsion/efficiency data keeps endurance and thrust claims UNKNOWN; the fixed 35-W calculation cannot substitute for flight analysis.
- **Structural load path:** independently evaluate a simple spar/beam model with actual geometry and declared material/load cases. Simplifications, joint adequacy, printed anisotropy, and unmodeled failure modes remain visible. Do not imply full-airframe FEA or fracture prediction.
- **Electrical and fit:** evaluate voltage/current constraints where data supports them, actual custom-part interference and declared component envelopes, clearances, and mounting consistency.
- **Manufacturing and assembly:** check generated geometry validity, print-volume/part segmentation, relevant thicknesses and mating dimensions, and the specific assembly constraints implemented. Successful STEP/STL export is not a manufacturing PASS.

Build the smallest validated method in each necessary category and record any uncovered claims explicitly. The complete system goal does not authorize guessed green statuses. At least two independent methods and a real failure-driven repair are necessary, but no longer sufficient by themselves to declare the requested package complete.

## Simulation visualization and what-if interaction

Use one visual simulation workspace with the actual CAD-derived aircraft and selectable run/scenario. Controls initially cover payload/placement, airspeed, and supported atmospheric/mission settings. Show CG/neutral-point references where justified, computed force/moment vectors, performance margins, and critical spar load/deflection results where the analysis supports them. Plot operating-envelope boundaries against the requirements, and highlight the affected physical parts.

Only render pressure/load distributions or flow fields if the selected method actually produces suitable data. Do not dress a lift/drag calculation in fabricated CFD or crash animation. Highlighting a failed structural requirement shows an exceeded modeled limit, not an independently simulated fracture.

On a design/mission change, show STALE/pending immediately, rerun, then display the new evidence. Cached/interpolated previews must be labeled and cannot create PASS unless a contract explicitly admits them. Every overlay and plotted point retains design/scenario/run IDs. Keep the previous result available for before/after comparison without displaying it as current.

## Final experience reference: S3-PX4 assembly explorer

The user supplied [S3-PX4 Assembly Explorer](https://s3-px4-assembly.pages.dev/) as the desired final presentation, in addition to AeroSandbox simulation visualizations. The reference was inspected in the browser: warm off-white background, dark green typography/controls, a large central model, assembled/inside/exploded modes, explode-distance slider, component/wiring labels, camera presets, and a Play assembly walkthrough with previous/next/replay/progress controls. Its page distinguishes project geometry from concept parts. Treat it as an interaction and visual reference for our own aircraft data/assets.

Use one CAD-derived scene with three views:

- **Explore:** assembled/interior/exploded states, smooth explode control, selective part labels and visibility, camera presets, and component selection showing its BOM/interface/evidence/Dalus references.
- **Simulate:** the same aircraft with the previously specified real AeroSandbox/calculation overlays, operating-condition controls, mission changes, failure highlights, before/after comparison, and Astra repair action.
- **Assemble:** a concise guided sequence using the actual versioned parts and one canonical assembly definition, with play/pause/previous/next/replay, parts/tools/fasteners, and explicit check/inspection status.

Keep the engineering V visible as a compact progress/trace affordance; evidence detail and package downloads are available without turning the main view into a dense dashboard. The same selected design/scenario/version must follow across views. Assembly motion comes from the shared assembly definition; simulation overlays come from actual run outputs. A plausible assembly animation cannot close collision/access/order requirements without the corresponding checks.

Implement the basic Explore and short Assemble interactions after the CAD/simulation/redesign loop works, as part of the final P0 experience. Reuse meshes, part IDs, and view controls across all modes rather than building three separate applications. Rich cinematic animation, video rendering, and PDF polish remain later work.

## Public example website

The user explicitly requested a public website where the reference aircraft example lives. A deployed, accessible URL is a P0 deliverable, alongside the public OSS repository and downloadable manufacturing package. Publishing this intended public example is authorized by that request; implementation still awaits the earlier architecture-approval boundary.

Publish the same Explore / Simulate / Assemble interface, with the engineering V, actual experiment history, inspectable evidence, known unknowns, CAD/BOM/manufacturing downloads, and links to the OSS repository and applicable Dalus trace. The site must be usable without a Dalus account to inspect the published example. Dalus links may require login; public evidence needs its own accessible published artifacts rather than broken private-only links.

The user selected live public mission execution. Serve the web interface and a thin Python API from a deployable backend that can run Astra, Dalus MCP, build123d, and AeroSandbox. Visitors can submit a supported mission and inspect its actual requirements, design, verification, redesign, and resulting package. Use the same pipeline entry point as the OSS app. Keep a published real reference run available while jobs execute; label recorded results clearly. A static-only example is no longer sufficient.

Use the same viewer and artifact manifest for public captured runs and live connected runs. A public snapshot remains evidence for its named design/version/scenario and does not become an independent editable engineering system of record. Keep model/MCP credentials on the server. Mediate every visitor action through the runtime and preserve immutable artifacts for each run. Per D043, serialize engineering updates into one persistent Dalus model for the aircraft; earlier website snapshots remain historical. Do not expose arbitrary MCP operations. Start with one active engineering job, bounded proposal/solver iterations and execution time, and configurable request/usage caps; display busy, stopped, and failed states explicitly. Use a simple in-process runner with durable run artifacts for today; interrupted jobs must be marked interrupted and never appear verified. Publish only the intended example data/assets; retain credentials and unrelated private data outside the build.

Choose a host capable of running the Python CAD/solver dependencies and serving the interface, based on available deployment access; use its default HTTPS domain for the hackathon. Prefer one service/container today. GitHub supplies source hosting; it does not by itself provision the live Python execution service. Deploy the shell early enough to validate access, replace it with the actual generated example before completion, and verify the final result from an unauthenticated browser.

Acceptance: a visitor can submit a fresh supported mission, receive a distinct run, observe actual Astra/solver execution and evidence-backed results, and download its matching package; the public URL also loads the reference model, the three modes work, recorded/live labels are accurate, evidence and package downloads are accessible, the GitHub/setup links work, and all assets refer to the same published design version. A localhost URL or a landing page without the aircraft example does not satisfy this deliverable.

## Dalus MCP is a P0 dependency

The user supplied the MCP endpoint: [https://app.dalus.io/api/mcp](https://app.dalus.io/api/mcp). A read-only probe reached it and received HTTP 401 with an OAuth Bearer challenge. Its protected-resource and authorization-server metadata advertise `mcp:read`/`mcp:write`, authorization-code flow with S256 PKCE, refresh tokens, and a client-registration endpoint. No authenticated connection, tool schema, or engineering records have been accessed yet. No Dalus tools are currently exposed directly in this Codex session. The next connection step is an authenticated MCP client session and actual tool discovery. Do not invent tool methods or substitute direct engineering REST/database access. OAuth discovery/sign-in endpoints support MCP authentication; they are not an alternate engineering integration.

First integration checkpoint: connect using the real MCP configuration, inspect available tools, and demonstrate a small requirement/parameter/evidence-reference round trip. Map to existing Dalus entities rather than extending or recreating its internal model. Record unsupported operations explicitly and resolve them against actual server capabilities.

MCP is a transport, not a verification authority. Do not hand Astra unrestricted generic Dalus writes. The runtime mediates model proposals, validates allowed fields/references, applies accepted engineering writes through MCP, and alone writes verifier evidence references and derived verdicts. A model-supplied status or claimed measurement is never authoritative.

Local artifacts hold raw outputs, fingerprints, and captured runs; Dalus owns the engineering record and their references. Cache state is labeled and not independently editable. Idempotent writes and a simple completion marker must keep partial remote updates from looking verified. An unavailable Dalus connection means the live Dalus milestone is incomplete; offline fixture progress can continue but cannot be presented as a working Dalus integration.

## Minimal canonical records

All records need stable IDs, pinned revisions, project/Dalus references, and provenance. Keep the implementation compact; do not build a generalized graph model.

| Record | Required content |
| --- | --- |
| Hardware system | Original mission/clauses, architecture hierarchy, domain version, baseline, current design, explicit gate policy. |
| Requirement | Statement, mission trace, owner, scope, mandatory membership, revision, required verification contracts. |
| Component | Exact identity/revision, properties with units and per-property sources; assignment includes quantity and position/frame. |
| Interface | Endpoint ports/elements, type, limits, units/datums, related requirements/contracts. |
| Design version | Immutable parameter/component/interface snapshot, parent, baseline, exact patch, content hash, experiment reference. |
| Verification contract | Metric, operator, threshold/unit/tolerance, reviewed method/version, scenario, complete dependencies, accepted provenance/assumptions, applicability and required artifacts. |
| Evidence | Source design/run/contract, exact inputs, sources/assumptions, tool/version, raw output and metrics, artifact hash/reference, dependency fingerprint, timestamp. |
| Engineering experiment | Problem/failure evidence, hypothesis, exact change, expected effects, invalidations, actual before/after evidence and deltas, regressions, disposition. |

Separate tool-run execution state from requirement evaluation. Requirements use PASS / FAIL / UNKNOWN. Evidence applicability is CURRENT / STALE; stale dependent results display UNKNOWN / NEEDS RE-VERIFY. Every PASS links to current admissible evidence.

Values retain units and quality (`sourced`, `measured`, `computed`, `assumed`, `estimated`). Missing never means zero; reject nonfinite/nonphysical inputs. Source records identify the document/property, retrieval revision/date, and exact component variant. Do not let Astra edit source facts to make a check pass.

## Verification rules that cannot be cut

- Freeze requirements, thresholds, scenarios, admissible methods/assumptions, and gate membership before redesign. New user requirements produce a recorded baseline amendment.
- Validate inputs, units, applicability, provenance, tool diagnostics, raw artifacts, and fingerprints before comparisons. Tool success by itself cannot yield PASS.
- Missing or inadequate evidence yields UNKNOWN. An admissible current counterexample yields FAIL. All required contracts must pass to close a requirement; empty sets cannot pass. Surface conflicting evidence instead of selecting the favorable result.
- Model proposals cannot author verdicts/evidence, rewrite methods, delete mandatory requirements, or adjust protected assumptions/source data.
- A design change immediately invalidates its dependent evaluations. Preserve historical evidence; do not delete or overwrite old runs.
- Separate completion of the demonstrated checks from build/flight release. Missing mandatory functional, manufacturing, assembly, and physical evidence blocks the corresponding release gate.

Use an explicit dependency map and fingerprints, not a general symbolic engine. A battery-position change invalidates CG and fit results; a battery replacement also affects mass, voltage compatibility, and other registered consumers. Include transitive derived values and source/method/scenario revisions. Reuse an unrelated result only if its full input/method fingerprint matches, retaining its original run/version reference.

Locally publish a candidate only with dependent applicability invalidated. In Dalus, use supported revision controls/completion markers so partial updates cannot satisfy a gate. Late results stay associated with their originating design and cannot make a newer design green without the same applicability checks.

## Implementation sequence and time budget

Approval was received. These original checkpoints target September 8, Pacific time; they are not completed features or guaranteed timings.

| By | Working result |
| --- | --- |
| 11:20 a.m. | Dalus MCP round trip, one bounded airframe family, canonical geometry/mission mapping, and smoke checks for CAD export and the chosen aircraft solver. Missing access/dependencies remain explicit blockers while independent work continues. |
| 12:20 p.m. | First aircraft CAD/mesh export plus a real analysis run; mass/CG and initial geometry/electrical checks; known bad case and evidence/Dalus references. |
| 1:20 p.m. | Real Astra failure-driven repair with invalidation, regenerated CAD, re-analysis, and a version-consistent candidate package. |
| 2:20 p.m. | Flight-analysis overlays, a mission/design-change scenario, and fabrication/BOM/assembly outputs with completed-check and unknown coverage visible. Stop adding integrations. |
| 3:00 p.m. | Inspect CAD completeness and export round trip; validate critical analysis/geometry cases and artifact consistency; rehearse with actual evidence. Freeze features. |
| 4:00 p.m. | CAD/manufacturing/evidence package and one-minute video/repository/demo materials ready, with accurate gate status and outstanding requirements. |

The supplied event guide sets submission at 5:30 p.m.; retain that interval as contingency. It requires an accessible demo link, a public isolated repository, and a one-minute video identifying what was built during the event. Existing Dalus and third-party tools must be distinguished from today's new work. Public publication/submission follows applicable user authorization.

## P0 - Must ship today

- [x] Approve this reduced implementation scope; record further accepted choices in `DECISIONS.md` as needed.
- [x] Implement one reusable pipeline entry point with small typed domain/tool interfaces; run the aircraft demo through that same entry point and keep aircraft assumptions out of the core.
- [x] Connect to Dalus exclusively through MCP and verify supported read/write/evidence-reference capabilities.
- [x] Implement the small canonical snapshot, frozen contracts, and tiny sourced component/reference set with explicit unknowns.
- [x] Generate the current 43-part parametric aircraft CAD assembly and fabrication exports; retain editable state/source and verify round-trip geometry/units/part identity.
- [ ] Finish the complete manufacturing definition: resolve the explicitly listed missing installation/joint/control details and verify them. The current package remains a candidate; this part of the original P0 milestone is not complete.
- [x] Integrate a validated AeroSandbox flight-analysis path and independent supporting calculations/checks; implement deterministic evaluations and provenance. Cover or explicitly leave open all required verification categories.
- [x] Implement versioned patches, transitive invalidation, experiment history, and re-verification.
- [x] Connect real Astra mission/design/redesign proposals; mediate all writes and feed actual evidence back.
- [x] Bound iterations/retries/timeouts; retain honest FAIL/UNKNOWN and stop reasons when unresolved.
- [x] Build a polished CAD-model-centered mission -> simulate -> fail -> repair experience with actual result overlays and evidence/Dalus trace.
- [x] Add the reference-inspired Explore/Simulate/Assemble views on the same CAD scene: assembled/interior/exploded interaction, selectable components, and a short guided assembly sequence with explicit verification status.
- [x] Deploy the public website and live Python pipeline backend; verify a fresh visitor mission end-to-end, run isolation, bounded execution, reference example access, evidence/package downloads, accurate live/recorded labels, and absence of credentials in public assets.
- [x] Demonstrate one mission/design perturbation, immediate invalidation, recomputed failures, and Astra's response without mixing nominal and candidate evidence.
- [x] Export the system BOM, fabrication details, concise assembly sequence/check status, and evidence manifest tied to the same design as the CAD.
- [x] Test good/bad cases, missing/invalid evidence, protected thresholds/status writes, transitive invalidation, and old/partial-result exclusion.
- [x] Record one real successful repair trajectory, label all fixtures/replays, and prepare the one-minute submission video and repository materials. The captioned 59.9-second recording and submission copy are included.
- [x] Document setup, tool/backend configuration, adding a domain/verifier, known capability limits, and an offline reproducible example; prove the core with a minimal non-aircraft regression.

A fixture proposer cannot satisfy real Astra acceptance. A mocked/local backend cannot satisfy Dalus MCP acceptance. A schematic mesh cannot satisfy CAD/manufacturing acceptance; a few component checks cannot satisfy aircraft simulation acceptance. If a required path is incomplete, report it without substituting a weaker claim. Real recorded runs are a labeled fallback where available.

## P1 - Only if P0 is stable before feature freeze

- Additional mission/environment scenarios and independent solver cross-checks beyond the required P0 demonstration.
- More complete assembly collision/access verification, manufacturing checks, and sourced component data to close remaining package requirements.
- Small extra visual refinements or sourced component choices that improve the existing demo.

## P2 - After the hackathon

Plugin marketplaces/dynamic discovery and rich backend features; additional full domain packs; broad sourcing across domains; TextToCAD as a second CAD proposal path; expanded numerical solvers; Onshape/RMFG; broad robustness campaigns; detailed assembly animation/PDF polish; richer collaboration/branching; physical fabrication and bench/flight validation. The thin reusable core, replaceable adapter contracts, useful OSS quickstart, full-reference-system CAD, system BOM, manufacturing-package outputs, and aircraft simulation remain P0.

## One-minute video

0-10 s: mission, Dalus requirements, generated aircraft CAD.

10-22 s: change payload/mission, run simulation, highlight the actual failing metric on the model.

22-42 s: Astra experiment, visible engineering change, dependent evidence goes stale.

42-55 s: regenerated CAD and simulation, before/after result, one evidence record and Dalus trace.

55-60 s: download the matching CAD/manufacturing package and show its verification scope/unknowns. Clearly identify today's new work; no blanket physical flight-ready claim.

## Approval boundary

The user approved implementation with "Go ahead". Proceed through P0 autonomously, preserving verification invariants and recording completed work and limitations.

### User-requested visual realism and simulation environments

- [x] Improve actual CAD presentation with material-specific shading, studio light, internal callouts and clearly labeled connection concepts.
- [x] Add airflow, structural-load and flight scenes with explicit model scope.
- [x] Generate version-bound AeroSandbox VLM streamlines and normal panel loads; expose model disagreement without granting PASS.
- [x] Add speed, atmospheric altitude and structural-load presets through existing mission amendment / Dalus / verification pipeline.
- [x] Test atmosphere sensitivity, trim provenance, output integrity, finite panel residuals and strict operating-case comparison (31 regression tests covered).
- [x] Publish cruise, slow-flight, 2,000 m altitude and 4 g load cases; verify all 252 package hashes, matching Dalus commits and deployed desktop/mobile switching.

### Animated 3D flight world

- [x] Add procedural valley/coast/ridge scenery, airfield, trees, water and distant hills around the real CAD aircraft.
- [x] Add prescribed-route animation, chase/wing/survey cameras, play/pause, restart and playback rate; keep physical flight UNKNOWN.
- [x] Verify moving frames, identical paused frames, failure-preserving case switching, camera/scenery selection, reduced-motion startup and mobile layout; publish the updated website.

### Clickable component specifications and sourcing

- [x] Display frozen component specs, manufacturer, part number, provenance and recorded source links when clicking CAD parts.
- [x] Link exact selected motor, battery and ESC to their product storefronts; preserve UNKNOWN selection for unresolved purchased parts.
- [x] Add an accessible selector for hidden parts, pause viewer motion during inspection, and expose custom-part stock details and version-matched CAD downloads.
- [x] Check actual mesh selection, sourced specs, pending parts, CAD download responses, flight pause and desktop/mobile layout with browser automation; production build succeeds.

### Two-hour extension — one build candidate (user approved)

Focus on the existing motor-glider rather than another domain or integration.

1. Select the remaining servo, receiver and propeller from primary manufacturer data; freeze the new catalog and installation interfaces in a new baseline. Preserve every historical run.
2. Add independent installed-component interference, continuous propeller swept-envelope clearance, straight-line insertion-envelope, BEC-voltage and channel-allocation checks. Add bad geometry/electrical and invalidation regressions before publishing new verdicts.
3. Generate component mounts/retention features, explicit installation positions, connection schedule and assembly dependencies from the same state. Keep unproven joints, controls, processes and physical performance UNKNOWN.
4. Run a new real Astra/Dalus build with these checks; expose actual failure locations, evidence and repairs in the viewer and package. Keep the deployed site runnable between milestones.
5. Use remaining time for solver-driven flight response and a stronger visible before/after engineering story, after the installation vertical slice is working. A prescribed animation never closes flight verification.

Extension checkpoint: 37 regression tests pass, including overlap versus contact, hollow-solid intersection, continuous insertion obstruction, voltage/source gaps, exact tube sections/cut lengths and evidence invalidation. Local fixture `installation-offline-002` exercised two real CAD/solver repair iterations (placement and tube section), reaching 16 PASS / 0 FAIL / 6 UNKNOWN. All 68 package hashes matched. This is a fixture acceptance check, not the new real Astra acceptance. Desktop/mobile Fit & access, sourced links and assembly tools/hardware were checked in the browser.


### Persistent Dalus system (user steering)

- [x] Update the existing model and stable engineering element IDs across runs; preserve prior test runs and snapshots.
- [x] Invalidate current statuses before updating inputs; reject missing mappings and concurrent writers; paginate MCP read-back and retry bounded consistency delays.
- [x] Regression-test repeated updates, identity/history retention, invalidation order, mapping loss and writer exclusion.
- [x] Migrate the deployed reference mapping and verify a live update uses the same model ID: run-dcef3705d89d reused 99ee8003-6171-47ce-903d-ad279e1b8f25 and reached CAD generation after strict MCP read-back.

Flight response checkpoint: four regression tests cover level-flight/ballistic references, power-loss descent, crosswind advection, terminal model bounds and real geometry provenance. Viewer integration and live acceptance are in progress.

Live installation acceptance: `run-dcef3705d89d` used actual Astra and the existing Dalus model. First CAD found 10.45 mm³ battery intersection with each tail-servo mount and 130.625 mm³ insertion obstruction at each mount. Astra changed battery x from 0.4116 m to 0.408 m; seven evidence records became stale. Re-verification reached 16 PASS / 0 FAIL / 8 UNKNOWN. The model retained 64 test-history rows, and all 68 candidate-package hashes matched. The 45-part candidate has modeled mass 1.149381 kg and 6.805 mm rigid propeller-envelope clearance; full manufacturing and physical flight release remain open.

Animated-response browser acceptance: power-off playback shows computed height/airspeed and zero commanded thrust after 5 s; banking/crosswind switch correctly, pause freezes telemetry, source output downloads, and desktop/mobile layouts have no overflow or JavaScript errors. The duplicate local fixture was explicitly stopped during its third CAD build after validating the earlier trajectory artifacts; it is marked INTERRUPTED/UNKNOWN, not a completed run. Final response/package acceptance uses a fresh verification of the repaired live aircraft. A regression also ensures the public Dalus commit indicator returns to defined/pending during redesign rather than retaining the previous evaluated marker.

Final deployed acceptance: `run-365c68904f40` reverified the unchanged Astra-repaired candidate and generated four COMPUTED point-mass responses. It reused every existing part, design-variable, requirement and test-case ID in the same Dalus model; all previous test runs remained, with 88 history rows after completion. Results remain 16 PASS / 0 FAIL / 8 UNKNOWN, with all 70 package hashes verified. At 25 s the diagnostic height changes are 0 m in trim hold, −16.62 m after power-off at 5 s, −3.46 m under the prescribed bank and 0 m under uniform crosswind advection. These are model predictions, not physical flight evidence. The complete regression suite passes 45 tests.


### Browser STEP assembly viewer (user request)

- [x] Read the selected design's actual assembly STEP in a browser worker; preserve hierarchy identities, meters and frozen component metadata. Keep loading/error previews explicit.
- [x] Add Assemble → STEP CAD alongside Assembly guide, with CAD edges, isolation, exploded view, section cuts and matching assembly download.
- [x] Add manufacturer reference photos for the selected motor, propeller, receiver and servo. Disclose purchased envelopes and missing vendor internals; no invented detailed vendor CAD.
- [x] Unit-check hierarchy identity, duplicate/missing parts, wrong placement/units, nonfinite coordinates and malformed faces (four tests). Local browser acceptance imported all 45 parts, exercised specification links, isolation, custom part downloads, section cuts, guide navigation, cached revisits and mobile layout without JavaScript errors.
- [x] Verify final Vercel deployment, version switching and existing flight playback. Production run `run-365c68904f40` loaded 45 parts / 2,320 CAD faces from its 11.7 MB STEP in 52.4 seconds. Browser checks passed for explosion, selection/specs, isolation, section cuts, guide navigation, cached return and mobile layout with no JavaScript errors. Local multi-version switching/cancellation and the existing computed-flight regression also passed.

First local browser import took 48.6 seconds for the 11.6 MB fixture; cached revisits avoid parsing. Browser tessellation is presentation only and leaves requirements, Dalus and package evidence unchanged.


### Continued assembly inspection

- [x] Search the assembly by part/manufacturer, hide individual parts, frame selection, reset the view and display mesh-derived XYZ bounds. Keep dimensions explicitly separate from tolerances/clearance verification.
- [x] Persist two parsed STEP displays in browser storage, keyed by source SHA-256 and reader settings. Re-download/hash the STEP before persistent reuse; keep import admission checks and bypass the cache on explicit retry.
- [x] Five viewer unit checks pass. Local browser acceptance exercised part visibility/reset, close-up/top views, XYZ labels, cached reload, blocked source, changed source, cancellation and mobile layout, with no JavaScript errors or engineering writes. First import took 48.6 s; cached reload took 2.0 s.
- [x] Recheck primary manufacturer resources for exact purchased-part CAD; retain labeled envelopes because no trustworthy exact STEP download was established.
- [x] Published commit `65faecf` on Vercel and verified the live 45-part candidate. Production browser acceptance passed all inspection/cache/source-failure/mobile checks with no JavaScript errors or engineering writes. Cold import took 53.9 s; hash-checked cached reload took 5.0 s.


### Submission recording plan

- [x] Replace the aspirational demo script with a timed one-minute shot list and a 120-word voiceover, using the actual Astra battery-repair run and the later unchanged-candidate flight/STEP example.
- [x] Identify today's OpenV contributions, preserve recorded-run labeling and UNKNOWN scope, provide preloaded-tab setup, submission copy and the earlier-video fallback.
- [ ] Record/edit the new submission video, check duration/audio/links, and submit through the event form. The recording plan does not mean a new video has been created or submitted.
