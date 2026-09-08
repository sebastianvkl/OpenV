"""Public mutations must preserve canonical baselines and protected fields."""
import asyncio
import json

import pytest
from fastapi import HTTPException

from openv import server
from openv.aircraft import Mission, Parameters, initial_design, system
from openv.pipeline import write_json


@pytest.fixture
def parent(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(server, 'active', None)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    hardware=system(Mission(text='Reference camera motor-glider mission'))
    design=initial_design(hardware,Parameters())
    data={'id':'parent', 'system':hardware.model_dump(), 'versions':[design.model_dump()],
          'current_design_id':design.id, 'evidence':[], 'evaluations':[]}
    write_json(tmp_path/'parent'/'run.json',data)
    class Process:
        returncode=0
        async def wait(self):return 0
    async def spawn(*args,**kwargs):return Process()
    monkeypatch.setattr(asyncio,'create_subprocess_exec',spawn)
    return data,tmp_path


def branch(parent, **changes):
    request=server.RunRequest(mission='Different request text must not rewrite the baseline',
        source_run_id='parent',verify_only=True,**changes)
    response=asyncio.run(server.admit_run(request))
    return json.loads((parent[1]/response['id']/'seed.json').read_text())


def test_parameter_branch_preserves_mission_and_records_parent(parent):
    seed=branch(parent,parameter_changes={'span_m':1.7})
    assert seed['definition']['mission']==parent[0]['system']['scenario']
    assert not seed['origin']['mission_amended']
    assert seed['origin']['design_id']==parent[0]['current_design_id']
    assert seed['changes']=={'span_m':1.7}
    from openv.domains import AircraftDomain
    domain=AircraftDomain()
    hardware,design=domain.branch(seed,domain.read_seed(seed))
    assert hardware.model_dump()==parent[0]['system']
    assert design.baseline_id==parent[0]['system']['baseline_id']


def test_numeric_mission_amendment_explicit_and_noops_removed(parent):
    seed=branch(parent,mission_changes={'payload_kg':.3,'cruise_mps':12})
    assert seed['origin']['mission_amended']
    assert seed['changes']=={'mission.payload_kg':.3}
    assert seed['definition']['mission']['text']==parent[0]['system']['mission']
    from openv.domains import AircraftDomain
    domain=AircraftDomain()
    hardware,_=domain.branch(seed,domain.read_seed(seed))
    assert hardware.baseline_id!=parent[0]['system']['baseline_id']
    assert hardware.scenario['payload_kg']==.3
    assert [r.model_dump() for r in hardware.requirements]==list(parent[0]['system']['requirements'])


@pytest.mark.parametrize('changes',[
    {'parameter_changes':{'status':1}},
    {'parameter_changes':{'span_m':9}},
    {'mission_changes':{'text':1}},
    {'parameter_changes':{'spar_od_m':.001}},
])
def test_invalid_or_protected_changes_cannot_launch(parent,changes):
    with pytest.raises(HTTPException) as error:branch(parent,**changes)
    assert error.value.status_code==422
    assert len(list(parent[1].glob('*/run.json')))==1


def test_only_explicit_mission_threshold_is_amended(parent):
    seed=branch(parent,mission_changes={'max_mass_kg':1.5})
    from openv.domains import AircraftDomain
    domain=AircraftDomain(); hardware,_=domain.branch(seed,domain.read_seed(seed))
    for old,new in zip(parent[0]['system']['requirements'],hardware.requirements):
        if old['id']=='mass':assert new.contracts[0].threshold==1.5
        else:assert new.model_dump()==old
