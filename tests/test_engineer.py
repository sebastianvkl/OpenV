import json
from types import SimpleNamespace

import pytest

from openv.aircraft import Mission,Parameters
from openv.engineer import AstraEngineer,MissionProposal


def proposer(always_invalid=False):
    requests=[]
    good=MissionProposal(supported=True,mission=Mission(text='Carry a camera'),parameters=Parameters(),
        rationale='Initial design',uncovered_clauses=[]).model_dump()
    bad={**good,'parameters':{**good['parameters'],'spar_od_m':.016,'chord_m':.15,'taper':.5}}
    class Response:
        def __init__(self,n):self.n=n;self.proposal=bad if n==1 or always_invalid else good
        def json(self):return {'id':f'response-{self.n}','model':'test-model','usage':{},
            'output':[{'content':[{'type':'output_text','text':json.dumps(self.proposal)}]}]}
        def parse(self):return SimpleNamespace(output_parsed=MissionProposal.model_validate(self.proposal))
    def parse(**kwargs):requests.append(json.loads(kwargs['input']));return Response(len(requests))
    engineer=AstraEngineer.__new__(AstraEngineer);engineer.calls=[];engineer.model='test-model'
    engineer.client=SimpleNamespace(responses=SimpleNamespace(with_raw_response=SimpleNamespace(parse=parse)))
    return engineer,requests


def test_actual_geometry_rejection_returns_to_proposer_without_silent_repair():
    engineer,requests=proposer()
    result=engineer.define('Carry a camera')
    assert len(requests)==2
    assert requests[1]['original_mission']==requests[0]['original_mission']
    assert 'Spar does not fit' in str(requests[1]['validation_errors'])
    assert engineer.calls[0]['response_id']=='response-1'
    assert engineer.calls[0]['validation']=='rejected'
    assert result.parameters.spar_od_m==Parameters().spar_od_m


def test_repeated_invalid_proposals_stop_after_three_attempts():
    engineer,requests=proposer(always_invalid=True)
    with pytest.raises(ValueError,match='exhausted three'):engineer.define('Carry a camera')
    assert len(requests)==3
    assert all(call['validation']=='rejected' for call in engineer.calls)
