# Project Instructions

This repository is an open-source, verification-first hardware engineering pipeline built for the GPT-6 Astra hackathon.

Before making architectural changes, read:

- `docs/PROJECT_CONTEXT.md`
- `docs/VERIFICATION_PHILOSOPHY.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/DEMO_PLAN.md`
- `docs/EXECUTION_PLAN.md`

## Core thesis

AI-generated CAD is a hypothesis, not proof.

Astra may propose requirements, architectures, components, CAD, analyses, and redesigns, but the model must never decide that its own design passes verification.

The core rule is:

**Astra proposes. Tools execute. Evidence decides.**

## Product goal

A user should be able to say:

> I want to build [hardware system].

The pipeline should be able to produce:

1. structured requirements
2. system architecture
3. subsystem and interface definitions
4. real components and a BOM
5. custom CAD
6. engineering verification
7. autonomous redesign when verification fails
8. robustness testing
9. manufacturing verification
10. assembly verification
11. a released build package
12. an interactive 3D build/assembly experience
13. an illustrated PDF manual
14. an assembly animation/video

The first reference implementation is a small electric RC motor glider, but the core architecture must stay generic enough for robotics, electronics, mechanisms, vehicles, test rigs, and other hardware.

## Dalus

Dalus is a critical external integration and the engineering system of record.

Use Dalus for the structured engineering model, including:

- requirements
- architecture and parts
- interfaces/connections
- parameters and variables
- analyses and test cases
- verification status/evidence references
- traceability

Do not recreate Dalus inside this open-source repository.

The repository should contain an open-source Dalus adapter and a simplified local backend so the project can still run without a Dalus account.

## Verification invariants

These are non-negotiable:

1. The LLM never decides PASS.
2. A successful tool call is not evidence by itself.
3. Requirements use PASS / FAIL / UNKNOWN semantics.
4. Every PASS must point to concrete evidence.
5. Design changes invalidate affected evidence automatically.
6. Real component data is preferred over model-invented physical data.
7. Interfaces are defined before subsystem delegation.
8. CAD is an output of canonical engineering state, not the canonical state itself.
9. Assembly plans must be checked, not merely generated.
10. Release requires explicit verification gates.
11. Unknowns must remain UNKNOWN instead of being guessed away.
12. Every design iteration should be recorded as an experiment with a hypothesis and measured outcome.

## Harness guidance

Prefer a thin, explicit orchestration loop over a large multi-agent graph.

Start with one strong Astra orchestrator. Add specialist agents only when they clearly reduce complexity.

Persistent engineering state lives outside model context. Give the model only the relevant current state, failed requirements, evidence, interfaces, and recent experiment summary.

Keep the tool surface small and semantic.

## Current tool direction

Likely integrations:

- GPT-6 Astra via OpenAI Responses API / Agents SDK
- Dalus
- TextToCAD / build123d for parametric CAD
- AeroSandbox for the aircraft reference implementation
- Onshape as an optional professional CAD handoff / editable assembly
- RMFG as a manufacturing-verification backend
- Three.js / react-three-fiber for the final interactive release experience

Do not add every integration before the core verification loop works.

## Demo priority

The hackathon demo must first prove:

**user intent -> requirements -> design -> external verification -> failures -> Astra redesign -> re-verification -> evidence-backed PASS**

CAD polish, sourcing, RMFG, Onshape, assembly animation, PDF generation, and extra integrations come after that core loop works end-to-end.

## Coding behavior

- Keep domain-specific aircraft logic behind a domain-pack boundary.
- Add tests for verifiers before polishing UI.
- Include intentionally bad designs in regression tests.
- Prefer deterministic code for comparisons and gates.
- Never hide UNKNOWN or failed evidence in the UI.
- Preserve provenance: tool, version, inputs, design version, assumptions, outputs, timestamp/run id when possible.
- Update `docs/DECISIONS.md` when a meaningful architecture decision changes.
- Keep `docs/EXECUTION_PLAN.md` current as implementation progresses.
