import numpy as np
import pytest

from openv.flight_response import integrate_case


def test_point_mass_trim_and_ballistic_reference():
    balanced=lambda speed:(9.80665,1.)
    cruise=integrate_case(balanced,1,12,1,0,'cruise',duration=3)
    end=cruise['samples'][-1]
    assert end['height_m']==pytest.approx(60,abs=1e-6)
    assert end['north_m']==pytest.approx(36,abs=1e-6)
    assert end['airspeed_mps']==pytest.approx(12,abs=1e-6)
    ballistic=integrate_case(lambda speed:(0,0),1,12,0,0,'cruise',duration=1)
    end=ballistic['samples'][-1]
    assert end['height_m']==pytest.approx(60-9.80665/2,abs=1e-5)
    assert end['north_m']==pytest.approx(12,abs=1e-5)


def test_power_loss_descends_and_wind_translates_ground_track():
    forces=lambda speed:(9.80665*(speed/12)**2,1.*(speed/12)**2)
    cut=integrate_case(forces,1,12,1,2,'power-off',duration=15)
    assert cut['samples'][-1]['height_m']<58
    assert cut['samples'][-1]['thrust_n']==0
    still=integrate_case(forces,1,12,1,2,'cruise',duration=10)
    wind=integrate_case(forces,1,12,1,2,'crosswind',duration=10)
    assert wind['samples'][-1]['east_m']-still['samples'][-1]['east_m']==pytest.approx(40,abs=1e-6)
    assert wind['samples'][-1]['airspeed_mps']==pytest.approx(still['samples'][-1]['airspeed_mps'])


def test_integrator_stops_at_model_speed_boundary():
    result=integrate_case(lambda speed:(9.80665,0),1,12,20,0,'cruise',duration=10)
    assert result['stop_reason']=='maximum_model_speed'
    assert result['samples'][-1]['airspeed_mps']==pytest.approx(22,abs=1e-5)
    assert result['samples'][-1]['time_s']<1


def test_real_geometry_response_is_version_bound_and_not_a_verdict():
    from test_aircraft_visualization import case
    from openv.flight_response import flight_response
    context,evidence=case()
    result=flight_response(context,evidence)
    assert result['status']=='COMPUTED',result.get('reason')
    assert len(result['cases'])==4
    assert result['refinement_endpoint_error_m']<.05
    assert 'metrics' not in result and 'gate' not in result
    assert result['trim_evidence_id']==evidence.id
    changed={**context,'scenario':{**context['scenario'],'altitude_m':2000}}
    assert flight_response(changed,evidence)['status']=='UNKNOWN'
