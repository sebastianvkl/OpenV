# Codex Handoff - Verification-First Hardware Engineering

This file is a compact single-file summary for situations where the full `docs/` directory is inconvenient. The repo documents remain the authoritative source.

## Product

Build an open-source agentic engineering V-model runtime where a user says what hardware they want to build and GPT-6 Astra carries it from requirements through design, external verification, redesign, manufacturing, and assembly outputs.

The differentiator is verification, not CAD generation.

**Astra proposes. Tools execute. Evidence decides.**

## Key rules

- Generated CAD is not verified.
- Astra never marks its own work PASS.
- Requirements are PASS / FAIL / UNKNOWN / STALE.
- Every PASS links to evidence.
- Design changes invalidate dependent evidence.
- Iterations are recorded engineering experiments.
- Prefer real component data.
- Define interfaces before independently designing subsystems.
- Manufacturing verification and functional verification are distinct.
- Assembly plans must also be checked.
- Unknowns stay unknown.

## Dalus

Dalus is the engineering system of record and digital thread for requirements, architecture, interfaces, parameters, analyses/test cases, verification state/evidence references, and traceability.

The OSS repo should provide a Dalus adapter plus a simple local fallback backend.

## First demo

Small conventional electric RC motor glider, roughly 0.9-1.1 m span, using a mixed build strategy such as PLA Aero + carbon reinforcement + COTS electronics/propulsion + metal only where appropriate.

Potential tools:

- Astra
- Dalus
- TextToCAD/build123d
- AeroSandbox
- RMFG
- Onshape (optional final handoff)
- Three.js

## Demo sequence

1. User asks for a hardware system.
2. Astra creates requirements + architecture.
3. Astra produces a plausible first design.
4. UI says DESIGN GENERATED - NOT VERIFIED.
5. External verification finds several failures.
6. User says "Make it actually work."
7. Astra proposes experiments and changes the design.
8. Verifiers re-run and requirements change status only based on evidence.
9. Dalus holds the trace from requirement to evidence.
10. Once release gates pass, generate a polished build package and interactive assembly experience.

## Final release experience

Tabs:

- Overview
- Verify
- Exploded
- Assembly
- BOM
- Manufacturing
- Files

One canonical `assembly.json` drives interactive assembly, video, and PDF instructions.

## Core implementation priority

Get this real first:

**intent -> requirements -> design -> external verification -> failure -> Astra redesign -> re-verification -> evidence-backed PASS**

Everything else is secondary until that works.
