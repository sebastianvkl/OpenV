"""Exercise the actual OpenAI SDK parser against an offline HTTP transport."""
import json

import httpx2
import pytest
from openai import OpenAI

from openv.aircraft import Mission,Parameters
from openv.engineer import AstraEngineer,MissionProposal


def proposer(always_invalid=False):
    requests=[]
    good=MissionProposal(supported=True,mission=Mission(text='Carry a camera'),parameters=Parameters(),
        rationale='Initial design',uncovered_clauses=[]).model_dump()
    bad={**good,'parameters':{**good['parameters'],'spar_od_m':.016,'chord_m':.15,'taper':.5}}
    def respond(request):
        sent=json.loads(request.content);requests.append(json.loads(sent['input']))
        candidate=bad if len(requests)==1 or always_invalid else good
        return httpx2.Response(200,json={'id':f'resp-{len(requests)}','object':'response',
            'created_at':0,'model':'test-model','status':'completed','usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2},
            'output':[{'id':'msg-test','type':'message','role':'assistant','status':'completed',
                'content':[{'type':'output_text','text':json.dumps(candidate),'annotations':[]}]}]})
    engineer=AstraEngineer.__new__(AstraEngineer);engineer.calls=[];engineer.model='test-model'
    engineer.client=OpenAI(api_key='unit-test-only',base_url='https://openv-test.invalid/v1',
        http_client=httpx2.Client(transport=httpx2.MockTransport(respond)))
    return engineer,requests


def test_actual_geometry_rejection_returns_to_proposer_without_silent_repair():
    engineer,requests=proposer()
    result=engineer.define('Carry a camera')
    assert len(requests)==2
    assert requests[1]['original_mission']==requests[0]['original_mission']
    assert 'Spar does not fit' in str(requests[1]['validation_errors'])
    assert engineer.calls[0]['response_id']=='resp-1'
    assert engineer.calls[0]['validation']=='rejected'
    assert result.parameters.spar_od_m==Parameters().spar_od_m


def test_repeated_invalid_proposals_stop_after_three_attempts():
    engineer,requests=proposer(always_invalid=True)
    with pytest.raises(ValueError,match='exhausted three'):engineer.define('Carry a camera')
    assert len(requests)==3
    assert all(call['validation']=='rejected' for call in engineer.calls)
