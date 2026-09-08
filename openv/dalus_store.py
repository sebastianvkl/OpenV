"""Typed engineering records mapped to discovered Dalus MCP operations.

The local mapping contains IDs/cache only. Every state transition is committed to
Dalus and read back before the pipeline can treat it as authoritative.
"""
from __future__ import annotations

import asyncio
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
        self.map={"model_id":model_id,"parts":{},"nodes":{},"variables":{},"requirements":{},"test_cases":{},"test_runs":{},"commit":"incomplete","fixed_variables":{}}
        self.hardware=None

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
        result=await self.call(connection,"searchModel",{"modelId":self.map["model_id"],"collections":collections})
        # Search responses can be capped. Never accept a partial read as a full commit.
        if result.get("truncated") or result.get("model",{}).get("truncated"):
            raise RuntimeError("Dalus read-back was truncated; narrow/page the query before committing")
        model=result.get("model",result)
        return {key:list(value.values()) if isinstance(value,dict) else value for key,value in model.items()}

    def persist(self):
        from openv.pipeline import write_json
        write_json(self.directory/"dalus-mapping.json",self.map)

    def create_system(self, hardware, design):
        self.hardware=hardware
        async def create():
            async with session() as s:
                if not self.map["model_id"]:
                    created=await self.call(s,"createModel",{"teamId":self.team_id,"name":f"OpenV · {self.directory.name}"})
                    self.map["model_id"]=created["model"]["id"]
                    self.map["model_slug"]=created["model"].get("slug")
                    self.persist()
                parents={}
                ordered=[]
                for parent,children in hardware.architecture.items():
                    if parent not in ordered:ordered.append(parent)
                    for child in children:
                        parents[child]=parent
                        if child not in ordered:ordered.append(child)
                root=ordered[0]
                for component in hardware.components:
                    if component.id not in ordered:
                        ordered.append(component.id);parents[component.id]=root
                for key in ordered:
                    self.map["parts"][key]=uuid();self.map["nodes"][key]=uuid()
                self.map["root"]=root
                ops=[]
                for key in ordered:
                    fields={"id":self.map["parts"][key],"nodeId":self.map["nodes"][key],"name":key.replace('-',' ').title(),
                            "notes":f"OpenV element {key}. Baseline {hardware.baseline_id}."}
                    if key in parents:fields["parentNodeId"]=self.map["nodes"][parents[key]]
                    if key==root:fields["notes"]=json.dumps({"mission":hardware.mission,"baseline":hardware.baseline_id,"design_id":design.id,"commit":"incomplete"})
                    ops.append(op("addPart",**fields))
                self.map["marker"]=uuid()
                ops.append(op("addVariable",id=self.map["marker"],name="openv_commit",value="incomplete",unitName="string",expression=""))
                attribute_ids=[self.map["marker"]]
                for name,value in design.parameters.items():
                    variable=uuid();self.map["variables"][name]=variable;attribute_ids.append(variable)
                    unit="meter" if name.endswith("_m") else "degree" if name.endswith("_deg") else "dimensionless"
                    ops.append(op("addVariable",id=variable,name=name,value=value,unitName=unit,expression="",
                                  description=f"Canonical design parameter. {design.id}; SI units."))
                scenario_units={"payload_kg":("gram","kilo"),"cruise_mps":("meter per second",None),
                    "endurance_min":("second",None),"max_mass_kg":("gram","kilo"),"altitude_m":("meter",None),"load_factor":("dimensionless",None)}
                for name,value in hardware.scenario.items():
                    if name=="text":continue
                    variable=uuid();attribute_ids.append(variable)
                    unit,prefix=scenario_units.get(name,("dimensionless",None))
                    stored_value=value*60 if name=="endurance_min" else value
                    fields={"id":variable,"name":"endurance_s" if name=="endurance_min" else name,"value":stored_value,
                        "unitName":unit,"description":f"Frozen mission baseline {hardware.baseline_id}"}
                    if prefix:fields["prefix"]=prefix
                    ops.append(op("addVariable",**fields));self.map["fixed_variables"][variable]=fields
                ops.append(op("updatePart",id=self.map["parts"][root],attributeIds=attribute_ids))
                units={"kg":("gram","kilo"),"m":("meter",None),"A":("ampere",None),"V":("volt",None),
                       "Ah":("ampere hour",None),"1":("dimensionless",None),"rpm/V":("dimensionless",None)}
                for component in hardware.components:
                    ids=[]
                    for name,prop in component.properties.items():
                        variable=uuid();ids.append(variable)
                        unit,prefix=units.get(prop.unit,("string",None))
                        fields={"id":variable,"name":name,"value":prop.value,"unitName":unit,"expression":"",
                                "description":json.dumps({"quality":prop.quality,"source":prop.source,"original_unit":prop.unit})}
                        if prefix:fields["prefix"]=prefix
                        if prop.unit=="rpm/V":
                            fields.update(value=f"{prop.value} rpm/V",unitName="string")
                        elif isinstance(prop.value,str):
                            fields["unitName"]="string"
                        ops.append(op("addVariable",**fields))
                        self.map["fixed_variables"][variable]=fields
                    ops.append(op("updatePart",id=self.map["parts"][component.id],name=component.name,attributeIds=ids,
                                  notes=json.dumps({"manufacturer":component.manufacturer,"part_number":component.part_number,"revision":component.revision})))
                # Route interfaces through explicit parent/child delegation ports.
                for interface in hardware.interfaces:
                    first=interface.endpoints[0]
                    for target in interface.endpoints[1:]:
                        def ancestry(element):
                            path=[element]
                            while element in parents:element=parents[element];path.append(element)
                            return path
                        left,right=ancestry(first),ancestry(target)
                        common=next(node for node in left if node in right)
                        route=left[:left.index(common)+1]+list(reversed(right[:right.index(common)]))
                        port_nodes=[]
                        for element in route:
                            port_node=uuid();port_nodes.append(port_node)
                            ops.append(op("addPort",name=interface.id,nodeId=port_node,id=uuid(),
                                          parentNodeId=self.map["nodes"][element],notes=json.dumps(interface.model_dump())))
                        for source_node,target_node in zip(port_nodes,port_nodes[1:]):
                            ops.append(op("addConnection",id=uuid(),name=interface.id,
                                          sourcePortNodeId=source_node,targetPortNodeId=target_node,notes=json.dumps(interface.definition)))
                await self.write(s,ops)
                self.persist()
                req_ops=[]
                for requirement in hardware.requirements:
                    owner=self.map["parts"].get(requirement.owner,self.map["parts"][root])
                    text=requirement.statement+". "+"; ".join(f"{c.metric} {c.operator} {c.threshold} {c.unit}. Scope: {c.scope}" for c in requirement.contracts)
                    req_ops.append(op("addRequirement",customerId=requirement.id,name=requirement.statement,
                        statement=text,tiptapDocument=f"<p>{html.escape(text)}</p>",status="Incomplete",systems=[owner],
                        lifecycleStatus="Baselined",info={"comment":json.dumps({"baseline":hardware.baseline_id,"origin":requirement.origin,"contracts":[c.model_dump() for c in requirement.contracts]})}))
                await self.write(s,req_ops)
                data=await self.search(s,["requirements"])
                requirements=data.get("requirements",[])
                self.map["requirements"]={r["customerId"]:r["id"] for r in requirements}
                if set(self.map["requirements"])!={r.id for r in hardware.requirements}:
                    raise RuntimeError("Dalus requirement read-back does not match the frozen baseline")
                ops=[]
                for key,part_id in self.map["parts"].items():
                    linked=[self.map["requirements"][r.id] for r in hardware.requirements if r.owner==key]
                    if linked:ops.append(op("updatePart",id=part_id,requirements=linked))
                for requirement in hardware.requirements:
                    owner=self.map["parts"].get(requirement.owner,self.map["parts"][root])
                    ops.append(op("addTestCase",name=f"OpenV / {requirement.id}",status="Planned",purpose=["Verification"],
                        type="Other",customType="External engineering analysis / inspection",systems=[owner],
                        requirements=[{"requirementId":self.map["requirements"][requirement.id],"rationale":"Independent evidence required by frozen contract"}],
                        description=json.dumps([c.model_dump() for c in requirement.contracts]),
                        procedure=["Resolve canonical design and provenance","Execute registered method","Admit metric only if input/method scope is valid","Compare with frozen threshold"],
                        notes="Physical methods are unexecuted unless measurement evidence is supplied."))
                await self.write(s,ops)
                data=await self.search(s,["testCases"])
                self.map["test_cases"]={t["name"].removeprefix("OpenV / "):t["id"] for t in data.get("testCases",[])}
                if set(self.map["test_cases"])!=set(self.map["requirements"]):
                    raise RuntimeError("Dalus verification plan read-back is incomplete")
                await self.write(s,[op("updateRequirement",id=self.map["requirements"][r.id],verifications=[{
                    "id":uuid(),"method":"test","testCaseId":self.map["test_cases"][r.id]}]) for r in hardware.requirements])
                await self.assert_design(s,design)
                await self.write(s,[op("updateVariable",id=self.map["marker"],value=f"defined:{design.id}",expression="")])
                self.map["commit"]="defined";self.persist()
                return self.public_ref()
        return asyncio.run(create())

    async def assert_design(self,s,design):
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
                read=await self.search(s,["requirements"])
                statuses={r["id"]:r["status"] for r in read.get("requirements",[])}
                for evaluation in snapshot["evaluations"]:
                    expected={"PASS":"Complete","FAIL":"Failed","UNKNOWN":"Incomplete"}[evaluation["status"]]
                    if statuses.get(self.map["requirements"][evaluation["requirement_id"]])!=expected:
                        raise RuntimeError("Dalus status read-back mismatch; commit remains incomplete")
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
