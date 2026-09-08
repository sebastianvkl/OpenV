"""The first domain pack: a bounded conventional electric motor-glider.

SI units throughout. Geometry axes: x aft from the nose, y right, z up.
These are modeled engineering checks, not flight clearance or certification.
"""
from __future__ import annotations

import math
from typing import Any

from pydantic import Field, model_validator

from openv.core import (Component, Contract, DesignVersion, HardwareSystem, Interface,
                       Measurement, Method, Property, Record, Requirement, ToolOutput, digest)


class Mission(Record):
    text: str = Field(min_length=5, max_length=4000)
    payload_kg: float = Field(default=.15, ge=0, le=.5)
    cruise_mps: float = Field(default=12, ge=8, le=22)
    endurance_min: float = Field(default=20, ge=1, le=90)
    max_mass_kg: float = Field(default=1.2, ge=.3, le=3)
    altitude_m: float = Field(default=0, ge=0, le=2500)
    load_factor: float = Field(default=2.5, ge=1, le=4)


class Parameters(Record):
    span_m: float = Field(default=1.3, ge=.9, le=2.0)
    chord_m: float = Field(default=.21, ge=.15, le=.28)
    taper: float = Field(default=.7, ge=.5, le=1)
    tail_span_m: float = Field(default=.42, ge=.3, le=.65)
    tail_chord_m: float = Field(default=.12, ge=.08, le=.18)
    tail_incidence_deg: float = Field(default=0, ge=-5, le=5)
    battery_x_m: float = Field(default=.40, ge=.12, le=.46)
    payload_x_m: float = Field(default=.22, ge=.1, le=.42)
    spar_od_m: float = Field(default=.008, ge=.006, le=.016)
    spar_wall_m: float = Field(default=.001, ge=.0005, le=.002)
    skin_m: float = Field(default=.0006, ge=.0004, le=.0012)

    @model_validator(mode="after")
    def geometry_feasible(self):
        if self.spar_wall_m * 2 >= self.spar_od_m:
            raise ValueError("Spar must have a positive bore")
        if self.spar_od_m + 2 * self.skin_m > .10 * self.chord_m * self.taper:
            raise ValueError("Spar does not fit inside the tip airfoil")
        return self


MATERIALS = {
    "printed": {"density_kg_m3": 620., "quality": "assumed", "note": "Foamed PLA effective density; calibrate coupons and sliced mass before fabrication."},
    "carbon": {"density_kg_m3": 1600., "E_pa": 70e9, "allowable_pa": 350e6,
               "quality": "assumed", "note": "Generic unidirectional tube model; no selected supplier/layup or joint test."},
}


def catalog() -> tuple[Component, ...]:
    def prop(value, unit, source, quality="sourced"):
        return Property(value=value, unit=unit, quality=quality, source=source)
    esc = "https://www.hobbywing.com/uploads/file/20240717/003cfdbd5f9fad6ac356f2396c8103b3.pdf"
    motor = "https://shop.emax-usa.com/collections/wing-uav/products/emx-mt-0409-gt2215-1180kv"
    battery = "https://www.tattuworld.com/products/tattu-classic-1300mah-3s1p-11-1v-75c-fpv-lipo-battery.html"
    return (
        Component(id="esc", name="Skywalker 20A V2", manufacturer="Hobbywing", part_number="30205200",
            properties={"mass_kg": prop(.019,"kg",esc), "current_a":prop(20,"A",esc),
                "min_cells":prop(2,"1",esc), "max_cells":prop(3,"1",esc),
                "length_m":prop(.045,"m",esc), "width_m":prop(.023,"m",esc), "height_m":prop(.008,"m",esc),
                "bec_v":prop(5,"V",esc), "bec_a":prop(3,"A",esc)}),
        Component(id="motor", name="EMAX GT2215 1180KV", manufacturer="EMAX", part_number="EMX-MT-0409",
            properties={"kv":prop(1180,"rpm/V",motor), "mass_kg":prop(.060,"kg","Pending exact motor datasheet","estimated"),
                        "diameter_m":prop(.028,"m","Envelope pending vendor drawing","estimated")}),
        Component(id="battery", name="Tattu Classic 1300mAh 3S 75C", manufacturer="Tattu", part_number="TAA13003S75X6",properties={
            "mass_kg":prop(.122,"kg",battery),"cells":prop(3,"1",battery),
            "capacity_ah":prop(1.3,"Ah",battery),"nominal_v":prop(11.1,"V",battery),
            "length_m":prop(.072,"m",battery),"width_m":prop(.036,"m",battery),"height_m":prop(.022,"m",battery),
            "connector":prop("XT60","1",battery)}),
        Component(id="servo", name="Four micro servos, selection pending", properties={
            "mass_kg":prop(.009,"kg","Per-servo mass allowance","estimated"),
            "quantity":prop(4,"1","Two ailerons, elevator and rudder","computed")}),
        Component(id="receiver", name="PWM receiver, selection pending", properties={
            "mass_kg":prop(.008,"kg","Receiver mass allowance","estimated")}),
        Component(id="propeller", name="8 × 4 electric propeller allocation", properties={
            "diameter_m":prop(.2032,"m","Design allocation; vendor and rotation pending","assumed"),
            "mass_kg":prop(.008,"kg","Propeller mass allowance","estimated")}),
    )


