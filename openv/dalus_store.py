"""Typed engineering records mapped to discovered Dalus MCP operations.

The local mapping contains IDs/cache only. Every state transition is committed to
Dalus and read back before the pipeline can treat it as authoritative.
"""
from __future__ import annotations

import asyncio
import copy
import fcntl
import html
import json
import os
from pathlib import Path
from uuid import uuid4

from openv.core import digest
from openv.dalus import session


def uuid():
    return str(uuid4())


def unpack(result):
    if result.isError:
        raise RuntimeError("Dalus MCP operation failed: "+" ".join(c.text for c in result.content if c.type=="text")[:1500])
    if result.structuredContent is not None:
        return result.structuredContent
    for content in result.content:
        if content.type=="text":
            return json.loads(content.text)
    raise RuntimeError("Dalus returned no structured engineering response")


def op(operation, **inputs):
    return {"operation":operation,"input":inputs}


class DalusStore:
    def __init__(self, run_directory: Path, team_id: str, model_id: str | None = None):
        self.directory=run_directory
        self.team_id=team_id
        self.shared_path=Path(os.environ.get("OPENV_DALUS_MAPPING",str(Path(os.environ.get("OPENV_AUTH_DIR",".openv"))/"dalus-system.json")))
        self.shared_path.parent.mkdir(parents=True,exist_ok=True)
        self._lock=self.shared_path.with_suffix(".lock").open("a")
        try:fcntl.flock(self._lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError("Another process is updating this Dalus system; retry after it completes")
        configured=model_id or os.environ.get("OPENV_DALUS_MODEL_ID")
        self.map={"model_id":configured,"parts":{},"nodes":{},"variables":{},"requirements":{},"test_cases":{},"test_runs":{},"commit":"incomplete","fixed_variables":{}}
        if self.shared_path.exists():
            saved=json.loads(self.shared_path.read_text())
            if configured and saved.get("model_id")!=configured:raise ValueError("Configured Dalus model does not match persistent mapping")
            self.map=saved
        elif configured:
            raise ValueError("Import this existing OpenV model's mapping before updating it; refusing to create duplicate elements")
        self.hardware=None

    def close(self):
        if getattr(self,"_lock",None):self._lock.close();self._lock=None

    def __del__(self):
        self.close()

    def public_ref(self):
        return {"model_id":self.map["model_id"],"commit":self.map["commit"],
                "requirements":self.map["requirements"],"test_cases":self.map["test_cases"]}

    async def call(self, connection, name, args):
        return unpack(await connection.call_tool(name,args))

    async def write(self, connection, operations):
        # Dalus evaluates expression as canonical; an empty expression clears a
        # supplied value. Encode literal constants, including quoted strings.
        for operation in operations:
            fields=operation["input"]
            if operation["operation"] in ("addVariable","updateVariable") and "value" in fields:
                fields["expression"]=json.dumps(fields["value"],allow_nan=False)
        result=await self.call(connection,"writeModelChanges",{"modelId":self.map["model_id"],"operations":operations})
        if result.get("failedOperations"):
            self.map["commit"]="incomplete"
            self.persist()
            raise RuntimeError("Dalus partial batch; commit remains incomplete: "+json.dumps(result["failedOperations"])[:1800])
        return result

    async def search(self, connection, collections):
        # searchModel exposes offset, but no page-size/total guarantee. Read each
        # collection until an empty page; never infer completeness from tool success.
        output={}
        for collection in collections:
            records=[];seen=set();offset=0
            for _ in range(100):
                result=await self.call(connection,"searchModel",{"modelId":self.map["model_id"],"collections":[collection],"offset":offset})
                model=result.get("model",result)
                page=model.get(collection,[])
                page=list(page.values()) if isinstance(page,dict) else page
                if not isinstance(page,list):raise RuntimeError("Malformed Dalus collection")
                if not page:
                    remaining=result.get("truncated",{}).get("remaining",{}).get(collection,0)
                    if remaining:raise RuntimeError("Dalus returned an empty page with remaining records")
                    break
                ids=[item.get("id") if isinstance(item,dict) else str(item) for item in page]
                if len(set(ids))!=len(ids) or any(id in seen for id in ids):raise RuntimeError("Dalus pagination did not advance consistently")
                records.extend(page);seen.update(ids);offset+=len(page)
            else:raise RuntimeError("Dalus collection exceeds bounded read-back limit")
            output[collection]=records
        return output

    async def confirmed(self,connection,collection,predicate):
        for attempt in range(4):
            result=await self.search(connection,[collection])
            if predicate(result[collection]):return result[collection]
            if attempt<3:await asyncio.sleep(.5*(attempt+1))
        raise RuntimeError(f"Dalus {collection} read-back did not match after bounded consistency retries")

    def persist(self):
        from openv.pipeline import write_json
        write_json(self.directory/"dalus-mapping.json",self.map)
        write_json(self.shared_path,self.map)
        self.shared_path.chmod(0o600)

    def create_system(self, hardware, design):
        self.hardware=hardware
        async def create():
            from openv.pipeline import write_json
            async with session() as connection:
                if not self.map["model_id"]:
                    created=await self.call(connection,"createModel",{"teamId":self.team_id,"name":"OpenV · Albatross motor-glider"})
                    self.map["model_id"]=created["model"]["id"]
                    self.map["model_slug"]=created["model"].get("slug")
                    self.persist()
                snapshot=await self.search(connection,["parts","variables","ports","connections","requirements","testCases"])
                write_json(self.directory/"dalus-before-update.json",snapshot)
                previous_parts={item['id']:item for item in snapshot['parts']}
                previous_variables={item['id']:item for item in snapshot['variables']}
                previous_requirements={item['customerId']:item for item in snapshot['requirements'] if item.get('customerId')}
                if len(previous_requirements)!=len([item for item in snapshot['requirements'] if item.get('customerId')]):
                    raise RuntimeError('Ambiguous duplicate Dalus requirement customer IDs')
                previous_cases={item['name'].removeprefix('OpenV / '):item for item in snapshot['testCases'] if item.get('name','').startswith('OpenV / ')}
                if any(id not in previous_parts for id in self.map['parts'].values()):
                    raise RuntimeError('Mapped Dalus elements missing; refusing duplicate reconstruction')
                # Close current verdicts before changing any engineering inputs.
                if self.map.get('marker'):
                    await self.write(connection,[op('updateVariable',id=self.map['marker'],value=f'incomplete:{design.id}')]+[
                        op('updateRequirement',id=item['id'],status='In Progress') for item in previous_requirements.values()]+[op('updateTestCase',id=item['id'],status='In Progress') for item in previous_cases.values()])
                    self.map['commit']='incomplete';self.persist()
                if previous_parts:
                    await self.write(connection,[op('addTradeStudy',title=f'OpenV baseline / {self.directory.name}',
                        description=json.dumps({'run_id':self.directory.name,'new_baseline':hardware.baseline_id,'new_design':design.id,
                            'previous_commit':snapshot['variables'] and next((v.get('value') for v in snapshot['variables'] if v.get('id')==self.map.get('marker')),None),
                            'previous_snapshot':f'{self.directory.name}/dalus-before-update.json',
                            'reason':'User-requested mission/design or engineering-definition update; historical evidence remains version-bound'}),
                        alternatives=[{'name':design.id,'description':'Current candidate; external verification pending'}])])
                parents={};ordered=[]
                for parent,children in hardware.architecture.items():
                    if parent not in ordered:ordered.append(parent)
                    for child in children:
                        parents[child]=parent
                        if child not in ordered:ordered.append(child)
                root=ordered[0];self.map['root']=root
                for component in hardware.components:
                    if component.id not in ordered:ordered.append(component.id);parents[component.id]=root
                ops=[]
                for key in ordered:
                    exists=key in self.map['parts']
                    if not exists:self.map['parts'][key]=uuid();self.map['nodes'][key]=uuid()
                    fields={'id':self.map['parts'][key],'name':key.replace('-',' ').title(),
                        'notes':json.dumps({'baseline':hardware.baseline_id,'design_id':design.id,'mission':hardware.mission}) if key==root else f'OpenV element {key}. Baseline {hardware.baseline_id}.'}
                    if exists:
                        if key in parents:fields['parentId']=self.map['parts'][parents[key]]
                    else:
                        fields['nodeId']=self.map['nodes'][key]
                        if key in parents:fields['parentNodeId']=self.map['nodes'][parents[key]]
                    ops.append(op('updatePart' if exists else 'addPart',**fields))
                self.map.setdefault('marker',uuid())
                ops.append(op('updateVariable' if self.map['marker'] in previous_variables else 'addVariable',id=self.map['marker'],name='openv_commit',value=f'incomplete:{design.id}',unitName='string'))
                def variable(fields):
                    ops.append(op('updateVariable' if fields['id'] in previous_variables else 'addVariable',**fields))
                attributes=[self.map['marker']]
                current_variables={}
                for name,value in design.parameters.items():
                    id=self.map['variables'].get(name) or uuid();current_variables[name]=id;attributes.append(id)
                    variable({'id':id,'name':name,'value':value,'unitName':'meter' if name.endswith('_m') else 'degree' if name.endswith('_deg') else 'dimensionless',
                        'description':f'Canonical design parameter. {design.id}; SI units.'})
                self.map['variables']=current_variables
                # Reconstruct identity indexes from Dalus attributes, not cached source values.
                root_attributes=previous_parts.get(self.map['parts'][root],{}).get('attributeIds',[])
                scenario_ids={previous_variables[id]['name']:id for id in root_attributes if id in previous_variables and previous_variables[id].get('description','').startswith('Frozen mission baseline')}
                self.map['fixed_variables']={}
                scenario_units={'payload_kg':('gram','kilo'),'cruise_mps':('meter per second',None),'endurance_min':('second',None),'max_mass_kg':('gram','kilo'),'altitude_m':('meter',None),'load_factor':('dimensionless',None)}
                for name,value in hardware.scenario.items():
                    if name=='text':continue
                    stored_name='endurance_s' if name=='endurance_min' else name
                    id=scenario_ids.get(stored_name) or uuid();attributes.append(id)
                    unit,prefix=scenario_units.get(name,('dimensionless',None))
                    fields={'id':id,'name':stored_name,'value':value*60 if name=='endurance_min' else value,'unitName':unit,'description':f'Frozen mission baseline {hardware.baseline_id}'}
                    if prefix:fields['prefix']=prefix
                    variable(fields);self.map['fixed_variables'][id]=fields
                ops.append(op('updatePart',id=self.map['parts'][root],attributeIds=attributes))
                units={'kg':('gram','kilo'),'m':('meter',None),'A':('ampere',None),'V':('volt',None),'Ah':('ampere hour',None),'1':('dimensionless',None)}
                for component in hardware.components:
                    old_ids=previous_parts.get(self.map['parts'][component.id],{}).get('attributeIds',[])
                    by_name={previous_variables[id]['name']:id for id in old_ids if id in previous_variables}
                    ids=[]
                    for name,prop in component.properties.items():
                        id=by_name.get(name) or uuid();ids.append(id);unit,prefix=units.get(prop.unit,('string',None))
                        fields={'id':id,'name':name,'value':prop.value,'unitName':unit,
                            'description':json.dumps({'quality':prop.quality,'source':prop.source,'original_unit':prop.unit})}
                        if prefix:fields['prefix']=prefix
                        if prop.unit=='rpm/V':fields.update(value=f'{prop.value} rpm/V',unitName='string')
                        elif isinstance(prop.value,str):fields['unitName']='string'
                        variable(fields);self.map['fixed_variables'][id]=fields
                    ops.append(op('updatePart',id=self.map['parts'][component.id],name=component.name,attributeIds=ids,
                        notes=json.dumps({'manufacturer':component.manufacturer,'part_number':component.part_number,'revision':component.revision})))
                for interface in hardware.interfaces:
                    old_ports=[p for p in snapshot['ports'] if p.get('name')==interface.id]
                    if old_ports:
                        for port in old_ports:
                            old=json.loads(port.get('notes','{}'))
                            if old.get('endpoints')!=list(interface.endpoints):raise RuntimeError('Interface endpoint migration requires an explicit route update')
                            ops.append(op('updatePort',id=port['id'],notes=json.dumps(interface.model_dump())))
                        ops.extend(op('updateConnection',id=edge['id'],notes=json.dumps(interface.definition)) for edge in snapshot['connections'] if edge.get('name')==interface.id)
                        continue
                    first=interface.endpoints[0]
                    for target in interface.endpoints[1:]:
                        def ancestry(element):
                            path=[element]
                            while element in parents:element=parents[element];path.append(element)
                            return path
                        left,right=ancestry(first),ancestry(target);common=next(node for node in left if node in right)
                        route=left[:left.index(common)+1]+list(reversed(right[:right.index(common)]));nodes=[]
                        for element in route:
                            node=uuid();nodes.append(node)
                            ops.append(op('addPort',id=uuid(),nodeId=node,name=interface.id,parentNodeId=self.map['nodes'][element],notes=json.dumps(interface.model_dump())))
                        ops.extend(op('addConnection',id=uuid(),name=interface.id,sourcePortNodeId=a,targetPortNodeId=b,notes=json.dumps(interface.definition)) for a,b in zip(nodes,nodes[1:]))
                await self.write(connection,ops);self.persist()
                wanted={r.id for r in hardware.requirements};ops=[]
                for key,item in previous_requirements.items():
                    if key not in wanted:
                        ops.append(op('updateRequirement',id=item['id'],status='Incomplete',lifecycleStatus='Deprecated',systems=[]))
                        if key in previous_cases:ops.append(op('updateTestCase',id=previous_cases[key]['id'],lifecycleStatus='Deprecated',status='Blocked'))
                for requirement in hardware.requirements:
                    owner=self.map['parts'].get(requirement.owner,self.map['parts'][root])
                    text=requirement.statement+'. '+'; '.join(f'{c.metric} {c.operator} {c.threshold} {c.unit}. Scope: {c.scope}' for c in requirement.contracts)
                    fields={'customerId':requirement.id,'name':requirement.statement,'tiptapDocument':f'<p>{html.escape(text)}</p>',
                        'status':'Incomplete','systems':[owner],'lifecycleStatus':'Baselined',
                        'info':{'comment':json.dumps({'baseline':hardware.baseline_id,'origin':requirement.origin,'contracts':[c.model_dump() for c in requirement.contracts]})}}
                    if requirement.id in previous_requirements:fields['id']=previous_requirements[requirement.id]['id'];operation='updateRequirement'
                    else:fields['statement']=text;operation='addRequirement'
                    ops.append(op(operation,**fields))
                await self.write(connection,ops)
                records=await self.confirmed(connection,'requirements',lambda rows:wanted.issubset({r.get('customerId') for r in rows}))
                self.map['requirements']={r['customerId']:r['id'] for r in records if r.get('customerId') in wanted}
                if len(self.map['requirements'])!=len(wanted):raise RuntimeError('Incomplete current requirements')
                ops=[]
                for key,id in self.map['parts'].items():
                    ops.append(op('updatePart',id=id,requirements=[self.map['requirements'][r.id] for r in hardware.requirements if r.owner==key]))
                for requirement in hardware.requirements:
                    owner=self.map['parts'].get(requirement.owner,self.map['parts'][root])
                    fields={'name':f'OpenV / {requirement.id}','status':'Planned','lifecycleStatus':'Baselined','purpose':['Verification'],
                        'type':'Other','customType':'External engineering analysis / inspection','systems':[owner],
                        'requirements':[{'requirementId':self.map['requirements'][requirement.id],'rationale':'Independent evidence required by frozen contract'}],
                        'description':json.dumps([c.model_dump() for c in requirement.contracts]),
                        'procedure':['Resolve canonical design and provenance','Execute registered method','Admit metric only if input/method scope is valid','Compare with frozen threshold'],
                        'notes':'History is version-bound; current verdict requires new admitted evidence.'}
                    if requirement.id in previous_cases:
                        item=previous_cases[requirement.id];fields['id']=item['id'];operation='updateTestCase'
                        self.map['test_runs'][requirement.id]=copy.deepcopy(item.get('runs',[]))
                    else:operation='addTestCase'
                    ops.append(op(operation,**fields))
                await self.write(connection,ops)
                records=await self.confirmed(connection,'testCases',lambda rows:wanted.issubset({r.get('name','').removeprefix('OpenV / ') for r in rows}))
                self.map['test_cases']={r['name'].removeprefix('OpenV / '):r['id'] for r in records if r.get('name','').removeprefix('OpenV / ') in wanted}
                await self.write(connection,[op('updateRequirement',id=self.map['requirements'][r.id],verifications=[{'id':uuid(),'method':'test','testCaseId':self.map['test_cases'][r.id]}]) for r in hardware.requirements])
                await self.assert_design(connection,design)
                await self.write(connection,[op('updateVariable',id=self.map['marker'],value=f'defined:{design.id}')])
                self.map['commit']='defined';self.persist();return self.public_ref()
        return asyncio.run(create())

    async def assert_design(self,s,design):
        for attempt in range(4):
            try:return await self._assert_design_once(s,design)
            except RuntimeError:
                if attempt==3:raise
                await asyncio.sleep(.5*(attempt+1))

    async def _assert_design_once(self,s,design):
        result=await self.search(s,["variables"])
        records={v["id"]:v for v in result.get("variables",[])}
        values={id:v.get("value") for id,v in records.items()}
        for name,id in self.map["variables"].items():
            if values.get(id)!=design.parameters[name]:
                raise RuntimeError(f"Dalus canonical parameter differs: {name}; verification blocked")
            expected_unit="meter" if name.endswith("_m") else "degree" if name.endswith("_deg") else "dimensionless"
            if records[id].get("unitName")!=expected_unit or records[id].get("prefix"):
                raise RuntimeError(f"Dalus parameter units differ: {name}; verification blocked")
        for id,expected in self.map["fixed_variables"].items():
            actual=records.get(id,{})
            if any(actual.get(field)!=expected.get(field) for field in ("value","unitName","prefix","description")):
                raise RuntimeError("Dalus baseline/component source differs; verification blocked")
        if self.hardware and self.map["requirements"]:
            data=await self.search(s,["requirements"])
            requirements={r["customerId"]:r for r in data.get("requirements",[])}
            for requirement in self.hardware.requirements:
                actual=requirements.get(requirement.id,{})
                recorded=json.loads(actual.get("info",{}).get("comment","{}"))
                if recorded.get("contracts")!=[c.model_dump() for c in requirement.contracts] or recorded.get("baseline")!=self.hardware.baseline_id:
                    raise RuntimeError("Dalus verification contract differs from frozen baseline")

    def record_verification(self,hardware,design,snapshot):
        async def record():
            async with session() as s:
                await self.assert_design(s,design)
                await self.write(s,[op("updateVariable",id=self.map["marker"],value=f"incomplete:{design.id}",expression="")])
                self.map["commit"]="incomplete";self.persist()
                operations=[]
                for evaluation in snapshot["evaluations"]:
                    key=evaluation["requirement_id"]
                    status=evaluation["status"]
                    case_status={"PASS":"Passed","FAIL":"Failed","UNKNOWN":"Blocked"}[status]
                    history=self.map["test_runs"].setdefault(key,[])
                    entry={"id":uuid(),"runNumber":len(history)+1,"status":case_status,
                        "notes":json.dumps({"design_id":design.id,"baseline":design.baseline_id,"evaluation":evaluation,
                            "evidence":[{k:e[k] for k in ("id","design_id","fingerprint","method","tool_version","output_hash")} for e in snapshot["evidence"] if e["id"] in evaluation["evidence_ids"]],
                            "artifact_path":f"{self.directory.name}/{design.id}/verification.json"})}
                    public=os.environ.get("OPENV_PUBLIC_URL")
                    if public:
                        entry["attachments"]=[{"id":uuid(),"type":"link","label":"Versioned verification evidence",
                            "url":f"{public.rstrip('/')}/artifacts/{self.directory.name}/{design.id}/verification.json"}]
                    history.append(entry)
                    operations.append(op("updateTestCase",id=self.map["test_cases"][key],status=case_status,runs=history))
                    operations.append(op("updateRequirement",id=self.map["requirements"][key],
                        status={"PASS":"Complete","FAIL":"Failed","UNKNOWN":"Incomplete"}[status]))
                await self.write(s,operations)
                expected_statuses={self.map["requirements"][e["requirement_id"]]:{"PASS":"Complete","FAIL":"Failed","UNKNOWN":"Incomplete"}[e["status"]] for e in snapshot["evaluations"]}
                await self.confirmed(s,"requirements",lambda rows:all({r["id"]:r.get("status") for r in rows}.get(id)==status for id,status in expected_statuses.items()))
                expected_runs={self.map["test_cases"][e["requirement_id"]]:self.map["test_runs"][e["requirement_id"]][-1]["id"] for e in snapshot["evaluations"]}
                await self.confirmed(s,"testCases",lambda rows:all(any(run.get("id")==run_id for run in next((r.get("runs",[]) for r in rows if r["id"]==id),[])) for id,run_id in expected_runs.items()))
                await self.write(s,[op("updateVariable",id=self.map["marker"],value=f"evaluated:{design.id}:{digest(snapshot)}",expression="")])
                self.map["commit"]="evaluated";self.persist()
                return self.public_ref()
        return asyncio.run(record())

    def record_experiment(self,hardware,old,candidate,experiment,evaluations):
        async def change():
            async with session() as s:
                await self.assert_design(s,old)
                # Stale statuses are written before any design variables change.
                stale=[op("updateVariable",id=self.map["marker"],value=f"incomplete:{candidate.id}",expression="")]
                for evaluation in evaluations:
                    if evaluation.get("stale_evidence_ids"):
                        key=evaluation["requirement_id"]
                        stale.extend([op("updateRequirement",id=self.map["requirements"][key],status="In Progress"),
                                      op("updateTestCase",id=self.map["test_cases"][key],status="In Progress")])
                await self.write(s,stale)
                self.map["commit"]="incomplete";self.persist()
                await self.write(s,[op("addTradeStudy",title=f"OpenV experiment / {experiment.id}",
                    description=json.dumps(experiment.model_dump()),alternatives=[
                        {"name":old.id,"description":"Parent design with actual failure evidence"},
                        {"name":candidate.id,"description":experiment.hypothesis}])]+[
                    op("updateVariable",id=self.map["variables"][name],value=value,expression="") for name,value in experiment.change.items()])
                await self.assert_design(s,candidate)
                await self.write(s,[op("updateVariable",id=self.map["marker"],value=f"defined:{candidate.id}",expression="")])
                self.map["commit"]="defined";self.persist()
        return asyncio.run(change())

    def complete_experiment(self,experiment):
        async def record():
            async with session() as s:
                studies=await self.search(s,["tradeStudies"])
                matches=[t for t in studies.get("tradeStudies",[]) if t.get("title")==f"OpenV experiment / {experiment.id}"]
                if len(matches)!=1:raise RuntimeError("Dalus experiment record missing or ambiguous")
                await self.write(s,[op("updateTradeStudy",id=matches[0]["id"],description=json.dumps(experiment.model_dump()))])
        return asyncio.run(record())

    def record_user_experiment(self,experiment):
        async def record():
            async with session() as s:
                await self.write(s,[op("addTradeStudy",title=f"OpenV experiment / {experiment.id}",
                    description=json.dumps(experiment.model_dump()),alternatives=[
                        {"name":experiment.from_design,"description":"Parent run; historical evidence is not current for this candidate"},
                        {"name":experiment.to_design,"description":"User-requested mission/design change with recomputed evidence"}])])
        return asyncio.run(record())
