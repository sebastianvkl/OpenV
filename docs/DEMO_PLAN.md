# Hackathon Demo Plan

Current scope clarification (2026-09-08, D021-D023): the 4:00 p.m. target includes real CAD and a manufacturing package, actual aircraft analysis visualizations, and a mission/design perturbation that triggers failure, invalidation, and Astra redesign. Dalus is central through MCP only. Physical fabrication/flight testing is not today's deliverable. The implementation order and acceptance criteria in `EXECUTION_PLAN.md` supersede the older P0/P1/P2 grouping below where they differ; never label an incomplete manufacturing or flight-verification gate as passed.

## Demo thesis

The audience should understand one idea immediately:

**AI-generated hardware can look correct and still be wrong. This pipeline finds the failures and keeps redesigning until the requirements are backed by engineering evidence.**

## Primary demo system

Small RC motor glider.

Suggested user prompt:

> Build me a small RC aircraft that can carry a 300 g camera for at least 25 minutes, cost less than $350, and use parts/custom components that are realistic to source and manufacture.

Exact numbers can be tuned so the first design predictably fails and later iterations can realistically pass.

## Desired stage flow

### 1. Prompt

Show a very simple entry screen:

> What do you want to build?

Enter the aircraft request.

### 2. V-model creation

Astra converts the request into:

- requirements
- architecture
- interfaces
- verification plan

Show these appearing in Dalus or in a mirrored UI fed from Dalus.

### 3. First design

Generate/select:

- geometry
- motor
- ESC
- propeller
- battery
- servos
- materials

Render the aircraft.

Then show the important label:

**DESIGN GENERATED - NOT VERIFIED**

### 4. Verification reveals problems

Run real checks.

Desired visible result:

```text
Payload                 PASS
Cost                    PASS
Endurance               FAIL
Stall speed             FAIL
CG / stability          FAIL
Manufacturability       FAIL or UNKNOWN
```

The first design should look plausible. That contrast is the point.

### 5. User says "Make it actually work"

Astra receives concrete failures and starts experiments.

Display experiment history visibly:

```text
v1  4 failures
v2  3 failures
v3  2 failures
v4  1 failure
v5  all nominal requirements pass
```

For each experiment, optionally show:

- hypothesis
- key parameter changes
- expected effect
- measured result

### 6. Evidence updates Dalus

As checks pass, requirements become green because evidence has been recorded.

Click one requirement and show:

- threshold
- actual result
- tool
- design version
- inputs/assumptions
- evidence run id

This is a key Dalus moment.

### 7. Manufacturing check

If time permits, select one meaningful fabricated metal component such as a motor bracket.

Send it through RMFG:

- first DFM failure is ideal if deterministic/reliable
- Astra adjusts geometry
- second submission passes
- quote becomes cost evidence

Do not depend on this for the core demo.

### 8. Robustness

Show a short challenge phase if it is reliable:

- battery capacity -15%
- payload +10%
- CG shift

Display nominal vs robustness separately.

### 9. Release Design

Only after gates pass, reveal a polished DayRing/PX4-style output experience.

Tabs:

- Overview
- Verify
- Exploded
- Assembly
- BOM
- Manufacturing
- Files

### 10. Assembly payoff

Show:

- exploded aircraft
- Play Assembly
- Previous / Next / Replay
- parts/tools/checks

The geometry itself animates into place.

### 11. Final artifacts

Show buttons for:

- build package
- STEP/STL
- BOM
- verification report
- illustrated assembly PDF
- assembly video
- Open in Dalus
- optional Open in Onshape

## Stage line

A useful transition after the first CAD appears:

> It looks like an airplane. But that doesn't mean it works.

Then click Verify.

Another useful line:

> Astra is allowed to propose a design. It is not allowed to grade its own homework.

## P0 live demo requirements

Must work live:

- user mission
- requirements
- first design state
- at least two independent verification checks
- at least one deterministic failure
- Astra redesign loop
- re-verification
- evidence-backed PASS
- visible experiment history

## P1

- Dalus write-through and evidence trace
- nice Three.js visualization
- BOM / real component data
- evidence invalidation

## P2 / stretch

- RMFG
- Onshape handoff
- robustness mode
- assembly validation
- assembly animation
- PDF manual
- physical P1S print

## Demo reliability strategy

Build the real live path first.

Also record one successful end-to-end run so the UI can replay the real captured trajectory if a network/service integration fails during judging. If replay mode is used, label it clearly as a recorded run rather than pretending it is live.

Cache static reference data for the aircraft demo where terms permit so supplier or solver latency does not ruin the demo.

Do not fake verifier outputs. A recorded real run is acceptable as fallback; invented passing numbers are not.
