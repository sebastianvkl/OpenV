# Project Context

## What we are building

This project is an open-source, verification-first hardware engineering pipeline.

The user experience should begin with a simple prompt such as:

> Build me a small RC aircraft that can carry a 300 g camera for at least 25 minutes, cost less than $350, and use parts I can realistically source.

The user should not need to know which motor, battery, airfoil, CAD tool, simulation method, manufacturing process, or verification method to use.

GPT-6 Astra acts as the engineering agent. It turns the request into a structured engineering V-model, proposes a design, uses external tools to evaluate the design, learns from failures, and keeps iterating until release criteria are met or the system determines that some requirements remain impossible or unverified.

The core product is not CAD generation.

The core product is **verification with traceable evidence**.

## Why this matters

Astra and other frontier models can already create impressive CAD and other engineering artifacts. The problem is that a plausible render or valid CAD file does not mean the hardware will actually work.

Common failure modes include:

- wrong component sizing
- bad center of gravity
- insufficient structural margin
- incompatible voltage/current ratings
- impossible assembly order
- inaccessible fasteners
- unrealistic tolerances
- unmanufacturable geometry
- wrong vendor footprint/model
- thermal problems
- unrealistic material assumptions
- cost or availability violations

The pipeline should therefore treat every generated design as a hypothesis that must be tested.

## Engineering V-model

The process is an executable, agentic version of the engineering V-model.

Left side:

1. user need / mission
2. system requirements
3. architecture
4. subsystem requirements
5. interfaces
6. detailed design
7. implementation artifacts

Right side:

1. component verification
2. subsystem verification
3. system verification
4. robustness testing
5. mission validation
6. physical validation when available

Every verification result should trace back to the requirement it supports.

## Role of Dalus

Dalus should be an important part of the product, while the hackathon repository remains open source.

Dalus is the engineering system of record / digital thread. It should hold or reference:

- mission / use-case structure
- requirements
- architecture and subsystems
- connections/interfaces
- engineering parameters
- component assignments
- analyses
- test cases
- verification status
- evidence references
- traceability

The open-source project should not recreate Dalus. It should contain an adapter to read/write structured engineering state into Dalus and a simplified local backend for users who do not have Dalus access.

A useful long-term framing is:

**Astra is the engineer. Dalus is the engineering memory and system model. External tools provide ground truth. The open-source harness executes the V-model.**

## First reference implementation: RC motor glider

The first end-to-end demo should use a small conventional electric RC motor glider because it gives a rich but understandable engineering trade space.

Approximate reference envelope:

- 0.9-1.1 m wingspan
- conventional wing + tail
- likely pusher motor
- 2S-3S LiPo
- 3-4 micro servos
- simple hand launch / belly landing
- Bambu PLA Aero for lightweight custom airframe parts
- carbon-fiber tube/rod for primary spar/reinforcement
- small amount of plywood or metal for high-load areas
- real purchasable motor, ESC, battery, receiver, propeller, servos, linkages, fasteners, wiring, adhesives

The aircraft is only a domain pack and demonstration. Do not hard-wire the core architecture around aircraft.

## Verification examples for the aircraft

Potential requirements and independent verification methods:

- payload capacity -> deterministic mass model
- endurance -> AeroSandbox / energy model
- stall speed -> aerodynamic model
- stability / CG -> AeroSandbox + analytical check
- motor/ESC compatibility -> electrical rules
- servo torque -> engineering calculation
- prop clearance -> geometry check
- custom-part interference -> CAD geometry check
- P1S build-volume fit -> geometry/slicer check
- printed manufacturability -> DfAM checks
- metal-part manufacturability -> RMFG
- manufacturing cost -> actual quotes + BOM prices
- assembly order -> insertion/collision/tool-access checks

The LLM should not mark these as passing.

## Manufacturing philosophy

The pipeline should choose an appropriate manufacturing process for each part rather than defaulting everything to 3D printing.

Examples:

- lightweight complex airframe -> PLA Aero on Bambu P1S
- wing spar -> purchased carbon tube
- motor / servo / battery -> COTS parts
- load-bearing bracket -> possibly aluminum, laser-cut/bent via RMFG

Manufacturing process, material, tolerances, orientation, and access constraints should influence the design before release.

## Real component data

Whenever possible, components should be grounded in real data:

- manufacturer
- exact part number
- source URL / supplier
- mass
- dimensions
- electrical/mechanical ratings
- price
- availability
- vendor CAD / STEP model

If a value is assumed or estimated, it must be marked as such.

## Interface-first design

Before delegating or independently designing subsystems, define interface contracts such as:

