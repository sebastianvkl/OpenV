"""Parametric manufacturing candidates and CAD-derived web meshes.

The canonical geometry is SI. OpenCascade construction/export is explicitly mm;
the viewer receives meters. Vendor envelopes are marked, never fabrication parts.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from openv.aircraft import MATERIALS, Parameters, catalog, wing_sections
from openv.core import Measurement, Method, ToolOutput, digest


def build(parameters: dict, mission: dict, output_dir: Path) -> dict:
    import aerosandbox as asb
    import numpy as np
    from build123d import (Box, CenterOf, Compound, Cylinder, Location, Plane, Solid,
                          Vector, Wire, export_step, export_stl, import_step)

    p = Parameters.model_validate(parameters).model_dump()
    output_dir.mkdir(parents=True, exist_ok=True)
    cad_dir = output_dir / "cad"
    cad_dir.mkdir(exist_ok=True)
    parts, shapes = [], []
    sourced_parts={c.id:c for c in catalog()}

    def add(id, label, shape, group, process="print", mass_kg=None, color="#e2e9df", note="", stock=None):
        shape.label = id
        shape_valid = bool(shape.is_valid)
        box = shape.bounding_box()
        dimensions = [float(v)/1000 for v in box.size]
        centroid = [float(v)/1000 for v in shape.center(CenterOf.MASS)]
        density = 650. if process=="cut-plywood" else MATERIALS["carbon" if process == "cut-carbon" else "printed"]["density_kg_m3"]
        mass = float(shape.volume)*1e-9*density if mass_kg is None else mass_kg
        component=sourced_parts.get("servo" if id.startswith("servo-") else id)
        if component and "mass_kg" in component.properties and process=="purchase":
            mass=float(component.properties["mass_kg"].value)
        verts, faces = shape.tessellate(.5,.15)
        mesh={"positions":[float(n)/1000 for v in verts for n in v],
              "indices":[int(n) for face in faces for n in face]}
        if process == "print":
            export_stl(shape,str(cad_dir/f"{id}.stl"))
        elif process.startswith("cut-"):
            export_step(shape,str(cad_dir/f"{id}.step"))
        parts.append({"id":id,"name":label,"group":group,"process":process,"mass_kg":mass,
            "mass_quality":"computed with assumed material density" if mass_kg is None else "allocated; see source catalog",
            "dimensions_m":dimensions,"centroid_m":centroid,"color":color,"valid":shape_valid,
            "volume_m3":float(shape.volume)*1e-9,"mesh":mesh,"note":note,
            "stock":stock or {},
            "file":f"cad/{id}.stl" if process=="print" else f"cad/{id}.step" if process.startswith("cut-") else None})
        if component:
            parts[-1]["component"]=component.model_dump()
        shapes.append(shape)

    def tube(start, end, diameter, wall):
        a=np.array(start)*1000; b=np.array(end)*1000
        vector=b-a; length=float(np.linalg.norm(vector))
        plane=Plane(origin=tuple(a),z_dir=tuple(vector))
        return Solid.make_cylinder(diameter*500,length,plane)-Solid.make_cylinder((diameter/2-wall)*1000,length,plane)

    def foil_wire(xyz, chord, airfoil, scale=1., incidence=0., vertical=False):
        coords=asb.Airfoil(airfoil).repanel(n_points_per_side=35).coordinates
        angle=math.radians(incidence)
        points=[]
        for x,z in coords[:-1]:
            x=(x-.5)*scale+.5; z*=scale
            xx=chord*(x*math.cos(angle)+z*math.sin(angle))
            zz=chord*(-x*math.sin(angle)+z*math.cos(angle))
            points.append(tuple(1000*v for v in ([xyz[0]+xx,xyz[1]+zz,xyz[2]] if vertical else [xyz[0]+xx,xyz[1],xyz[2]+zz])))
        return Wire.make_polygon(points,close=True)

    # Loft and split wings into individually printable segments. The interior loft
    # is deliberately labeled as an approximation, not a wall-thickness proof.
    for is_tail in (False,True):
        section=wing_sections(p,is_tail)
        (root,cr),(tip,ct)=section
        root,tip=np.array(root),np.array(tip)
        count=math.ceil(float(tip[1])/.22)
        foil="naca0012" if is_tail else "naca2412"
        incidence=p["tail_incidence_deg"] if is_tail else 0
        for sign in (-1,1):
            side="L" if sign<0 else "R"
            for index in range(count):
                ends=[]
                for t in [index/count,(index+1)/count]:
                    xyz=root+(tip-root)*t; xyz[1]*=sign
                    ends.append((xyz,cr+(ct-cr)*t))
                outer=Solid.make_loft([foil_wire(xyz,c,foil,incidence=incidence) for xyz,c in ends],ruled=True)
                inner=Solid.make_loft([foil_wire(xyz,c,foil,scale=max(.72,1-p["skin_m"]/(.06*c)),incidence=incidence) for xyz,c in ends],ruled=True)
                shell=outer-inner
                prefix="tail" if is_tail else "wing"
                if not is_tail:
                    # Interior rib at each segment root, with a clearance bore
                    # following the same spar datum/dihedral as the assembly.
                    (xyz,c),_=ends
                    rib_ends=[(xyz+np.array([0,sign*.001,0]),c),(xyz+np.array([0,sign*.002,0]),c)]
                    rib=Solid.make_loft([foil_wire(q,ch,foil,scale=.985) for q,ch in rib_ends],ruled=True)
                    shell=shell+rib
                    a=root.copy();b=tip.copy();a[0]+=.30*cr;b[0]+=.30*ct;a[2]+=.015*cr;b[2]+=.015*ct;b[1]*=sign
                    vector=(b-a)*1000
                    bore=Solid.make_cylinder((p["spar_od_m"]+.0003)*500,float(np.linalg.norm(vector))+4,
                        Plane(origin=tuple(a*1000-vector/np.linalg.norm(vector)*2),z_dir=tuple(vector)))
                    shell=shell-bore
                # Split physical control surfaces with a declared 0.6 mm hinge
                # gap. The aerodynamic model's hinge datum is 75% chord.
                if is_tail or index>=count//2+1:
                    def control_mask(gap):
                        wires=[]
                        for xyz,c in ends:
                            hinge=(xyz[0]+.75*c*math.cos(math.radians(incidence)))*1000+gap
                            y=xyz[1]*1000
                            wires.append(Wire.make_polygon([(hinge,y,-150),(1100,y,-150),(1100,y,350),(hinge,y,350)],close=True))
                        return Solid.make_loft(wires,ruled=True)
                    control=shell & control_mask(.3)
                    shell=shell-control_mask(-.3)
                    control_name="elevator" if is_tail else "aileron"
                    add(f"{control_name}-{side}-{index+1}",f"{control_name.title()} {side} {index+1}",control,"controls",color="#c4d3b8",
                        note="75% chord hinge datum; 0.6 mm chordwise gap. Hinge tape and travel require inspection.")
                add(f"{prefix}-{side}-{index+1}",f"{prefix.title()} {side} · segment {index+1}",shell,prefix,
                    color="#e8ece0" if is_tail else "#dce5d4",
                    note="Airfoil shell and integral rib candidate; scaled wall offset, seams and sliced density need verification.")
            if not is_tail:
                # Spar follows the same spanwise dihedral and chordwise datum.
                start=root.copy(); end=tip.copy()
                start[0]+=.30*cr; end[0]+=.30*ct
                start[2]+=.015*cr; end[2]+=.015*ct
                end[1]*=sign
                spar=tube(start,end,p["spar_od_m"],p["spar_wall_m"])
                add(f"spar-{side}",f"Carbon spar {side}",spar,"structure","cut-carbon",color="#283934",
                    note="Tube stock selection and center joint adequacy UNKNOWN; cut length is CAD length.",
                    stock={"length_mm":float(np.linalg.norm(np.array(end)-np.array(start)))*1000,
                        "outer_diameter_mm":p["spar_od_m"]*1000,"wall_mm":p["spar_wall_m"]*1000})

    # Fin uses the same section coordinates as the aero model.
    fin_sections=[([.87,0,.07],.15),([.94,0,.24],.075)]
    fin_outer=Solid.make_loft([foil_wire(xyz,c,"naca0012",vertical=True) for xyz,c in fin_sections],ruled=True)
    fin_inner=Solid.make_loft([foil_wire(xyz,c,"naca0012",scale=.86,vertical=True) for xyz,c in fin_sections],ruled=True)
    fin_shell=fin_outer-fin_inner
    rudder_wires=[]
    for xyz,c in fin_sections:
        x=(xyz[0]+.75*c)*1000;z=xyz[2]*1000
        rudder_wires.append(Wire.make_polygon([(x,-100,z),(1200,-100,z),(1200,100,z),(x,100,z)],close=True))
    rudder_mask=Solid.make_loft(rudder_wires,ruled=True)
    add("rudder","Rudder",fin_shell & rudder_mask,"controls",color="#c4d3b8",note="Hinge/travel clearances require inspection.")
    add("fin","Vertical tail",fin_shell-rudder_mask,"tail",note="Rudder hinge datum at 75% local chord.")

    # Circular-section pod, divided into three printable shells.
    fuselage_sections=[(0,.003),(.08,.045),(.22,.055),(.43,.05),(.58,.025),(.66,.008)]
    outer=Solid.make_loft([Wire.make_circle(r*1000,Plane(origin=(x*1000,0,0),z_dir=(1,0,0))) for x,r in fuselage_sections])
    inner=Solid.make_loft([Wire.make_circle(max(.0008,r-.0012)*1000,Plane(origin=(x*1000,0,0),z_dir=(1,0,0))) for x,r in fuselage_sections])
    pod=outer-inner
    # Removable top access panels, each within the print envelope.
    hatch_mask=Box(400,140,100).moved(Location((300,0,78)))
    hatch=pod & hatch_mask
    pod=pod-hatch_mask
    for i in range(2):
        hatch_piece=hatch & Box(200,160,160).moved(Location((200+i*200,0,60)))
        add(f"hatch-{i+1}",f"Top access hatch {i+1}",hatch_piece,"fuselage",color="#c3d2b6",
            note="Install internal components before wing saddle. Positive retention and seam clearances require inspection.")
    for i in range(3):
        cutter=Box(220,180,180).moved(Location((i*220+110,0,0)))
        segment=pod & cutter
        add(f"pod-{i+1}",f"Fuselage shell {i+1}",segment,"fuselage",color="#eef0e5",
            note="Candidate shell with top access opening. Seam joint and local reinforcement checks remain open.")
    add("boom","Carbon tail boom",tube([.54,0,.025],[.99,0,.07],.012,.001),"structure","cut-carbon",color="#263b33",
        stock={"length_mm":math.hypot(450,45),"outer_diameter_mm":12,"wall_mm":1})
    pylon_profile=Wire.make_polygon([(500,-3,35),(602,-3,35),(569,-3,208),(551,-3,208)],close=True)
    from build123d import Face
    pylon=Solid.extrude(Face(pylon_profile),(0,6,0))
    add("motor-pylon","6 mm plywood motor pylon",pylon,"power","cut-plywood",
        note="Cut profile candidate; plywood grain direction, root fastening and load validation remain open.",color="#b59b70",stock={"thickness_mm":6})
    firewall=Solid.make_cylinder(22,4,Plane(origin=(545,0,220),z_dir=(1,0,0)))
    for y,z in [(-8,212),(-8,228),(8,212),(8,228)]:
        firewall=firewall-Solid.make_cylinder(1.6,6,Plane(origin=(544,y,z),z_dir=(1,0,0)))
    add("motor-firewall","Motor firewall candidate",firewall,"power","cut-plywood",color="#b59b70",
        note="Provisional 16 mm square M3 pattern; vendor pattern must be confirmed before cutting.",stock={"thickness_mm":4})
    saddle=(Box(82,86,65)-Box(76,80,70)).moved(Location((342,0,75)))-outer
    add("wing-saddle","Wing mounting saddle",saddle,"structure",note="Connects pod to elevated wing; center spar restraint and fastening need validation.",color="#71946b")
    add("battery-tray","Battery tray candidate",Box(105,43,2).moved(Location((p["battery_x_m"]*1000,0,-24))),"power")
    add("payload-tray","Payload tray candidate",Box(65,45,2).moved(Location((p["payload_x_m"]*1000,0,17))),"payload")
    # COTS geometry is an explicitly labeled envelope, not a fabricated vendor model.
    add("battery","Tattu 1300mAh 3S battery",Box(72,36,22).moved(Location((p["battery_x_m"]*1000,0,-10))),"power","purchase",.122,"#c88149","TAA13003S75X6: manufacturer mass/dimensions. Wire/connector routing still requires clearance checks.")
    add("payload","Mission payload envelope",Box(45,35,30).moved(Location((p["payload_x_m"]*1000,0,35))),"payload","provided",mission["payload_kg"],"#50685e","Payload envelope is an allocation; user hardware not measured.")
    add("esc","Skywalker 20A V2 envelope",Box(45,23,8).moved(Location((420,0,-20))),"power","purchase",.019,"#344a41","Manufacturer dimensions; connector lead envelopes not included.")
    add("motor","EMAX GT2215 motor envelope",Cylinder(14,32,rotation=(0,90,0)).moved(Location((566,0,220))),"power","purchase",.060,"#59655b","Motor mass and dimensions estimated pending drawing.")
    add("propeller","8-inch propeller envelope",Box(5,203.2,12).moved(Location((589,0,220))),"power","purchase",.008,"#273d31","Simplified two-blade envelope; not propeller manufacturing geometry.")
    add("receiver","Receiver envelope",Box(30,18,8).moved(Location((330,0,-20))),"controls","purchase",.008,"#28453a")
    for i,(x,y,z) in enumerate([(.4,-p["span_m"]*.3,.12),(.4,p["span_m"]*.3,.12),(.46,-.018,0),(.46,.018,0)]):
        add(f"servo-{i+1}",f"Control servo {i+1}",Box(23,12,24).moved(Location((x*1000,y*1000,z*1000))),"controls","purchase",.009,"#55745e","Envelope and mass allowance; mount, horn, linkage and torque verification pending.")
    # A mass allowance is explicit and separate from CAD, never silently omitted.
    allowance={"id":"installation-allowance","name":"Wiring, hinges, linkages, fasteners and adhesive allowance",
               "mass_kg":.055,"centroid_m":[.4,0,.04],"quality":"estimated","note":"Detailed selections and installed geometry remain UNKNOWN."}
    total=sum(part["mass_kg"] for part in parts)+allowance["mass_kg"]
    cg=[(sum(part["mass_kg"]*part["centroid_m"][axis] for part in parts)+allowance["mass_kg"]*allowance["centroid_m"][axis])/total for axis in range(3)]
    assembly=Compound(children=shapes,label="OpenV-Albatross-01")
    step_file=cad_dir/"aircraft.step"
    export_step(assembly,str(step_file))
    # Round-trip validates geometry scale/volume, separate from functional verdicts.
    imported=import_step(str(step_file))
    original_volume=sum(float(s.volume) for s in shapes)
    volume_error=abs(float(imported.volume)-original_volume)/max(original_volume,1)
    max_print=max(max(part["dimensions_m"]) for part in parts if part["process"]=="print")
    metadata={"units":{"cad":"mm","mesh":"m","engineering":"SI"},"parameters":p,"parts":parts,
        "mass_properties":{"mass_kg":total,"cg_m":cg,"parts":[{k:v for k,v in part.items() if k not in ("mesh",)} for part in parts],"allowances":[allowance],"materials":MATERIALS},
        "checks":{"max_print_dimension_m":max_print,"invalid_solids":sum(not part["valid"] for part in parts),
                  "step_volume_relative_error":volume_error},
        "coverage":{"complete_manufacturing_definition":False,"assembly_verified":False,
            "open_items":["Control hinge, horn and linkage selection/travel","Fastener and joint details","Battery/hatch positive retention","Vendor motor bolt-pattern confirmation and support loads","Supplier tube and remaining COTS selections","Collision/access/sequence verification","Process calibration and slicing"]}}
    (output_dir/"geometry.json").write_text(json.dumps(metadata,allow_nan=False))
    (output_dir/"design-parameters.json").write_text(json.dumps(p,indent=2))
    return metadata


def cad_output(inputs):
    checks=inputs["cad_checks"]
    admissible=checks["step_volume_relative_error"]<1e-5
    return ToolOutput(metrics={
        "max_print_dimension_m":Measurement(value=checks["max_print_dimension_m"],unit="m",admissible=admissible),
        "invalid_solids":Measurement(value=checks["invalid_solids"],unit="1",admissible=admissible),
    },raw=checks,assumptions=("Topology and axis-aligned build envelope only; printability, thin walls, supports and joints require additional checks.",))


def method():
    return Method("cad","build123d-0.10.0;ocp-7.8.1.1;openv/1",("cad_checks","geometry"),cad_output)
