"""Computed 3D point-mass responses at fixed alpha, not attitude/flight validation.

AeroSandbox supplies geometry-based lift/drag and the point-mass equations.
SciPy integrates the equations. Prescribed thrust and ideal attitude tracking
are explicit assumptions. No result from this diagnostic grants PASS.
"""
from __future__ import annotations

import inspect
import math

from openv.core import ENGINEERING_REVISION,digest


CASES={'cruise':'Trim hold','power-off':'Power off at 5 s','bank':'30° bank command','crosswind':'4 m/s crosswind'}


def integrate_case(forces,mass,speed,thrust,alpha,case,duration=25,max_step=.1):
    import aerosandbox as asb
    import numpy as np
    from scipy.integrate import solve_ivp
    if case not in CASES or not all(math.isfinite(x) for x in (mass,speed,thrust,alpha,duration)) or mass<=0 or not 8<=speed<=22:
        raise ValueError('Invalid point-mass response inputs')
    wind_east=4. if case=='crosswind' else 0.
    def commands(t):
        return (0. if case=='power-off' and t>=5 else thrust,
                math.radians(30)*min(1,max(0,t-5)) if case=='bank' else 0.)
    def dynamics(t,state):
        north,east,z,v,gamma,heading=state
        command,bank=commands(t)
        # Guard only solver trial stages outside terminal model boundaries.
        # Published states end at the speed event, never at extrapolated forces.
        lift,drag=forces(float(np.clip(v,8,22)))
        d=asb.DynamicsPointMass3DSpeedGammaTrack(mass_props=asb.MassProperties(mass=mass),
            x_e=north,y_e=east,z_e=z,speed=max(v,1),gamma=gamma,track=heading,alpha=alpha,bank=bank)
        d.add_force(Fx=command-drag,Fz=-lift,axes='wind')
        d.add_gravity_force(g=9.80665)
        values=d.state_derivatives()
        return [float(values['x_e']),float(values['y_e'])+wind_east,float(values['z_e']),
                float(values['speed']),float(values['gamma']),float(values['track'])]
    def ground(t,y):return -y[2]
    def slow(t,y):return y[3]-8
    def fast(t,y):return 22-y[3]
    def steep(t,y):return math.radians(60)-abs(y[4])
    events=[ground,slow,fast,steep]
    for event in events:event.terminal=True;event.direction=-1
    result=solve_ivp(dynamics,(0,duration),[0,0,-60,speed,0,0],rtol=1e-7,atol=1e-9,
        max_step=max_step,t_eval=np.linspace(0,duration,round(duration*10)+1),events=events)
    if not result.success or not np.isfinite(result.y).all():raise ValueError('Nonfinite or incomplete ODE solution')
    samples=list(zip(result.t,result.y.T));stop='duration_complete'
    for i,times in enumerate(result.t_events):
        if len(times):
            stop=['flat_ground_contact','minimum_model_speed','maximum_model_speed','flight_path_model_limit'][i]
            if not samples or abs(samples[-1][0]-times[0])>1e-8:samples.append((times[0],result.y_events[i][0]))
    output=[]
    for t,state in samples:
        north,east,z,v,gamma,heading=map(float,state)
        force,bank=commands(t);lift,drag=forces(float(np.clip(v,8,22)))
        output.append({'time_s':float(t),'north_m':north,'east_m':east,'height_m':-z,'airspeed_mps':v,
            'gamma_rad':gamma,'heading_rad':heading,'pitch_rad':gamma+math.radians(alpha),'bank_rad':bank,
            'thrust_n':force,'lift_n':lift,'drag_n':drag,'load_factor':lift/(mass*9.80665)})
    return {'id':case,'name':CASES[case],'samples':output,'stop_reason':stop,'duration_s':output[-1]['time_s'],
            'height_change_m':output[-1]['height_m']-60,'wind_east_mps':wind_east,
            'solver':{'method':'SciPy RK45','rtol':1e-7,'atol':1e-9,'max_step_s':max_step,'evaluations':result.nfev}}


