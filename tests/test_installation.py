import copy

import pytest
from build123d import Box, Location

from openv.installation import collision_pairs, insertion_check, control_power_output


def test_exact_interference_detects_overlap_but_not_contact_or_empty_bounds():
    shapes={'battery':Box(10,10,10), 'tray':Box(12,12,2).moved(Location((0,0,-6))),
            'esc':Box(4,4,4).moved(Location((20,0,0)))}
    result=collision_pairs(shapes, ['battery'])
    assert result['collisions']==[]
    shapes['esc']=Box(4,4,4).moved(Location((4,0,0)))
    bad=collision_pairs(shapes,['battery'])
    assert bad['collisions'][0]['parts']==['battery','esc']
    assert bad['collisions'][0]['volume_mm3']==pytest.approx(48)
    shapes['battery']=Box(10,10,10)-Box(8,8,12)
    shapes['esc']=Box(2,2,2)
    assert collision_pairs(shapes,['battery'])['collisions']==[]


def test_insertion_checks_continuous_path_and_declared_removed_parts():
    shapes={'battery':Box(10,10,10), 'hatch':Box(20,20,1).moved(Location((0,0,23.7)))}
    # Obstacle lies between sample heights; swept solid must catch it.
    bad=insertion_check('battery',shapes,50,removed=[])
    assert bad['collisions'][0]['parts']==['battery','hatch']
    good=insertion_check('battery',shapes,50,removed=['hatch'])
    assert good['collisions']==[]
    assert good['removed']==['hatch']


def test_control_power_requires_sources_and_handles_voltage_and_channel_failure():
    from openv.aircraft import catalog
    inputs={'catalog':[c.model_dump() for c in catalog()]}
    good=control_power_output(inputs)
    assert good.metrics['bec_voltage_compatible'].value==1
    assert good.metrics['channel_margin'].value==1  # five channels incl throttle, six outputs
    assert good.metrics['bec_current_margin_a'].value is None
    bad=copy.deepcopy(inputs)
    next(c for c in bad['catalog'] if c['id']=='esc')['properties']['bec_v']['value']=8
    assert control_power_output(bad).metrics['bec_voltage_compatible'].value==0
    missing=copy.deepcopy(inputs)
    del next(c for c in missing['catalog'] if c['id']=='servo')['properties']['min_voltage_v']
    assert control_power_output(missing).metrics['bec_voltage_compatible'].value is None


def test_incomplete_geometry_coverage_cannot_create_pass():
    from openv.installation import geometry_output
    with pytest.raises(ValueError,match='coverage'):
        geometry_output({'installation_checks':{'available':True,'static':{'checked_pair_count':0},'insertions':[],'propeller':{}}})


def test_stock_requires_exact_section_and_sufficient_cut_length():
    from openv.aircraft import catalog,Parameters,materials_for
    from openv.installation import stock_output
    inputs={'catalog':[c.model_dump() for c in catalog()], 'geometry':Parameters(spar_od_m=.012).model_dump(),
            'mass_properties':{'parts':[{'id':f'spar-{side}','stock':{'length_mm':650}} for side in ('L','R')]}}
    assert stock_output(inputs).metrics['stock_compatible'].value==1
    assert materials_for(catalog(),inputs['geometry'])['carbon']['E_pa']==64e9
    inputs['geometry']['spar_od_m']=.011
    assert stock_output(inputs).metrics['stock_compatible'].value==0
    inputs['geometry']['spar_od_m']=.012
    inputs['mass_properties']['parts'][0]['stock']['length_mm']=1000
    assert stock_output(inputs).metrics['stock_compatible'].value==0


def test_installation_invalidation_and_unrelated_control_power_reuse():
    from openv.aircraft import system,Mission,initial_design
    from openv.installation import methods
    hardware=system(Mission(text='Reference motor glider'))
    ctx={'geometry':initial_design(hardware).parameters,'mass_properties':{'parts':[]},
         'catalog':[c.model_dump() for c in hardware.components], 'interfaces':[i.model_dump() for i in hardware.interfaces],
         'installation_checks':{'available':False}}
    contracts=tuple(c for r in hardware.requirements for c in r.contracts)
    methods={m.name:m for m in methods()}
    before={k:m.fingerprint(ctx,contracts) for k,m in methods.items()}
    ctx['geometry']={**ctx['geometry'],'battery_x_m':.22}
    assert before['installation']!=methods['installation'].fingerprint(ctx,contracts)
    assert before['control-power']==methods['control-power'].fingerprint(ctx,contracts)
    ctx['catalog'][0]['properties']['bec_v']['value']=8
    assert before['control-power']!=methods['control-power'].fingerprint(ctx,contracts)
