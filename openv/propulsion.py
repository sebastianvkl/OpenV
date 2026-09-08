"""APC manufacturer-predicted propeller data, with explicit motor/battery gaps."""
from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path

from openv.core import Measurement, ToolOutput

SOURCE="https://www.apcprop.com/files/PER3_8x4E.dat"


def profile(speed_mps: float, density_kg_m3: float):
    import httpx
    import numpy as np
    path=Path(os.environ.get("OPENV_AUTH_DIR",".openv"))/"PER3_8x4E.dat"
    try:
        if not path.exists():
            response=httpx.get(SOURCE,timeout=20,follow_redirects=True)
            response.raise_for_status()
            if "PROP RPM" not in response.text:raise ValueError("Unexpected propeller dataset")
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(response.text)
        raw=path.read_text()
        data={};rpm=None
        for line in raw.splitlines():
            match=re.search(r"PROP RPM\s*=\s*(\d+)",line)
            if match:rpm=int(match.group(1));data[rpm]=[];continue
            fields=line.split()
            if rpm is not None and len(fields)==15:
                try: values=[float(v) for v in fields]
                except ValueError:continue
                data[rpm].append(values)
        points=[]
        diameter=.2032
        # Only the small speed-specific interpolation slice is included in the
        # evidence package; the full downloaded vendor file stays in local cache.
        for rpm,rows in data.items():
            if not 6000<=rpm<=13000 or not rows:continue
            advance=speed_mps/(rpm/60*diameter)
            j=[r[1] for r in rows]
            if not min(j)<=advance<=max(j):continue
            ct=float(np.interp(advance,j,[r[3] for r in rows]))
            cp=float(np.interp(advance,j,[r[4] for r in rows]))
            points.append({"rpm":rpm,"thrust_n":ct*density_kg_m3*(rpm/60)**2*diameter**4,
                           "shaft_w":cp*density_kg_m3*(rpm/60)**3*diameter**5})
        return {"source":SOURCE,"sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "kind":"manufacturer aerodynamic prediction, not a bench measurement", "speed_mps":speed_mps,
                "density_kg_m3":density_kg_m3,"points":points}
    except Exception as exc:
        return {"source":SOURCE,"points":[],"error":f"{type(exc).__name__}: {exc}"}


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
                     "APC predicted Ct/Cp interpolation at declared airspeed/density. Geometry is still a simplified installed-aircraft model."))

