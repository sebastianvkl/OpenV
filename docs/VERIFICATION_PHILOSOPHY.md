# Verification Philosophy

## Fundamental rule

**Generated is not verified.**

Astra can generate claims and hypotheses. External methods must generate the evidence used to accept or reject those claims.

The runtime must preserve a hard boundary between:

- proposal
- execution
- evidence
- judgment

## Core loop

```text
Requirement
    ↓
Verification contract
    ↓
Astra proposes design/change
    ↓
Engineering tool executes
    ↓
Evidence artifact/result
    ↓
Deterministic evaluator
    ↓
PASS / FAIL / UNKNOWN
    ↓
FAIL -> next engineering experiment
PASS -> continue
UNKNOWN -> identify missing evidence / method
```

## Verification contracts

Requirements should be machine-evaluable whenever possible.

Example:

```json
{
  "id": "REQ-014",
  "statement": "Endurance shall be at least 25 minutes",
  "metric": "endurance_min",
  "operator": ">=",
  "threshold": 25,
  "verification": {
    "method": "mission_simulation",
    "tool": "aerosandbox",
    "scenario": "cruise_with_300g_payload"
  }
}
```

The evaluator - not Astra - performs the comparison.

## Status model

Use at least:

- PASS
- FAIL
- UNKNOWN
- STALE / NEEDS_REVERIFY (useful internal state)

Meaning:

- PASS: evidence satisfies the contract
- FAIL: evidence violates the contract
- UNKNOWN: no sufficient verification method/evidence currently exists
- STALE: evidence once existed but a relevant design/input change invalidated it

## Verification ladder

Different evidence has different strength. Keep the method visible.

### Level 0 - model reasoning

Example: "Astra believes this should be strong enough."

This is not verification.

### Level 1 - deterministic constraints

Examples:

- dimension limits
- voltage compatibility
- mass arithmetic
- printer build envelope
- interference checks
- prop clearance
- tool/fastener access

### Level 2 - analytical engineering calculations

Examples:

- torque
- beam stress
- wing loading
- energy budget
- current draw
- thermal resistance approximation

### Level 3 - numerical simulation / solver

Examples:

- AeroSandbox
- FEA
- SPICE
- thermal simulation
- multibody dynamics

### Level 4 - independent cross-check

Where practical, compare two methods.

Example:

- analytical endurance model
- mission simulation

Disagreement should be surfaced, not hidden.

### Level 5 - physical validation

Examples:

- thrust stand
- load test
- dimensional measurement
- current measurement
- flight test

A design can be simulation-verified while physical validation remains UNKNOWN.

## Evidence provenance

Every PASS should be inspectable.

Store/reference:

- requirement id
- design version
- verification method
- tool name
- tool/solver version if available
- input parameters
- assumptions
- raw output/result
- derived metric
- run id
- timestamp
- source files/artifacts

A green check with no evidence should be treated as a bug.

## Evidence invalidation

Evidence is only valid for the design/input state it was produced against.

Build a dependency graph from design state to verification evidence.

Example:

```text
Battery changed
  -> mass changed
      -> CG evidence STALE
      -> stall-speed evidence STALE
      -> structural-load evidence STALE
  -> capacity changed
      -> endurance evidence STALE
  -> electrical configuration changed
      -> voltage/current evidence STALE

Motor-bracket DFM result unchanged
      -> remains VALID
```

Do not blindly re-run every verifier if dependency tracking can identify affected checks.

## Design changes as experiments

Before modifying the design, Astra should record:

- the current problem
- hypothesis
- exact intended changes
- expected effect
- verification evidence likely to be invalidated

After execution, record:

- actual result
- requirements improved/regressed
- whether to keep, branch, or abandon the candidate

This is AutoResearch-style iteration applied to hardware.

## Do not automatically revert every regression

Engineering is multi-objective.

A candidate that improves endurance but temporarily breaks structure can still be valuable if it reveals a useful Pareto move.

Maintain design lineage and optionally a small set of promising candidates rather than only one linear current state.

## Robustness / challenge phase

After nominal verification passes, run a challenge stage.

Astra should propose realistic perturbations based on sensitivity and failure modes, then the normal deterministic verification engine re-evaluates them.

Report separately:

- nominal requirements
- robustness tests
- known weaknesses
- unknowns

## Manufacturing verification is not functional verification

Keep these distinct.

Example:

- structural solver: does the bracket survive the load?
- RMFG: can the bracket be manufactured with the selected process/material?

A DFM PASS must never be used as evidence for structural adequacy.

## Assembly verification

An AI-generated assembly animation is not proof that assembly is possible.

For each step, verify when practical:

- insertion path collision
- part orientation
- required clearances
- fastener access
- tool access envelope
- dependency/order constraints
- whether future parts become inaccessible

If invalid, either change sequence or redesign geometry.

## Real component data

Do not let the model invent physical properties when authoritative component data can be sourced.

Mark every property as one of:

- sourced
- measured
- computed
- assumed
- estimated

Assumptions should be easy to inspect because they often drive verification uncertainty.

## Release gates

Release criteria should be explicit per project.

Example:

- all mandatory requirements PASS
- no blocking DFM failures
- no unresolved interface violations
- no impossible assembly steps
- required artifacts generated
- allowed UNKNOWN items explicitly acknowledged

Do not let the model silently redefine the release criteria.

## Design-for-test

If a requirement cannot be closed, Astra should be able to propose the verification method and, where useful, create test fixtures/features.

This is part of the engineering output, not an afterthought.

## User-facing trust model

The UI should never collapse all evidence into an unexplained score.

Prefer explicit labels such as:

- VERIFIED
- ESTIMATED
- UNKNOWN
- FAILED
- NEEDS RE-VERIFY

The credibility of the product comes from showing limits, not hiding them.
