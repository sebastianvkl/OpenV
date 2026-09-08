"""Parametric manufacturing candidates and CAD-derived web meshes.

The canonical geometry is SI. OpenCascade construction/export is explicitly mm;
the viewer receives meters. Vendor envelopes are marked, never fabrication parts.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from openv.aircraft import MATERIALS, Parameters, catalog, wing_sections, tube_stock, materials_for
from openv.core import Measurement, Method, ToolOutput, digest


def build(parameters: dict, mission: dict, output_dir: Path, components=None, interfaces=None) -> dict:
    import aerosandbox as asb
    import numpy as np
    from build123d import (Box, CenterOf, Compound, Cylinder, Location, Plane, Solid,
                          Vector, Wire, export_step, export_stl, import_step)

    p = Parameters.model_validate(parameters).model_dump()
    output_dir.mkdir(parents=True, exist_ok=True)
    cad_dir = output_dir / "cad"
    cad_dir.mkdir(exist_ok=True)
    parts, shapes = [], []
    interface_records=[i.model_dump() if hasattr(i,"model_dump") else i for i in (interfaces or [])]
    installation=next((i["definition"] for i in interface_records if i["id"]=="installation"),None)
    installed=installation is not None and installation.get("revision")=="albatross-installation/2"

    from openv.core import Component
    sourced_parts={c.id:c for c in (Component.model_validate(item) for item in (catalog() if components is None else components))}

    def dimension(component,key,legacy_value):
        value=sourced_parts[component].properties.get(key)
        if value is None:return legacy_value
        if value.unit!="m":raise ValueError(f"{component}.{key} must use meters")
        return float(value.value)

    if installed:
        servo_dims=[dimension("servo",key,default)*1000 for key,default in [("length_m",.023),("width_m",.0115),("height_m",.024)]]
        fraction=.66
        local_chord=p["chord_m"]*(1-(1-p["taper"])*fraction)
        servo_x=.28+.02*fraction+.53*local_chord
        servo_z=.11+.05*p["span_m"]*fraction/2-.008*local_chord-servo_dims[2]/2000
        servo_positions=[(servo_x,-p["span_m"]*fraction/2,servo_z),(servo_x,p["span_m"]*fraction/2,servo_z),(.46,-.021,.012),(.46,.021,.012)]
    else:
        servo_dims=[23,12,24]
        servo_positions=[(.4,-p["span_m"]*.3,.12),(.4,p["span_m"]*.3,.12),(.46,-.018,0),(.46,.018,0)]

    def add(id, label, shape, group, process="print", mass_kg=None, color="#e2e9df", note="", stock=None):
        shape.label = id
        shape_valid = bool(shape.is_valid)
        box = shape.bounding_box()
        dimensions = [float(v)/1000 for v in box.size]
        centroid = [float(v)/1000 for v in shape.center(CenterOf.MASS)]
        density = 650. if process=="cut-plywood" else MATERIALS["carbon" if process == "cut-carbon" else "printed"]["density_kg_m3"]
        mass = float(shape.volume)*1e-9*density if mass_kg is None else mass_kg
        component=sourced_parts.get("servo" if id in ("servo-1","servo-2","servo-3","servo-4") else id)
        if component and "mass_kg" in component.properties and process=="purchase":
            mass=float(component.properties["mass_kg"].value)
        stock_mass=False
        if installed and process=="cut-carbon" and stock:
            component=tube_stock(sourced_parts.values(),stock['outer_diameter_mm']/1000,stock['wall_mm']/1000)
            if component:
                mass=component.properties['linear_mass_kg_m'].value*stock['length_mm']/1000
                stock_mass=True
        verts, faces = shape.tessellate(.5,.15)
        mesh={"positions":[float(n)/1000 for v in verts for n in v],
              "indices":[int(n) for face in faces for n in face]}
        if process == "print":
            export_stl(shape,str(cad_dir/f"{id}.stl"))
        elif process.startswith("cut-"):
            export_step(shape,str(cad_dir/f"{id}.step"))
        parts.append({"id":id,"name":label,"group":group,"process":process,"mass_kg":mass,
            "mass_quality":"computed from sourced linear stock mass" if stock_mass else component.properties["mass_kg"].quality if component and process=="purchase" and "mass_kg" in component.properties else "computed with assumed material density" if mass_kg is None else "allocated; see source catalog",
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
                    if installed and index==0:
                        center_clearance=Solid.make_cylinder((p["spar_od_m"]+.0056)*500,80,
                            Plane(origin=tuple(a*1000-vector/np.linalg.norm(vector)*2),z_dir=tuple(vector)))
                        shell=shell-center_clearance
                if installed and not is_tail:
                    for sx,sy,sz in servo_positions[:2]:
                        if min(ends[0][0][1],ends[1][0][1]) <= sy+(servo_dims[1]+1)/2000 and max(ends[0][0][1],ends[1][0][1]) >= sy-(servo_dims[1]+1)/2000:
                            shell=shell-Box(servo_dims[0]+1,servo_dims[1]+1,servo_dims[2]+2).moved(Location((sx*1000,sy*1000,sz*1000)))
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
    if installed:
        for index,(x,radius) in enumerate(((220,53.8),(440,47.13)),1):
            collar=(inner & Box(14,140,140).moved(Location((x,0,0))))-Solid.make_cylinder(radius-3,18,Plane(origin=(x-9,0,0),z_dir=(1,0,0)))
            collar=collar-hatch_mask
            add(f"pod-collar-{index}",f"Pod seam bonding collar {index}",collar,"fuselage",
                note="14 mm internal backing at pod seam, shaped to nominal inner shell. Bond both halves; adhesive selection, tolerances and joint loads require validation.")
    add("boom","Carbon tail boom",tube([.54,0,.025],[.99,0,.07],.012,.001),"structure","cut-carbon",color="#263b33",
        stock={"length_mm":math.hypot(450,45),"outer_diameter_mm":12,"wall_mm":1})
    pylon_profile=Wire.make_polygon([(500,-3,35),(590,-3,35),(545,-3,195),(545,-3,220),(539,-3,220)] if installed else [(500,-3,35),(602,-3,35),(569,-3,208),(551,-3,208)],close=True)
    from build123d import Face
    pylon=Solid.extrude(Face(pylon_profile),(0,6,0))
    add("motor-pylon","6 mm plywood motor pylon",pylon,"power","cut-plywood",
        note="Cut profile candidate; plywood grain direction, root fastening and load validation remain open.",color="#b59b70",stock={"thickness_mm":6})
    firewall=Solid.make_cylinder(22,4,Plane(origin=(545,0,220),z_dir=(1,0,0)))
    motor_properties=sourced_parts["motor"].properties
    sourced_mount="mount_horizontal_m" in motor_properties and "mount_vertical_m" in motor_properties
    horizontal=dimension("motor","mount_horizontal_m",.016)*500
    vertical=dimension("motor","mount_vertical_m",.016)*500
    holes=[(-horizontal,220),(horizontal,220),(0,220-vertical),(0,220+vertical)] if sourced_mount else [(-8,212),(-8,228),(8,212),(8,228)]
    for y,z in holes:
        firewall=firewall-Solid.make_cylinder(1.6,6,Plane(origin=(544,y,z),z_dir=(1,0,0)))
    if sourced_mount:firewall=firewall-Solid.make_cylinder(3,6,Plane(origin=(544,0,220),z_dir=(1,0,0)))
    add("motor-firewall","Motor firewall candidate",firewall,"power","cut-plywood",color="#b59b70",
        note="Manufacturer GT2215-family 19/16 mm cross pattern; 3.2 mm clearance holes and 6 mm center relief are design choices. Confirm delivered variant, screw engagement and loads." if sourced_mount else "Legacy provisional 16 mm square pattern; vendor pattern unconfirmed.",stock={"thickness_mm":4})
    saddle=(Box(82,86,65)-Box(76,80,70)).moved(Location((342,0,75)))-outer
    if installed:
        (root,cr),(tip,ct)=wing_sections(p)
        root=np.array(root);tip=np.array(tip)
        root[0]+=.30*cr;root[2]+=.015*cr;tip[0]+=.30*ct;tip[2]+=.015*ct
        for sign in (-1,1):
            end=root+(tip-root)*(.075/(p["span_m"]/2));end[1]*=sign
            direction=end-root;direction=direction/np.linalg.norm(direction)
            socket=tube(root-direction*.004,end,p["spar_od_m"]+.0053,.0025)
            saddle=saddle+socket
    add("wing-saddle","Wing mounting saddle with spar sockets" if installed else "Wing mounting saddle",saddle,"structure",note="Connects pod to elevated wing; center spar restraint and fastening need validation.",color="#71946b")
    battery_dims=[dimension("battery",key,default)*1000 for key,default in [("length_m",.072),("width_m",.036),("height_m",.022)]]
    esc_dims=[dimension("esc",key,default)*1000 for key,default in [("length_m",.045),("width_m",.023),("height_m",.008)]]
    receiver_dims=[dimension("receiver",key,default)*1000 for key,default in [("length_m",.030),("width_m",.018),("height_m",.008)]]
    payload_z=p["payload_z_m"] if installed else .035
    esc_x=p["esc_x_m"] if installed else .420
    receiver_x=p["receiver_x_m"] if installed else .330
    esc_z=-.012 if installed else -.020
    receiver_z=-.022 if installed else -.020

    def tray(id,name,x,z,length,width,group):
        if not installed:
            add(id,name,Box(length,width,2).moved(Location((x*1000,0,z*1000))),group)
            return
        # 2 mm base, shallow side lips, and two 12 x 2 mm strap passages.
        base=Box(length,width+8,2)
        for dx in (-length*.30,length*.30):
            for dy in (-width/2-1.5,width/2+1.5):
                base=base-Box(12,2,4).moved(Location((dx,dy,0)))
        for dy in (-width/2-3,width/2+3):
            base=base+Box(length,2,5).moved(Location((0,dy,1.5)))
        base=base.moved(Location((x*1000,0,z*1000)))
        # Legs terminate at the nominal inner pod surface, providing real bonding
        # lands instead of a tray floating in empty space. Adhesive is unmodeled.
        for dx in (-length*.30,length*.30):
            for dy in (-width*.35,width*.35):
                leg_top=z*1000
                leg=Box(5,4,leg_top+90).moved(Location((x*1000+dx,dy,(leg_top-90)/2))) & inner
                base=base+leg
        add(id,name,base,group,
            note="2 mm base, pod-conforming support legs, guide lips and 12 × 2 mm strap passages. Route 10 mm hook-and-loop straps through passages. Bond to pod; bond/strap strength and print tolerances UNKNOWN.")
    tray("battery-tray","Slotted battery retention tray",p["battery_x_m"],-.011-battery_dims[2]/2000 if installed else -.024,battery_dims[0]+12,battery_dims[1]+2,"power")
    tray("payload-tray","Slotted payload retention tray",p["payload_x_m"],payload_z-.016 if installed else .017,65,37 if installed else 45,"payload")
    if installed:
        tray("receiver-tray","Receiver mounting tray",receiver_x,receiver_z-receiver_dims[2]/2000-.001,receiver_dims[0]+6,receiver_dims[1]+2,"controls")
        tray("esc-tray","ESC mounting tray",esc_x,esc_z-esc_dims[2]/2000-.001,esc_dims[0]+6,esc_dims[1]+2,"power")
    add("battery","Tattu 1300mAh 3S battery",Box(*battery_dims).moved(Location((p["battery_x_m"]*1000,0,-10))),"power","purchase",.122,"#c88149","Frozen manufacturer body dimensions; leads and connector routing remain open.")
    add("payload","Mission payload envelope",Box(45,35,30).moved(Location((p["payload_x_m"]*1000,0,payload_z*1000))),"payload","provided",mission["payload_kg"],"#50685e","Payload envelope is an allocation; user hardware not measured.")
    add("esc","Skywalker 20A V2 envelope",Box(*esc_dims).moved(Location((esc_x*1000,0,esc_z*1000))),"power","purchase",.019,"#344a41","Manufacturer dimensions; connector lead envelopes not included.")
    add("motor","EMAX GT2215 motor envelope",Cylinder(dimension("motor","diameter_m",.028)*500,
        dimension("motor","body_length_m",.032)*1000,rotation=(0,90,0)).moved(Location((566,0,220))),
        "power","purchase",.060,"#59655b","Frozen motor body envelope. Shaft adapter, screw engagement and support loads require validation.")
    prop_thickness=dimension("propeller","hub_thickness_m",.005)*1000
    prop_diameter=dimension("propeller","diameter_m",.2032)*1000
    prop_shape=Box(prop_thickness,prop_diameter,12)
    if installed:
        hub=Solid.make_cylinder(dimension("propeller","hub_diameter_m",.02032)*500,prop_thickness,
            Plane(origin=(-prop_thickness/2,0,0),z_dir=(1,0,0)))
        prop_shape=prop_shape+hub
    add("propeller","APC 8 × 4E propeller envelope" if installed else "8-inch propeller envelope",prop_shape.moved(Location((594 if installed else 589,0,220))),"power","purchase",.008,"#273d31","Simplified rigid blade/hub envelope; no blade flex or installed adapter definition. Manufacturer face must face forward in pusher installation; thrust direction and retention require bench validation.")
    add("receiver","RadioMaster ER6 receiver envelope" if installed else "Receiver envelope",Box(*receiver_dims).moved(Location((receiver_x*1000,0,receiver_z*1000))),"controls","purchase",.008,"#28453a","Compatible 2.4 GHz ExpressLRS transmitter required; antenna routing and radio range remain unverified.")
    for i,(x,y,z) in enumerate(servo_positions):
        if installed:
            # An open-top cradle with floor and side walls. Ear/horn geometry is
            # still excluded, explicitly: these are body fit checks only.
            sx,sy,sz=servo_dims
            cradle=Box(sx+4,sy+4,sz+1)-Box(sx+1,sy+1,sz+3).moved(Location((0,0,2)))
            add(f"servo-mount-{i+1}",f"Servo {i+1} body cradle",cradle.moved(Location((x*1000,y*1000,z*1000-.5))),"controls",
                note="0.5 mm nominal body clearance per side; open insertion top. Bond cradle, retain servo by removable band. Ears, horn sweep, band and joint strength remain UNKNOWN.")
        add(f"servo-{i+1}",f"EMAX ES08MA II servo {i+1}" if installed else f"Control servo {i+1}",Box(*servo_dims).moved(Location((x*1000,y*1000,z*1000))),"controls","purchase",.009,"#55745e","Body envelope from frozen catalog; mounting ears, horn and wire lead require detailed clearance verification.")
    from openv.installation import analyze
    installation_checks=analyze(dict(zip((part["id"] for part in parts),shapes)),parts,installation)
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
    roundtrip=roundtrip_checks(parts,imported)
    max_print=max(max(part["dimensions_m"]) for part in parts if part["process"]=="print")
    metadata={"units":{"cad":"mm","mesh":"m","engineering":"SI"},"parameters":p,"parts":parts,
        "installation_checks":installation_checks,"installation":installation,
        "mass_properties":{"mass_kg":total,"cg_m":cg,"parts":[{k:v for k,v in part.items() if k not in ("mesh",)} for part in parts],"allowances":[allowance],"materials":materials_for(sourced_parts.values(),p)},
        "checks":{"max_print_dimension_m":max_print,"invalid_solids":sum(not part["valid"] for part in parts),
                  "step_volume_relative_error":volume_error,**roundtrip},
        "coverage":{"complete_manufacturing_definition":False,"assembly_verified":False,
            "open_items":["Control hinge, horn and linkage selection/travel","Fastener and joint details","Strap, hatch and bonded support retention loads","Delivered motor variant, screw engagement and support loads","Spar cut length/stock match; installed prop adapter and fasteners","Collision/access/sequence verification","Process calibration and slicing"]}}
    (output_dir/"geometry.json").write_text(json.dumps(metadata,allow_nan=False))
    (output_dir/"design-parameters.json").write_text(json.dumps(p,indent=2))
    return metadata


def roundtrip_checks(parts,imported):
    """Translation/scale/identity errors can preserve volume; check them too."""
    from build123d import CenterOf
    expected={part["id"]:part for part in parts}
    children=list(imported.children)
    labels=[part.label for part in children]
    mismatches=len(set(labels)^set(expected))+len(labels)-len(set(labels))
    center_error=0.;bounds_error=0.
    for shape in children:
        if shape.label not in expected:continue
        part=expected[shape.label]
        center=[float(v)/1000 for v in shape.center(CenterOf.MASS)]
        size=[float(v)/1000 for v in shape.bounding_box().size]
        center_error=max(center_error,max(abs(a-b) for a,b in zip(center,part["centroid_m"])))
        bounds_error=max(bounds_error,max(abs(a-b) for a,b in zip(size,part["dimensions_m"])))
    return {"step_part_id_mismatches":mismatches,"step_centroid_max_error_m":center_error,
        "step_bounds_max_error_m":bounds_error,"step_import_valid":bool(imported.is_valid)}


def cad_output(inputs):
    checks=inputs["cad_checks"]
    admissible=(checks["step_volume_relative_error"]<1e-5 and checks.get("step_part_id_mismatches")==0
        and checks.get("step_centroid_max_error_m",float("inf"))<1e-5
        and checks.get("step_bounds_max_error_m",float("inf"))<1e-5 and checks.get("step_import_valid") is True)
    return ToolOutput(metrics={
        "max_print_dimension_m":Measurement(value=checks["max_print_dimension_m"],unit="m",admissible=admissible),
        "invalid_solids":Measurement(value=checks["invalid_solids"],unit="1",admissible=admissible),
    },raw=checks,assumptions=("Topology and axis-aligned build envelope only; printability, thin walls, supports and joints require additional checks.",))


def method():
    return Method("cad","build123d-0.10.0;ocp-7.8.1.1;openv/1",("cad_checks","geometry"),cad_output)