def system(mission: Mission) -> HardwareSystem:
    def req(id, statement, method, metric, operator, threshold, unit, scope, level="system", owner="aircraft"):
        return Requirement(id=id, statement=statement, level=level, owner=owner,
            contracts=(Contract(id=f"{id}-contract", method=method, metric=metric, operator=operator,
                                threshold=threshold, unit=unit, scope=scope),))
    modeled = "Declared geometry, mass/material assumptions and nominal operating scenario only"
    requirements = (
        req("mass", "Modeled takeoff mass within allocation", "mass", "mass_kg", "<=", mission.max_mass_kg,"kg",modeled),
        req("trim", "Steady level trim solution within control limits", "aero", "trim_residual", "<=", .01,"1",modeled),
        req("stability-min", "Modeled longitudinal static margin at least 5% MAC", "aero", "static_margin", ">=", .05,"1",modeled),
        req("stability-max", "Modeled longitudinal static margin at most 25% MAC", "aero", "static_margin", "<=", .25,"1",modeled),
        req("alpha", "Trim angle remains within reviewed analysis envelope", "aero", "abs_alpha_deg", "<=", 8,"deg",modeled),
        req("spar", "Idealized spar bending margin at declared load factor", "structure", "stress_margin", ">=", 1,"1",modeled,"component","wing-spar"),
        req("deflection", "Idealized spar tip deflection below 5% semispan", "structure", "relative_deflection", "<=", .05,"1",modeled,"component","wing-spar"),
        req("esc-cells", "Allocated battery cell count within ESC specification", "electrical", "cell_compatibility", "==", 1,"1","Sourced ESC cell limits; declared 3S allocation","integration","power"),
        req("print-size", "Every printed part fits 256 mm build envelope", "cad", "max_print_dimension_m", "<=", .256,"m","Axis-aligned part bounds; orientation recorded, not a slicing check","component","airframe"),
        req("cad-valid", "All exported custom CAD solids are valid", "cad", "invalid_solids", "==", 0,"1","OpenCascade topology check only","component","airframe"),
        req("endurance", "Cruise endurance meets mission", "propulsion", "endurance_min", ">=", mission.endurance_min,"min","Requires sourced prop/motor map, energy budget and reserve"),
        req("assembly", "Assembly sequence, tool access and fit are verified", "assembly", "verified", "==", 1,"1","Requires geometry and access checks","integration","airframe"),
        req("full-structure", "Airframe, joints and controls survive design loads", "airframe-load-test", "verified", "==", 1,"1","Spar calculation alone does not establish this claim"),
        req("flight", "Manufactured aircraft meets the mission in flight", "flight-test", "verified", "==", 1,"1","Physical measurements required","mission"),
    )
    baseline = "baseline-" + digest({"mission":mission.model_dump(), "contracts":[r.model_dump() for r in requirements]})[:12]
    return HardwareSystem(mission=mission.text, baseline_id=baseline, domain="motor-glider/1",
        architecture={"aircraft":["airframe","power","controls","payload"],
                      "airframe":["wing","wing-spar","fuselage","tail","boom"]},
        requirements=requirements, components=catalog(), scenario=mission.model_dump(),
        interfaces=(
            Interface(id="battery-esc",endpoints=("battery","esc"),kind="electrical",
                definition={"cells":3,"nominal_v":11.1,"connector":"UNKNOWN"},requirement_ids=("esc-cells",)),
            Interface(id="wing-spar",endpoints=("wing","wing-spar","fuselage"),kind="mechanical",
                definition={"frame":"x aft, y right, z up; SI meters", "spar_x_chord":.30,"joint_strength":"UNKNOWN"},requirement_ids=("spar","full-structure")),
            Interface(id="control-linkages",endpoints=("servo","wing","tail","receiver"),kind="control",
                definition={"channels":4,"hinge_fraction":.75,"torque_and_travel":"UNKNOWN"},requirement_ids=("assembly",)),
        ))


