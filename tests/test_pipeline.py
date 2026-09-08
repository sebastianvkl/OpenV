"""A second, minimal domain proves the public runtime is not aircraft-only."""
from pydantic import BaseModel

from openv.core import (Contract, DesignVersion, HardwareSystem, Measurement,
    Method, Proposal, Requirement, ToolOutput)
from openv.pipeline import Pipeline,write_json


class BracketProposal(BaseModel):
    supported:bool=True
    width_mm:float=12


class BracketEngineer:
    label='Bracket test fixture — no Astra'
    calls=[]
    def define(self,text):return BracketProposal()
    def redesign(self,context):
        assert context['evaluations'][0]['status']=='FAIL'
        assert context['verification_inputs']['width_mm']==12
        assert 'inputs' not in context['evidence'][0]
        assert context['evidence'][0]['output']['metrics']['width_mm']['value']==12
        return Proposal(problem='Part exceeds machine opening',hypothesis='Reduce width',
            changes={'width_mm':9},expected_effect='Fit the 10 mm opening')


class BracketDomain:
    def methods(self):
        return [Method('drawing','1',('width_mm',),lambda x:ToolOutput(
            metrics={'width_mm':Measurement(value=x['width_mm'],unit='mm')},raw=x))]
    def define(self,proposal,text):
        r=Requirement(id='fit',statement='Bracket width at most 10 mm',level='component',owner='bracket',
            contracts=(Contract(id='fit-c',method='drawing',metric='width_mm',operator='<=',threshold=10,
                unit='mm',scope='Nominal drawing dimension, not a physical measurement'),))
        h=HardwareSystem(mission=text,baseline_id='bracket-baseline',domain='test-bracket',
            architecture={'bracket':[]},requirements=(r,),components=(),interfaces=(),scenario={})
        return h,DesignVersion(baseline_id=h.baseline_id,parameters={'width_mm':proposal.width_mm})
    def patch(self,design,changes,experiment_id):
        assert set(changes)=={'width_mm'}
        return DesignVersion(parent_id=design.id,baseline_id=design.baseline_id,
            parameters=changes,experiment_id=experiment_id)
    def build(self,design,scenario,directory):
        write_json(directory/'drawing.json',design.parameters)
        return {'coverage':{'physical_fit_verified':False}}
    def context(self,hardware,design,artifacts):return design.parameters
    def pending_context(self,context,candidate):return candidate.parameters
    def package(self,folder,hardware,design,artifacts):return {}


def test_non_aircraft_public_pipeline_fail_change_invalidate_pass(tmp_path):
    state=Pipeline(tmp_path/'bracket',BracketEngineer(),domain=BracketDomain()).run('A bracket for a 10 mm opening')
    assert state['status']=='complete'
    assert state['gate']=='PASS' # Only the explicitly scoped drawing requirement.
    assert len(state['versions'])==2
    experiment=state['experiments'][0]
    assert experiment['invalidated_evidence']
    assert experiment['actual_effect']['fit']['before']=='FAIL'
    assert experiment['actual_effect']['fit']['after']=='PASS'
    assert (tmp_path/'bracket'/'candidate-package.zip').exists()