- mounting envelope
- bolt pattern
- mechanical datums
- connector type
- voltage/current limits
- loads
- thermal interfaces
- software/data interfaces
- allowable mass / volume

This prevents individually plausible subsystems from becoming incompatible when assembled.

## Design iterations as experiments

Every redesign should be recorded as an experiment:

- failed requirement(s)
- hypothesis
- exact parameter/component changes
- expected impact
- evidence invalidated by the change
- actual measured result
- design version / lineage

Do not simply "try again".

Example:

```text
Experiment 014
Problem: endurance target >= 25 min, current 21.3 min
Hypothesis: higher aspect ratio reduces cruise drag enough to close endurance gap
Changes: span 920 -> 1040 mm; tip chord 130 -> 115 mm
Expected: endurance up, stall speed down, structure risk up
Invalidated evidence: aero, mass, structure
Actual: endurance 25.9 PASS; stall speed 8.7 PASS; wing stress FAIL
```

The failure can still be useful. The next experiment may preserve the aerodynamic improvement and strengthen only the spar.

## Evidence invalidation

A major feature should be automatic evidence invalidation.

Example: changing the battery invalidates prior evidence for:

- total mass
- CG
- stall speed
- endurance
- structural loading
- voltage/current compatibility

An unrelated manufacturing result for an unchanged bracket may remain valid.

This is important for a credible digital thread and strongly differentiates the project from one-shot CAD generation.

## PASS / FAIL / UNKNOWN

The pipeline must explicitly support UNKNOWN.

Examples:

- aerodynamic simulation: PASS
- DFM check: PASS
- real-world flight test: UNKNOWN

If the system cannot prove a claim, it should not invent confidence.

Avoid arbitrary aggregate confidence scores unless there is a rigorous definition.

## Robustness / adversarial verification

After nominal requirements pass, Astra should try to break the design by proposing perturbations such as:

- battery capacity -15%
- payload +10%
- motor efficiency -10%
- CG shift
- higher ambient temperature
- material property variation
- component tolerances

The system should show nominal pass state separately from robustness results and known weaknesses.

## Design-for-test

Astra should be able to propose how an unverified requirement could be proven and, where useful, create verification fixtures or access features.

Examples:

- aircraft CG jig
- thrust-stand adapter
- current measurement point
- wing load-test fixture
- PCB test points / programming header
- robotic-joint calibration fixture

The system can eventually design both the product and the means to verify the product.

## Final released experience

The final output should feel like a polished product, similar in spirit to modern interactive hardware explainers and assembly viewers rather than a raw engineering dashboard.

Target tabs/modes:

- Overview
- Verify
- Exploded
- Assembly
- BOM
- Manufacturing
- Files

### Verify

Every green check is clickable and shows:

- requirement
- threshold
- result
- verification method
- tool / solver
- design version
- inputs
- assumptions
- run id
- evidence/provenance

### Exploded / Explore

Interactive 3D model with:

- assembled/exploded modes
- subsystem highlighting
- internal-component visibility
- labels
- wiring/interfaces
- component metadata
- links to requirements and verification evidence

### Assembly

Step-by-step interactive instructions using the real CAD components:

- Previous / Next / Replay
- exact parts
- fasteners
- tools
- current action
- check/inspection

The assembly plan itself must be verified for insertion paths, collisions, fastener access, tool access, and ordering dependencies.

### Single source for assembly outputs

Use one canonical structured assembly definition, e.g. `assembly.json`.

That same data should generate:

- interactive Three.js assembly guide
- assembly animation/video
- illustrated PDF assembly manual

This prevents the video, interactive guide, and PDF from contradicting each other.

## Final build package

A released design should be able to produce a package such as:

```text
/cad
  full-assembly.step
  custom-part.stl
/bom
  bom.csv
/manufacturing
  print-settings.json
  rmfg-parts/
/verification
  verification-report.pdf
/assembly
  assembly.json
  assembly.mp4
  assembly-instructions.pdf
```

## What should be memorable in the demo

The memorable moment is not the first CAD render.

The desired stage sequence is:

1. Astra creates a plausible-looking design.
2. The system says DESIGN GENERATED - NOT VERIFIED.
3. Verification reveals several real failures.
4. User says "Make it actually work."
5. Astra proposes experiments and redesigns.
6. External tools re-run.
7. Requirements become green only as evidence appears.
8. The design reaches release criteria.
9. The polished build/assembly experience is generated.

The product thesis should be obvious without a long explanation:

**Everyone can generate CAD. We prove whether the hardware actually works.**
