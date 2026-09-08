"""Scoped, deterministic installation checks. Geometry is in millimeters.

These checks do not prove retention, structural strength, wire routing or flight.
A continuous translated box envelope is conservative for straight insertion.
"""
from __future__ import annotations

import math

from openv.core import Measurement, Method, ToolOutput

REVISION = 'albatross-installation/2'
VOLUME_TOLERANCE_MM3 = .01


def collision_pairs(shapes, moving_ids, excluded=()):
    excluded={tuple(sorted(pair)) for pair in excluded}
    checked=[];collisions=[];seen=set()
    for name in moving_ids:
        a=shapes[name]
        if not a.is_valid: raise ValueError(f'Invalid collision solid: {name}')
        for other,b in shapes.items():
            pair=tuple(sorted((name,other)))
            if name==other or pair in excluded or pair in seen:continue
            seen.add(pair)
            if not b.is_valid: raise ValueError(f'Invalid collision solid: {other}')
            aa,bb=a.bounding_box(),b.bounding_box()
            overlaps=all(min(list(aa.max)[i],list(bb.max)[i])-max(list(aa.min)[i],list(bb.min)[i])>1e-7 for i in range(3))
            volume=0.
            if overlaps:
                common=a & b
                if common is not None:
                    volume=abs(float(common.volume))
                    if not math.isfinite(volume):raise ValueError('Nonfinite intersection')
            row={'parts':[name,other],'volume_mm3':volume}
            checked.append(row)
            if volume>VOLUME_TOLERANCE_MM3:collisions.append(row)
    return {'checked_pair_count':len(checked),'checked_pairs':checked,'collisions':collisions,
            'volume_tolerance_mm3':VOLUME_TOLERANCE_MM3}


def insertion_check(part_id,shapes,travel_mm,removed):
    from build123d import Box,Location
    box=shapes[part_id].bounding_box()
    size=box.size;center=(box.min+box.max)*.5
    if not math.isfinite(travel_mm) or travel_mm<=0:raise ValueError('Positive insertion travel required')
    sweep=Box(size.X,size.Y,size.Z+travel_mm).moved(Location((center.X,center.Y,center.Z+travel_mm/2)))
    obstacles={key:shape for key,shape in shapes.items() if key not in removed and key!=part_id}
    result=collision_pairs({part_id:sweep,**obstacles},[part_id])
    return {**result,'part_id':part_id,'direction':[0,0,1],'travel_mm':travel_mm,
            'removed':list(removed),'envelope':'Continuous translated axis-aligned bounding box',
            'bounds_mm':{'min':list(box.min),'max':[box.max.X,box.max.Y,box.max.Z+travel_mm]}}


def analyze(shapes,parts,interface):
    if interface is None:return {'available':False,'reason':'No versioned installation interface in this baseline'}
    from build123d import Plane,Solid
    indexed={p['id']:p for p in parts}
    purchased=[p['id'] for p in parts if p['process'] in ('purchase','provided') and p['id']!='propeller']
    static=collision_pairs(shapes,purchased)
    prop=indexed['propeller'];bounds=shapes['propeller'].bounding_box()
    radius=prop['component']['properties']['diameter_m']['value']*500
    # Hub thickness conservatively bounds blade axial extent; flex is excluded.
    disk=Solid.make_cylinder(radius,bounds.size.X,Plane(origin=(bounds.min.X,0,prop['centroid_m'][2]*1000),z_dir=(1,0,0)))
    prop_obstacles={k:v for k,v in shapes.items() if k not in ('propeller',)}
    sweep=collision_pairs({'propeller':disk,**prop_obstacles},['propeller'])
    distances=[{'part_id':name,'clearance_mm':float(disk.distance_to(shape))} for name,shape in prop_obstacles.items()]
    if not distances or any(not math.isfinite(x['clearance_mm']) for x in distances):raise ValueError('Invalid propeller clearance')
    sweep.update(min_clearance_mm=min(x['clearance_mm'] for x in distances),clearances=distances,
                 radius_mm=radius,axial_thickness_mm=bounds.size.X,center_m=prop['centroid_m'])
    # Install the internal electronics with wing, saddle and access covers absent.
    # All other modeled parts remain obstacles, including trays and each other.
    removed=[p['id'] for p in parts if p['id'].startswith(('wing-','aileron-','spar-','hatch-')) or p['id']=='wing-saddle']
    insertions=[insertion_check(name,shapes,180,removed) for name in ('battery','payload','receiver','esc')]
    return {'available':True,'revision':REVISION,'interface':interface,'static':static,'propeller':sweep,
            'insertions':insertions,'scope':'Modeled COTS/payload solids and declared assembly order only',
            'unverified':['Flexible wiring and connectors','Fastener/tool access','Adhesive and joint strength',
                          'Servo horns/linkages and control travel','Printed tolerances and process','Dynamic propeller flex']}


