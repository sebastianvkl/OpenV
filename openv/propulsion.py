"""Measured propeller data with explicit installed motor/battery coverage gaps."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from openv.core import Measurement, ToolOutput

SOURCE="https://m-selig.ae.illinois.edu/props/volume-1/propDB-volume-1.html"
DATASETS=[
    (4001,"apce_8x4_2792rd_4001.txt"),
    (5011,"apce_8x4_2793rd_5011.txt"),
    (6007,"apce_8x4_2794rd_6007.txt"),
    (7011,"apce_8x4_2796rd_7011.txt"),
    (7025,"apce_8x4_2795rd_7025.txt"),
]


def profile(speed_mps: float, density_kg_m3: float):
    import httpx
    import numpy as np
    cache=Path(os.environ.get("OPENV_AUTH_DIR",".openv"))/"propeller-data"
    points=[];sources=[];errors=[]
    diameter=.2032
    for rpm,name in DATASETS:
        url="https://m-selig.ae.illinois.edu/props/volume-1/data/"+name
        path=cache/name
        try:
            if not path.exists():
                response=httpx.get(url,timeout=10,follow_redirects=True)
                response.raise_for_status()
                if not response.text.strip().startswith("J"):raise ValueError("Unexpected propeller dataset")
                cache.mkdir(parents=True,exist_ok=True);path.write_text(response.text)
            raw=path.read_text()
            rows=np.loadtxt(path,skiprows=1)
            if rows.ndim!=2 or rows.shape[1]!=4 or not np.isfinite(rows).all():raise ValueError("Invalid measurement table")
            if not np.all(np.diff(rows[:,0])>0):raise ValueError("Advance ratio must increase")
            sources.append({"url":url,"sha256":hashlib.sha256(raw.encode()).hexdigest(),"rpm":rpm})
            advance=speed_mps/(rpm/60*diameter)
            if not rows[0,0]<=advance<=rows[-1,0]:continue
            ct=float(np.interp(advance,rows[:,0],rows[:,1]))
            cp=float(np.interp(advance,rows[:,0],rows[:,2]))
            if ct<=0 or cp<=0:continue
            points.append({"rpm":rpm,"advance_ratio":advance,"ct":ct,"cp":cp,
                "thrust_n":ct*density_kg_m3*(rpm/60)**2*diameter**4,
                "shaft_w":cp*density_kg_m3*(rpm/60)**3*diameter**5})
        except Exception as exc:errors.append({"url":url,"error":f"{type(exc).__name__}: {exc}"})
    return {"source":SOURCE,"datasets":sources,"errors":errors,
        "kind":"UIUC wind-tunnel measurements: APC Thin Electric 8x4, volume 1 version 3",
        "speed_mps":speed_mps,"density_kg_m3":density_kg_m3,"points":points}


def output(inputs):
    import numpy as np
    from openv.aircraft import aero_output
    aero=aero_output(inputs)
    drag=aero.metrics.get("drag_n")
    profile=inputs["propeller_profile"]
    points=profile["points"]
    unknown="Motor efficiency/load map, installed propwash, battery discharge and mission reserves are not validated."
    if not drag or not drag.admissible or len(points)<2:
        return ToolOutput(metrics={"endurance_min":Measurement(value=None,unit="min",admissible=False,reason="Missing admissible trim or propeller data")},raw={"profile":profile})
    points=sorted(points,key=lambda p:p["thrust_n"])
    if not points[0]["thrust_n"]<=drag.value<=points[-1]["thrust_n"]:
        return ToolOutput(metrics={"endurance_min":Measurement(value=None,unit="min",admissible=False,reason="Required thrust outside available propeller interpolation range")},raw={"required_thrust_n":drag.value,"profile":profile})
    thrust=[p["thrust_n"] for p in points]
    shaft=float(np.interp(drag.value,thrust,[p["shaft_w"] for p in points]))
    rpm=float(np.interp(drag.value,thrust,[p["rpm"] for p in points]))
    # Exploratory range only. Missing motor evidence cannot become an endurance PASS.
    battery=next(c for c in inputs["catalog"] if c["id"]=="battery")["properties"]
    energy=battery["nominal_v"]["value"]*battery["capacity_ah"]["value"]*.8
    bounds=[energy/(shaft/eta+2)*60 for eta in [.65,.85]]
    return ToolOutput(metrics={"endurance_min":Measurement(value=sum(bounds)/2,unit="min",admissible=False,reason=unknown)},
        raw={"required_thrust_n":drag.value,"required_shaft_w":shaft,"rpm":rpm,"endurance_estimate_min":bounds,
             "assumed_motor_esc_efficiency":[.65,.85],"assumed_usable_energy_wh":energy,"assumed_auxiliary_w":2,"profile":profile},
        assumptions=(unknown,"Energy estimate assumes 80% nominal battery energy and 2 W auxiliary load; cruise-only, no launch/climb reserve.",
                     "UIUC measured Ct/Cp interpolation at declared airspeed/density; no extrapolation beyond measured RPM/J. Geometry is still a simplified installed-aircraft model."))

