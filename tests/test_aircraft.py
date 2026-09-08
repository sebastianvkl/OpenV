import math

import pytest

from openv.aircraft import (MATERIALS, Mission, Parameters, initial_design, patched,
                           structure_output, system)
from openv.core import VerificationEngine


def test_protected_design_patch_and_geometry_bounds():
    hardware=system(Mission(text="A small camera motor glider"))
    design=initial_design(hardware)
    for changes in ({"max_mass_kg":100},{"status":1},{"spar_wall_m":.02},{"battery_x_m":100}):
        with pytest.raises(ValueError):patched(design,changes,"experiment")
    next_design=patched(design,{"battery_x_m":.2},"experiment")
    assert next_design.baseline_id==design.baseline_id
    assert next_design.parent_id==design.id
    assert design.parameters["battery_x_m"]==.4


def test_cantilever_reference_and_span_scaling():
    # Uniform load: M_root = W*b/8. At fixed W, same section, delta scales b^3.
    p=Parameters().model_dump()
    def evaluate(span):
        return structure_output({"geometry":{**p,"span_m":span},"mass_properties":{"mass_kg":1},
            "scenario":{"load_factor":2},"materials":MATERIALS})
    a,b=evaluate(1),evaluate(2)
    assert a.raw["root_moment_nm"]==pytest.approx(2*9.80665/8)
    assert b.raw["tip_deflection_m"]==pytest.approx(8*a.raw["tip_deflection_m"])
    assert b.raw["stress_pa"]==pytest.approx(2*a.raw["stress_pa"])
    assert a.raw["spanwise"][0]["deflection_m"]==0


def test_transitive_mass_input_invalidates_aero_but_not_electrical():
    from openv.aircraft import methods
    hardware=system(Mission(text="A small camera motor glider"))
    design=initial_design(hardware)
    context={"geometry":design.parameters,"mass_properties":{"mass_kg":1,"cg_m":[.4,0,0]},
        "scenario":hardware.scenario,"materials":MATERIALS,"catalog":[c.model_dump() for c in hardware.components]}
    contracts=tuple(c for r in hardware.requirements for c in r.contracts)
    method_map={m.name:m for m in methods()}
    old={name:m.fingerprint(context,contracts) for name,m in method_map.items()}
    context["mass_properties"]={"mass_kg":1.1,"cg_m":[.42,0,0]}
    changed={name for name,m in method_map.items() if old[name]!=m.fingerprint(context,contracts)}
    assert changed=={"mass","aero","structure"}


def test_aero_symmetric_wing_reference():
    import aerosandbox as asb
    from openv.aircraft import airplane
    p=Parameters().model_dump()
    model=airplane(p,[.40,0,0])
    output=asb.AeroBuildup(airplane=model,op_point=asb.OperatingPoint(velocity=12,alpha=3)).run_with_stability_derivatives(beta=False,p=False,q=False,r=False)
    assert float(output["L"][0])>0
    assert float(output["D"][0])>0
    assert 2<float(output["CLa"][0])<9
    # At finite alpha, AeroBuildup's x_np uses CLa rather than the body-normal
    # force derivative. Its inferred neutral point is approximate (<1 mm here).
    # Physical forces must be invariant to translating the moment reference.
    aft=airplane(p,[.45,0,0])
    shifted=asb.AeroBuildup(airplane=aft,op_point=asb.OperatingPoint(velocity=12,alpha=3)).run_with_stability_derivatives(beta=False,p=False,q=False,r=False)
    assert float(shifted["L"][0])==pytest.approx(float(output["L"][0]))
    assert float(shifted["D"][0])==pytest.approx(float(output["D"][0]))
    assert float(shifted["x_np"][0])==pytest.approx(float(output["x_np"][0]),abs=.001)
    assert float(shifted["Cma"][0])>float(output["Cma"][0])