def initial_design(hardware: HardwareSystem, parameters: Parameters | None = None) -> DesignVersion:
    return DesignVersion(baseline_id=hardware.baseline_id, parameters=(parameters or Parameters()).model_dump(),
                         component_ids=tuple(c.id for c in hardware.components))


def patched(design: DesignVersion, changes: dict[str, float], experiment_id: str) -> DesignVersion:
    if not changes or not set(changes).issubset(Parameters.model_fields):
        raise ValueError("Only declared design parameters may change; requirements and source facts are protected")
    parameters = Parameters.model_validate({**design.parameters, **changes})
    if parameters.model_dump() == design.parameters:
        raise ValueError("The proposal must make a specific engineering change")
    return DesignVersion(parent_id=design.id, baseline_id=design.baseline_id,
        parameters=parameters.model_dump(), component_ids=design.component_ids, experiment_id=experiment_id)


def wing_sections(p: dict, tail=False):
    if tail:
        return [([.88,0,.07],p["tail_chord_m"]),
                ([.90,p["tail_span_m"]/2,.07],p["tail_chord_m"]*.7)]
    return [([.28,0,.11],p["chord_m"]),
            ([.30,p["span_m"]/2,.11+.05*p["span_m"]/2],p["chord_m"]*p["taper"])]


def airplane(p: dict, cg: list[float], elevator=0.):
    import aerosandbox as asb
    wings = []
    for tail in (False, True):
        wings.append(asb.Wing(name="tail" if tail else "wing", symmetric=True,
            xsecs=[asb.WingXSec(xyz_le=xyz,chord=chord,
                twist=p["tail_incidence_deg"] if tail else 0,
                airfoil=asb.Airfoil("naca0012" if tail else "naca2412"),
                control_surfaces=[asb.ControlSurface(name="elevator",deflection=elevator)] if tail else [])
                for xyz,chord in wing_sections(p,tail)]))
    wings.append(asb.Wing(name="fin",symmetric=False,xsecs=[
        asb.WingXSec(xyz_le=[.87,0,.07],chord=.15,airfoil=asb.Airfoil("naca0012")),
        asb.WingXSec(xyz_le=[.94,0,.24],chord=.075,airfoil=asb.Airfoil("naca0012"))]))
    fuselage=asb.Fuselage(name="pod",xsecs=[asb.FuselageXSec(xyz_c=[x,0,0],radius=r)
        for x,r in [(0,.003),(.08,.045),(.22,.055),(.43,.05),(.58,.025),(.66,.008)]])
    return asb.Airplane(name="OpenV / Albatross 01",wings=wings,fuselages=[fuselage],xyz_ref=cg)


def mass_output(inputs):
    mass = inputs["mass_properties"]
    return ToolOutput(metrics={"mass_kg":Measurement(value=mass["mass_kg"],unit="kg")}, raw=mass,
        assumptions=("Custom-part mass uses CAD volume and assumed process density; COTS allowances are labeled in BOM.",))


