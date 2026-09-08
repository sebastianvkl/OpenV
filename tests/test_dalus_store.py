import asyncio
import copy
import json
from contextlib import asynccontextmanager

import pytest

from openv import dalus_store
from openv.aircraft import Mission, system, initial_design
from openv.dalus_store import DalusStore


class MemoryMCP:
    """Stateful remote double: records identities/history across store lifetimes."""
    def __init__(self):
        self.collections={k:{} for k in ['parts','variables','ports','connections','requirements','testCases','tradeStudies']}
        self.created=0
        self.actions=[]

    async def call(self,connection,name,args):
        if name=='createModel':
            self.created+=1
            return {'model':{'id':'one-aircraft'}}
        if name=='searchModel':
            return {'model':{key:copy.deepcopy(list(self.collections[key].values())[args.get('offset',0):args.get('offset',0)+7]) for key in args['collections']}}
        assert name=='writeModelChanges'
        kinds={'Part':'parts','Variable':'variables','Port':'ports','Connection':'connections','Requirement':'requirements','TestCase':'testCases','TradeStudy':'tradeStudies'}
        for operation in args['operations']:
            action=operation['operation'];fields=copy.deepcopy(operation['input'])
            self.actions.append((action,fields))
            collection=self.collections[kinds[action[3:] if action.startswith('add') else action[6:]]]
            if action.startswith('add'):
                fields.setdefault('id',f'{action}-{len(collection)}')
                assert fields['id'] not in collection
                collection[fields['id']]={}
            else:
                assert fields['id'] in collection
            if 'expression' in fields:fields['value']=json.loads(fields['expression'])
            collection[fields['id']].update(fields)
        return {'failedOperations':[]}


@pytest.fixture
def remote(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENV_DALUS_MAPPING',str(tmp_path/'shared.json'))
    monkeypatch.delenv('OPENV_DALUS_MODEL_ID',raising=False)
    remote=MemoryMCP()
    @asynccontextmanager
    async def session():yield remote
    monkeypatch.setattr(dalus_store,'session',session)
    async def call(self,connection,name,args):return await remote.call(connection,name,args)
    monkeypatch.setattr(DalusStore,'call',call)
    return remote


def test_second_run_reuses_model_and_elements_preserving_test_history(tmp_path,remote):
    hardware=system(Mission(text="RC glider"));design=initial_design(hardware)
    first=DalusStore(tmp_path/'run-1','team')
    first.create_system(hardware,design)
    ids=copy.deepcopy(first.map)
    case_id=next(iter(ids['test_cases'].values()))
    remote.collections['testCases'][case_id]['runs']=[{'id':'historic','runNumber':1,'status':'Passed','notes':'version-bound evidence'}]
    first.close()
    start=len(remote.actions)
    changed=system(Mission(text="RC glider",payload_kg=.2));next_design=initial_design(changed)
    second=DalusStore(tmp_path/'run-2','team')
    second.create_system(changed,next_design)
    assert remote.created==1
    for key in ['parts','nodes','variables','requirements','test_cases']:
        assert second.map[key]==ids[key]
    assert not any(action.startswith('add') and action!='addTradeStudy' for action,_ in remote.actions[start:])
    assert remote.collections['testCases'][case_id]['runs'][0]['id']=='historic'
    assert any(rows and rows[0]['id']=='historic' for rows in second.map['test_runs'].values())
    assert (tmp_path/'run-2/dalus-before-update.json').exists()
    # Invalidation precedes every new baseline value.
    actions=remote.actions[start:]
    first_input=next(i for i,(action,fields) in enumerate(actions) if action=='updateVariable' and fields.get('name')=='payload_kg')
    invalidated={fields['id'] for action,fields in actions[:first_input] if action=='updateRequirement' and fields.get('status')=='In Progress'}
    assert invalidated==set(ids['requirements'].values())
    second.close()


def test_existing_model_without_mapping_is_rejected_and_writer_lock_is_exclusive(tmp_path,remote):
    with pytest.raises(ValueError,match='Import'):
        DalusStore(tmp_path/'a','team',model_id='existing')
    first=DalusStore(tmp_path/'a','team')
    with pytest.raises(RuntimeError,match='Another process'):
        DalusStore(tmp_path/'b','team')
    first.close()
    second=DalusStore(tmp_path/'b','team');second.close()


def test_missing_mapped_parts_blocks_without_creating_replacements(tmp_path,remote):
    hardware=system(Mission(text="RC glider"));design=initial_design(hardware)
    first=DalusStore(tmp_path/'a','team');first.create_system(hardware,design);first.close()
    remote.collections['parts'].pop(next(iter(remote.collections['parts'])))
    count=len(remote.actions)
    second=DalusStore(tmp_path/'b','team')
    with pytest.raises(RuntimeError,match='missing'):
        second.create_system(hardware,design)
    assert len(remote.actions)==count
    assert remote.created==1
    second.close()