def geometry_output(inputs):
    data=inputs['installation_checks']
    if not data.get('available'):return ToolOutput(metrics={},raw=data)
    if (data['static'].get('checked_pair_count',0)<=0
        or len(data['static'].get('checked_pairs',[]))!=data['static']['checked_pair_count']
        or {row['part_id'] for row in data.get('insertions',[])}!={'battery','payload','receiver','esc'}
        or any(row.get('checked_pair_count',0)<=0 for row in data['insertions'])
        or not data['propeller'].get('clearances')):
        raise ValueError('Incomplete installation check coverage')
    measured=[row['clearance_mm'] for row in data['propeller']['clearances']]
    if any(not math.isfinite(v) or v<0 for v in measured) or abs(min(measured)-data['propeller']['min_clearance_mm'])>1e-7:
        raise ValueError('Invalid propeller distance summary')
    insertion_count=sum(len(row['collisions']) for row in data['insertions'])
    return ToolOutput(metrics={
        'component_collision_count':Measurement(value=len(data['static']['collisions']),unit='1'),
        'propeller_clearance_mm':Measurement(value=data['propeller']['min_clearance_mm'],unit='mm'),
        'insertion_collision_count':Measurement(value=insertion_count,unit='1')},raw=data,
        assumptions=('OpenCascade solid intersections; contact <=0.01 mm³ is numerical tolerance, not a fit allowance.',
                     'Rigid nominal envelopes. No wiring, thermal expansion, blade flex or manufacturing tolerance validation.',
                     'Continuous +Z insertion box with explicitly removed wing, spar, saddle and hatch parts; not in-service battery access.'))


def control_power_output(inputs):
    parts={c['id']:c['properties'] for c in inputs['catalog']}
    def sourced(id,key,unit):
        prop=parts.get(id,{}).get(key)
        if not prop or prop['unit']!=unit or prop['quality'] not in ('sourced','measured'):return None
        value=prop['value']
        return float(value) if isinstance(value,(int,float)) and math.isfinite(value) else None
    supply=sourced('esc','bec_v','V')
    ranges={id:[sourced(id,'min_voltage_v','V'),sourced(id,'max_voltage_v','V')] for id in ('servo','receiver')}
    known=supply is not None and all(v is not None for r in ranges.values() for v in r)
    voltage=int(all(lo<=supply<=hi for lo,hi in ranges.values())) if known else None
    available=sourced('receiver','channels','1')
    quantity=parts.get('servo',{}).get('quantity',{}).get('value')
    required=quantity+1 if isinstance(quantity,(int,float)) else None
    return ToolOutput(metrics={
        'bec_voltage_compatible':Measurement(value=voltage,unit='1',reason='Sourced BEC output and both load voltage ranges required'),
        'channel_margin':Measurement(value=available-required if available is not None and required is not None else None,unit='1',reason='Receiver outputs minus one throttle plus each independent servo'),
        'bec_current_margin_a':Measurement(value=None,unit='A',reason='Simultaneous servo/receiver current and BEC transient/thermal behavior not measured')},
        raw={'bec_voltage_v':supply,'load_ranges_v':ranges,'available_channels':available,'required_channels':required},
        assumptions=('Nominal sourced voltage ranges only; supply transients, stall current and installed wiring remain UNKNOWN.',
                     'Two independent ailerons, elevator, rudder and throttle require five PWM outputs.'))


def methods():
    return [Method('tube-stock','sourced-section-fit/1',('geometry','mass_properties','catalog'),stock_output),Method('installation','ocp-solid-installation/2',('geometry','installation_checks','catalog','interfaces'),geometry_output),
            Method('control-power','sourced-control-power/1',('catalog',),control_power_output)]


def stock_output(inputs):
    from openv.aircraft import tube_stock
    p=inputs['geometry'];stock=tube_stock(inputs['catalog'],p['spar_od_m'],p['spar_wall_m'])
    parts=inputs['mass_properties']['parts']
    lengths=[part['stock']['length_mm']/1000 for part in parts if part['id'].startswith('spar-')]
    options=[{'id':c['id'],'part_number':c.get('part_number'),'properties':c['properties']} for c in inputs['catalog'] if c['id'].startswith('tube-')]
    if not options:return ToolOutput(metrics={},raw={'reason':'No sourced stock alternatives in this baseline'})
    length=stock['properties']['length_m']['value'] if stock else None
    fits=stock is not None and len(lengths)==2 and all(0<cut+.003<=length for cut in lengths)
    return ToolOutput(metrics={'stock_compatible':Measurement(value=int(fits),unit='1')},
        raw={'selected_stock':stock,'cut_lengths_m':lengths,'kerf_allowance_m':.003,'available_options':options},
        assumptions=('One 1 m stock length per spar half, with 3 mm cutting allowance. Nominal dimensions only.',
                     'Material straightness, delivered tolerances, compression, joints and torsion require validation.'))
