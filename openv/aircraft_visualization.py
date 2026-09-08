"""Version-bound lifting-surface diagnostics. These never grade requirements."""
from __future__ import annotations

import inspect

from openv.core import ENGINEERING_REVISION, digest


def flow_field(context, aero_evidence):
    import aerosandbox as asb
    import numpy as np
    from openv.aircraft import airplane

    trim = aero_evidence.output.raw
    scenario = context["scenario"]
    inputs = {k: context[k] for k in ("geometry", "mass_properties", "scenario")}
    result = {
        "kind": "lifting-surface diagnostic", "status": "UNKNOWN",
        "method": f"AeroSandbox VortexLatticeMethod/{asb.__version__}",
        "engineering_revision": ENGINEERING_REVISION,
        "source_hash": digest(inspect.getsource(flow_field)),
        "design_id": aero_evidence.design_id, "baseline_id": aero_evidence.baseline_id,
        "trim_evidence_id": aero_evidence.id, "trim_output_hash": aero_evidence.output_hash,
        "inputs": inputs, "units": {"position": "m", "velocity": "m/s", "normal_load": "Pa"},
        "assumptions": [
            "Inviscid lifting surfaces at the recorded AeroBuildup trim; this VLM model is not independently retrimmed.",
            "No fuselage blockage, viscosity, separation, propwash or turbulence. Not CFD or flight validation.",
            "Coarse 8-span by 4-chord panel discretization; no mesh-convergence claim.",
            "Panel normal load is force per panel area, not upper/lower surface pressure or Cp.",
            "Particle motion is an illustrative tracer along computed streamlines, not a transient simulation.",
        ],
    }
    result["fingerprint"] = digest({"inputs": inputs, "trim": aero_evidence.output_hash,
        "source": result["source_hash"], "revision": ENGINEERING_REVISION, "method": result["method"]})
    if digest(inputs) != digest(aero_evidence.inputs) or digest(aero_evidence.output.model_dump()) != aero_evidence.output_hash:
        result["reason"] = "Trim evidence does not match these inputs or its recorded output hash."
        return result
    if not trim.get("cg_m") or trim.get("trim_residual", 1) >= .01 or abs(trim.get("alpha_deg", 90)) > 12 or abs(trim.get("elevator_deg", 90)) > 25:
        result["reason"] = "No admissible trim for this visualization. No flow field generated."
        return result
    try:
        model = asb.VortexLatticeMethod(
            airplane=airplane(inputs["geometry"], trim["cg_m"], trim["elevator_deg"]),
            op_point=asb.OperatingPoint(velocity=scenario["cruise_mps"], alpha=trim["alpha_deg"],
                atmosphere=asb.Atmosphere(altitude=scenario["altitude_m"])),
            spanwise_resolution=8, chordwise_resolution=4, vortex_core_radius=.003,
            align_trailing_vortices_with_wind=True)
        output = model.run()
        # Seed clear of the idealized surfaces; canonical x points downstream.
        seeds = np.array([[-.18, y, z] for z in (.035, .17, .29)
            for y in np.linspace(-inputs["geometry"]["span_m"]*.65, inputs["geometry"]["span_m"]*.65, 15)])
        lines = model.calculate_streamlines(seed_points=seeds, n_steps=80, length=1.7)
        vertices = np.stack([model.front_left_vertices, model.back_left_vertices,
            model.back_right_vertices, model.front_right_vertices], axis=1)
        normal_load = np.sum(model.forces_geometry * model.normal_directions, axis=1) / model.areas
        boundary_velocity = model.get_velocity_at_points(model.collocation_points)
        residual = float(np.max(np.abs(np.sum(boundary_velocity * model.normal_directions, axis=1)))) / scenario["cruise_mps"]
        numeric = [lines, vertices, normal_load, np.array([output["L"], output["D"], residual])]
        if not all(np.isfinite(a).all() for a in numeric) or residual > 1e-5:
            raise ValueError("Nonfinite flow field or panel no-penetration residual exceeds tolerance")
        result.update(status="COMPUTED", boundary_residual=residual,
            density_kg_m3=float(model.op_point.atmosphere.density()),
            lift_n=float(output["L"]), induced_drag_n=float(output["D"]),
            aero_buildup_lift_n=trim["L"], lift_difference_n=float(output["L"])-trim["L"],
            streamlines_m=np.transpose(lines, (0, 2, 1)).round(6).tolist(),
            panels=[{"vertices_m": v.round(6).tolist(), "normal_load_pa": float(q)}
                for v, q in zip(vertices, normal_load)],
            panel_count=len(vertices))
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    return result
