import numpy as np

from openv.aircraft import Mission, Parameters, methods, system, initial_design
from openv.aircraft_visualization import flow_field
from openv.core import VerificationEngine


def case(altitude=0):
    hardware = system(Mission(text="Reference camera aircraft", altitude_m=altitude))
    design = initial_design(hardware, Parameters(battery_x_m=.28))
    context = {"geometry": design.parameters, "mass_properties": {"mass_kg":1.05, "cg_m":[.375,0,.04]},
        "scenario":hardware.scenario}
    engine = VerificationEngine(methods())
    requirements = tuple(r for r in hardware.requirements if r.contracts[0].method == "aero")
    evidence = engine.verify(design, requirements, context)[0]
    return context, evidence


def test_real_flow_field_bound_to_trim_and_changed_atmosphere():
    context, evidence = case()
    sea = flow_field(context, evidence)
    high_context, high_evidence = case(2000)
    high = flow_field(high_context, high_evidence)
    assert sea["status"] == high["status"] == "COMPUTED"
    assert sea["boundary_residual"] < 1e-5
    assert np.asarray(sea["streamlines_m"]).shape == (45,80,3)
    assert np.isfinite(np.asarray(sea["streamlines_m"])).all()
    assert high["density_kg_m3"] < sea["density_kg_m3"]
    assert high["fingerprint"] != sea["fingerprint"]
    assert not np.allclose(high["streamlines_m"], sea["streamlines_m"])
    assert sea["trim_evidence_id"] == evidence.id
    assert "metrics" not in sea and "gate" not in sea  # A diagnostic cannot grant PASS.
    assert flow_field(high_context, evidence)["status"] == "UNKNOWN"
    corrupt = evidence.model_copy(update={"output_hash":"altered"})
    assert flow_field(context, corrupt)["status"] == "UNKNOWN"