def aero_output(inputs):
    import aerosandbox as asb
    import numpy as np
    from scipy.optimize import root
    p, mass, scenario = inputs["geometry"], inputs["mass_properties"], inputs["scenario"]
    velocity = scenario["cruise_mps"]
    weight = mass["mass_kg"] * 9.80665
    atmosphere = asb.Atmosphere(altitude=scenario["altitude_m"])
    def analysis(alpha, elevator, derivatives=False, speed=velocity):
        model = asb.AeroBuildup(airplane=airplane(p,mass["cg_m"],elevator),
            op_point=asb.OperatingPoint(velocity=speed,alpha=float(alpha),atmosphere=atmosphere))
        result = model.run_with_stability_derivatives(beta=False,p=False,q=False,r=False) if derivatives else model.run()
        return {key:float(np.asarray(value).ravel()[0]) for key,value in result.items()
                if key in ("L","D","CL","CD","Cm","CLa","Cma","x_np","m_b")}
    def residual(x):
        result = analysis(*x)
        return [result["L"]/weight-1, result["Cm"]]
    solution = root(residual,[3.,0.],tol=1e-6)
    alpha, elevator = map(float, solution.x)
    # Do not use a solver's success flag alone; validate residuals and domain.
    values = analysis(alpha,elevator,derivatives=True)
    error = max(abs(v) for v in residual(solution.x))
    bounded = abs(elevator) <= 25 and abs(alpha) <= 12 and values["CLa"] > 0
    mac = float(airplane(p,mass["cg_m"]).wings[0].mean_aerodynamic_chord())
    margin = (values["x_np"]-mass["cg_m"][0])/mac
    envelope=[]
    for speed in [8.,10.,12.,14.,16.,18.]:
        r=analysis(alpha,elevator,speed=speed)
        envelope.append({"speed_mps":speed,"lift_n":r["L"],"drag_n":r["D"],"weight_n":weight,
                         "alpha_deg":alpha,"note":"Fixed trim attitude sweep; not retrimmed or a stall prediction"})
    return ToolOutput(metrics={
        "trim_residual":Measurement(value=error if bounded else max(1.,error),unit="1"),
        "static_margin":Measurement(value=margin,unit="1",admissible=error<.01 and bounded,reason="Requires admissible trim"),
        "abs_alpha_deg":Measurement(value=abs(alpha),unit="deg"),
        "drag_n":Measurement(value=values["D"],unit="N",admissible=bounded and error<.01),
    },raw={**values,"alpha_deg":alpha,"elevator_deg":elevator,"trim_residual":error,"cg_m":mass["cg_m"],
           "mac_m":mac,"static_margin":margin,"weight_n":weight,"velocity_mps":velocity,"envelope":envelope,
           "solver_converged":bool(solution.success)},
       assumptions=("AeroSandbox AeroBuildup quasi-steady aerodynamic model, NACA2412 wing / NACA0012 tail.",
                    "No propwash, flutter, dynamic controllability or flight validation; mass inputs include estimates.",
                    "Analysis envelope: |alpha| <= 12 deg and |elevator| <= 25 deg; requirement restricts trim alpha to 8 deg."))


def structure_output(inputs):
    p, mass, scenario, material = inputs["geometry"], inputs["mass_properties"], inputs["scenario"],inputs["materials"]["carbon"]
    halfspan=p["span_m"]/2
    total_lift=mass["mass_kg"]*9.80665*scenario["load_factor"]
    load_per_m=total_lift/p["span_m"]
    od, inner=p["spar_od_m"],p["spar_od_m"]-2*p["spar_wall_m"]
    inertia=math.pi*(od**4-inner**4)/64
    moment=load_per_m*halfspan**2/2
    stress=moment*(od/2)/inertia
    deflection=load_per_m*halfspan**4/(8*material["E_pa"]*inertia)
    points=[]
    for i in range(21):
        y=halfspan*i/20
        dy=load_per_m*y*y*(6*halfspan**2-4*halfspan*y+y*y)/(24*material["E_pa"]*inertia)
        points.append({"y_m":y,"deflection_m":dy,"moment_nm":load_per_m*(halfspan-y)**2/2})
    return ToolOutput(metrics={"stress_margin":Measurement(value=material["allowable_pa"]/stress,unit="1"),
        "relative_deflection":Measurement(value=deflection/halfspan,unit="1")},
        raw={"stress_pa":stress,"tip_deflection_m":deflection,"root_moment_nm":moment,"second_moment_m4":inertia,
             "spanwise":points,"material":material,"total_lift_n":total_lift},
        assumptions=("Uniform distributed load on two independent cantilever semispans; ideal root restraint.",
                     "Assumed tube properties; joints, buckling, torsion, fatigue, skin and controls are not covered."))


def electrical_output(inputs):
    parts={c["id"]:c["properties"] for c in inputs["catalog"]}
    cells=parts["battery"]["cells"]["value"]
    low,high=(parts["esc"][k]["value"] for k in ("min_cells","max_cells"))
    return ToolOutput(metrics={"cell_compatibility":Measurement(value=int(low<=cells<=high),unit="1")},
        raw={"allocated_cells":cells,"esc_min":low,"esc_max":high},
        assumptions=("Checks declared battery cell allocation against manufacturer ESC rating; current, BEC and connectors remain unverified.",))


def methods():
    import aerosandbox
    return [Method("mass","cad-mass/1",("mass_properties",),mass_output),
        Method("aero",f"aerosandbox/{aerosandbox.__version__};openv/1",("geometry","mass_properties","scenario"),aero_output),
        Method("structure","euler-bernoulli/1",("geometry","mass_properties","scenario","materials"),structure_output),
        Method("electrical","cell-rating/1",("catalog",),electrical_output)]
