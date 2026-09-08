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