def flight_response(context,aero_evidence):
    import aerosandbox as asb
    import scipy
    import numpy as np
    from openv.aircraft import airplane
    inputs={k:context[k] for k in ('geometry','mass_properties','scenario')}
    result={'kind':'3D point-mass flight response','status':'UNKNOWN','design_id':aero_evidence.design_id,
        'baseline_id':aero_evidence.baseline_id,'trim_evidence_id':aero_evidence.id,'trim_output_hash':aero_evidence.output_hash,
        'engineering_revision':ENGINEERING_REVISION,'source_hash':digest(inspect.getsource(flight_response)+inspect.getsource(integrate_case)),
        'method':f'AeroSandbox AeroBuildup + DynamicsPointMass3DSpeedGammaTrack/{asb.__version__}; SciPy {scipy.__version__} RK45',
        'inputs':inputs,'units':{'positions':'m','time':'s','angles':'rad','forces':'N'},
        'assumptions':['Point mass with ideal tracking of recorded alpha and commanded bank; no pitch/roll/yaw inertia, controller or actuator dynamics.',
            'Prescribed thrust equals trim drag until the power-off command; not measured installed motor/propeller performance.',
            'Lift/drag interpolated from this geometry at fixed trim alpha/elevator over 8–22 m/s, at constant mission atmospheric density.',
            'Initial diagnostic height is 60 m above a flat reference plane, independent of atmospheric altitude. Scenery is not collision geometry.',
            'Crosswind is uniform advection from the start, not a gust or turbulence simulation.',
            'Stops at the force-table speed bounds, 60° flight-path angle or flat ground. No stall, post-stall or physical flight claim.']}
    result['fingerprint']=digest({'inputs':inputs,'trim':aero_evidence.output_hash,'source':result['source_hash'],'revision':ENGINEERING_REVISION,'method':result['method']})
    if digest(inputs)!=digest(aero_evidence.inputs) or digest(aero_evidence.output)!=aero_evidence.output_hash:
        result['reason']='Trim evidence hash or inputs do not match this design';return result
    raw=aero_evidence.output.raw
    if raw.get('trim_residual',1)>=.01 or abs(raw.get('alpha_deg',99))>8 or abs(raw.get('elevator_deg',99))>25:
        result['reason']='No trim within the reviewed force-model envelope';return result
    try:
        craft=airplane(inputs['geometry'],raw['cg_m'],raw['elevator_deg'])
        speeds=sorted(set([float(v) for v in range(8,23)]+[float(inputs['scenario']['cruise_mps'])]))
        atmosphere=asb.Atmosphere(altitude=inputs['scenario']['altitude_m'])
        table=[]
        for v in speeds:
            values=asb.AeroBuildup(airplane=craft,op_point=asb.OperatingPoint(velocity=v,alpha=raw['alpha_deg'],atmosphere=atmosphere)).run()
            table.append({'speed_mps':v,'lift_n':float(np.asarray(values['L']).ravel()[0]),'drag_n':float(np.asarray(values['D']).ravel()[0])})
        if any(not math.isfinite(row[k]) or row[k]<=0 for row in table for k in row):raise ValueError('Invalid force table')
        def forces(v):return tuple(float(np.interp(v,speeds,[row[key] for row in table])) for key in ('lift_n','drag_n'))
        cases=[integrate_case(forces,inputs['mass_properties']['mass_kg'],inputs['scenario']['cruise_mps'],raw['D'],raw['alpha_deg'],case) for case in CASES]
        # Independent time-step refinement exposes numerical disagreement.
        fine=integrate_case(forces,inputs['mass_properties']['mass_kg'],inputs['scenario']['cruise_mps'],raw['D'],raw['alpha_deg'],'power-off',max_step=.05)
        coarse=next(c for c in cases if c['id']=='power-off')
        error=max(abs(coarse['samples'][-1][key]-fine['samples'][-1][key]) for key in ('north_m','east_m','height_m'))
        if error>.05:raise ValueError('Trajectory endpoint changed by more than 5 cm under time-step refinement')
        result.update(status='COMPUTED',force_table=table,cases=cases,refinement_endpoint_error_m=error)
    except Exception as exc:result['reason']=f'{type(exc).__name__}: {exc}'
    return result
