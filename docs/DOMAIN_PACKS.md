# Domain Pack Concept

The runtime should stay hardware-generic. Domain packs supply expert engineering context, tool mappings, and verification strategies.

## Why domain packs

A user should be able to say "build me a plane" without personally knowing every check an experienced aerospace engineer would remember.

The domain pack should encode that expert checklist and connect it to available tools.

## Conceptual structure

```text
domains/
  generic/
    geometry/
    cost/
    sourcing/
    assembly/
    manufacturability/
  aircraft/
    requirements/
    architecture/
    interfaces/
    aerodynamics/
    propulsion/
    stability/
    structures/
    manufacturing/
    assembly/
    verification/
  electronics/
  robotics/
```

Only `aircraft` needs to be implemented for the hackathon.

## Aircraft expert context examples

The aircraft pack should make Astra remember to consider things such as:

- payload and mission profile
- total mass budget
- wing loading
- stall speed
- aerodynamic efficiency
- thrust margin
- motor/prop/battery compatibility
- ESC current margin
- center of gravity
- static stability margin
- control-surface authority
- servo torque
- prop clearance
- wing spar orientation/load path
- battery insertion/removal path
- fastener accessibility
- field serviceability
- manufacturing process/material constraints
- component availability and sourcing
- robustness to battery degradation / payload / CG shifts

## Tool mapping examples

```yaml
requirement: endurance
preferred_methods:
  - analytical_energy_model
  - aerosandbox_mission_simulation
```

```yaml
requirement: manufacturable_motor_bracket
preferred_methods:
  - geometry_rules
  - rmfg_dfm
```

```yaml
requirement: assembly_access
preferred_methods:
  - insertion_path_check
  - fastener_tool_envelope_check
```

## Domain pack output

A domain pack can contribute:

- requirement templates
- decomposition heuristics
- interface templates
- design parameter schemas
- tool capability mappings
- verification plans
- failure-mode prompts
- robustness scenarios
- assembly heuristics

The generic runtime should not hard-code the aircraft-specific details.

## Minimal public extension contract

Per D025, a domain pack plugs into the same pipeline used by the live reference demo. It supplies an ID/version, applicable mission/design schema, requirement and interface templates, reviewed verification-contract bindings, declared dependency mappings, and mappings from canonical state to CAD/analysis/assembly inputs. Tool adapters implement the actual external execution and normalize results.

The core owns baseline/version handling, evidence admission, deterministic verdicts, invalidation, experiment history, and gates. A domain pack or model proposal cannot bypass those rules. Adapter selection can be a static configuration in P0; adding a domain must not require editing the core loop.

An unsupported mission may still produce requirements and a verification plan, but unavailable methods stay explicit UNKNOWNs. Adding a replacement tool requires validating its units, output semantics, assumptions, applicability, and provenance against the contract. Method changes invalidate affected evidence.

P0 should include one minimal non-aircraft dimensional-check regression through the generic runtime and document how to add a real domain or verifier. This validates the boundary without promising a second complete hardware domain today.

## Implemented extension points

The static registry is `openv/domains.py`. `AircraftDomain` supplies:

- `define(proposal, mission_text)` → frozen `HardwareSystem` and `DesignVersion`.
- `methods()` → registered `Method` adapters declaring versions and input dependencies.
- `patch(design, changes, experiment_id)` → validated child version; reject unsupported fields.
- `build(design, scenario, directory)` → artifacts and explicit coverage metadata.
- `context(...)` and `pending_context(...)` → actual verification inputs and immediate stale-state inputs.
- `package(...)` → domain-owned fabrication/assembly files and their public artifact references.
- `read_seed(...)` and `branch(...)` → optional user experiment support, retaining accepted contracts.

The engineer adapter implements `define` and `redesign`, exposes a provider `label`
and model-call provenance in `calls`. The pipeline owns evidence generation and
comparison; neither proposer method returns verdicts. The minimal bracket domain
in `tests/test_pipeline.py` runs an actual dimensional FAIL → repair → invalidation
→ PASS through `Pipeline.run`, including packaging. It is a boundary regression,
not a second supported public hardware domain.

To add a verifier, return `ToolOutput` with metrics (`value`, `unit`, `admissible`,
`reason`), raw results, assumptions and diagnostics. Bind a frozen `Contract` to
its method/metric and explicit threshold/scope. Declare every consumed source,
scenario and derived input as a dependency. Missing metrics, wrong units,
unadmitted assumptions and missing methods produce UNKNOWN. Add a known failing
case and an input-change invalidation case before using the method in a demo.

The current website's mission schema and visualizer are aircraft-specific. A new
production domain needs its own validated mission adapter and presentation; it
can reuse the same orchestration, evidence evaluator, Dalus adapter, job service
pattern and manifest format. Dynamic plugin discovery is deferred.
