"""One public entry point for the website, CLI and reference demo."""
from __future__ import annotations

import csv
import json
import os
import shutil
import time
import zipfile
from pathlib import Path

from openv import aircraft, cad
from openv.core import (Contract, Evidence, Experiment, Requirement, Status,
                        VerificationEngine, digest, gate, uid)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False))
    temporary.replace(path)


class Pipeline:
    def __init__(self, directory: Path, engineer, store=None):
        self.directory, self.engineer, self.store = directory,engineer,store
        self.directory.mkdir(parents=True,exist_ok=True)
        self.state={"id":directory.name,"status":"running","stage":"mission","provider":engineer.label,
            "engineering_store":"local fixture" if store is None else "Dalus MCP",
            "events":[],"versions":[],"experiments":[],"evaluations":[],"evidence":[],"stop_reason":None}
        self.started=time.monotonic()
        self.engine=VerificationEngine(aircraft.methods()+[cad.method()])

    def event(self, kind, message, **details):
        self.state["stage"]=kind
        self.state["events"].append({"kind":kind,"message":message,"elapsed_s":round(time.monotonic()-self.started,2),**details})
        self.save()

    def save(self):
        write_json(self.directory/"run.json",self.state)

    def context(self, hardware, design, geometry):
        # Derived mass properties embed each input/source and material assumption.
        # A source, placement or geometry change therefore propagates transitively.
        return {"geometry":design.parameters,"mass_properties":geometry["mass_properties"],
            "scenario":hardware.scenario,"materials":aircraft.MATERIALS,
            "catalog":[c.model_dump() for c in hardware.components],"cad_checks":geometry["checks"]}

    def geometry(self, design, mission):
        self.event("design","Generating parametric CAD and CAD-derived mass properties",design_id=design.id)
        directory=self.directory/design.id
        geometry=cad.build(design.parameters,mission.model_dump(),directory)
        write_json(directory/"design.json",design.model_dump())
        self.state["versions"].append({**design.model_dump(),"geometry_file":f"{design.id}/geometry.json"})
        self.state["current_design_id"]=design.id
        self.state["geometry_file"]=f"{design.id}/geometry.json"
        return geometry

    def verify(self,hardware,design,context,previous=()):
        self.event("verify","Running registered external engineering methods",design_id=design.id)
        evidence=self.engine.verify(design,hardware.requirements,context,previous)
        evaluations=self.engine.evaluate(hardware.requirements,context,evidence)
        self.state["evidence"]=[e.model_dump() for e in evidence]
        self.state["evaluations"]=[e.model_dump() for e in evaluations]
        self.state["gate"]=gate(hardware.requirements,evaluations).value
        snapshot={"design":design.model_dump(),"evidence":self.state["evidence"],
                  "evaluations":self.state["evaluations"],"gate":self.state["gate"]}
        write_json(self.directory/design.id/"verification.json",snapshot)
        if self.store:
            self.state["dalus"]=self.store.record_verification(hardware,design,snapshot)
        self.event("evaluated","Independent comparisons completed",statuses={e.requirement_id:e.status for e in evaluations})
        return evidence,evaluations

    def run(self,mission_text: str,max_experiments=5):
        try:
            return self._run(mission_text,max_experiments)
        except Exception as exc:
            self.state["status"]="error"
            self.state["stop_reason"]=f"{type(exc).__name__}: {exc}"
            self.event("error","Execution stopped; existing evidence remains version-bound")
            raise

    def _run(self,mission_text,max_experiments):
        self.event("mission","Proposing mission requirements, architecture and initial design")
        definition=self.engineer.define(mission_text)
        self.state["mission_proposal"]=definition.model_dump()
        if not definition.supported:
            self.state.update(status="complete",stop_reason="unsupported_mission",gate="UNKNOWN")
            self.event("complete","Requested mission is outside current domain coverage")
            return self.state
        # Retain the user's exact intent even if the model paraphrases its text.
        definition=definition.model_copy(update={"mission":definition.mission.model_copy(update={"text":mission_text})})
        hardware=aircraft.system(definition.mission)
        # Preserve every uncovered clause as an explicit requirement with no fabricated method.
        extra=tuple(Requirement(id=f"uncovered-{i+1}",statement=clause,level="mission",owner="aircraft",
            contracts=(),origin="uncovered user clause") for i,clause in enumerate(definition.uncovered_clauses))
        hardware=hardware.model_copy(update={"requirements":hardware.requirements+extra})
        self.state["system"]=hardware.model_dump()
        design=aircraft.initial_design(hardware,definition.parameters)
        if self.store:
            self.state["dalus"]=self.store.create_system(hardware,design)
        self.event("requirements","Mission baseline and verification contracts frozen",baseline_id=hardware.baseline_id)
        geometry=self.geometry(design,definition.mission)
        context=self.context(hardware,design,geometry)
        evidence,evaluations=self.verify(hardware,design,context)
        stop="experiment_limit"
        for _ in range(max_experiments):
            if time.monotonic()-self.started>float(os.environ.get("OPENV_RUN_TIMEOUT","600")):
                stop="time_limit"; break
            failures=[e for e in evaluations if e.status==Status.FAIL]
            if not failures:
                stop="verified_modeled_checks_with_unknowns" if any(e.status==Status.UNKNOWN for e in evaluations) else "requirements_passed"
                break
            self.event("redesign","Sending actual failure evidence to the proposing engineer")
            proposal_context={"system":hardware.model_dump(),"design":design.model_dump(),
                "evaluations":[e.model_dump() for e in evaluations],
                "evidence":[e.model_dump() for e in evidence],"experiments":self.state["experiments"][-3:]}
            for attempt in range(3):
                proposal=self.engineer.redesign(proposal_context)
                experiment_id=uid("experiment")
                try:
                    candidate=aircraft.patched(design,proposal.changes,experiment_id)
                    break
                except ValueError as exc:
                    self.event("proposal-rejected",str(exc))
                    proposal_context["proposal_validation_error"]=str(exc)
                    if attempt==2:
                        raise ValueError("Proposer exhausted schema/engineering repair attempts") from exc
            # Publish invalidation before invoking CAD/solvers. All geometry-dependent
            # consumers are stale here; unrelated electrical evidence remains applicable.
            affected={name for name,m in self.engine.methods.items() if "geometry" in m.dependencies or "mass_properties" in m.dependencies}
            invalidated=tuple(e.id for e in evidence if e.method in affected)
            before=tuple(e.id for e in evidence)
            exp=Experiment(id=experiment_id,problem=proposal.problem,hypothesis=proposal.hypothesis,
                change=proposal.changes,expected_effect=proposal.expected_effect,from_design=design.id,to_design=candidate.id,
                before_evidence=before,invalidated_evidence=invalidated)
            self.state["experiments"].append(exp.model_dump())
            self.state["current_design_id"]=candidate.id
            self.state["evaluations"]=[{**e.model_dump(),"status":"UNKNOWN","stale_evidence_ids":list(e.evidence_ids),"reasons":["Design changed; dependent evidence needs re-verification"]}
                if set(e.evidence_ids)&set(invalidated) else e.model_dump() for e in evaluations]
            self.state["gate"]="UNKNOWN"
            self.event("invalidated","Candidate committed; dependent evidence is stale",experiment=exp.model_dump())
            if self.store:
                self.store.record_experiment(hardware,design,candidate,exp,self.state["evaluations"])
            geometry=self.geometry(candidate,definition.mission)
            new_context=self.context(hardware,candidate,geometry)
            new_evidence,new_evaluations=self.verify(hardware,candidate,new_context,evidence)
            actual={e.requirement_id:{"before":next(old.status.value for old in evaluations if old.requirement_id==e.requirement_id),
                                     "after":e.status.value,"reasons":list(e.reasons)} for e in new_evaluations}
            exp=exp.model_copy(update={"after_evidence":tuple(e.id for e in new_evidence),"actual_effect":actual})
            self.state["experiments"][-1]=exp.model_dump()
            design,context,evidence,evaluations=candidate,new_context,new_evidence,new_evaluations
            self.event("experiment-complete","Experiment recorded with actual results",experiment_id=exp.id)
        self.state["model_calls"]=self.engineer.calls
        self.state["stop_reason"]=stop
        self.package(hardware,design,geometry)
        self.state["status"]="complete"
        self.event("complete","Candidate package ready; inspect verification scope and open requirements")
        return self.state

    def package(self,hardware,design,geometry):
        self.event("package","Packaging this design version, evidence, BOM and fabrication notes")
        folder=self.directory/design.id
        bom=[{k:part[k] for k in ("id","name","process","mass_kg","mass_quality","note")} for part in geometry["parts"]]
        with (folder/"bom.csv").open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(bom[0]));writer.writeheader();writer.writerows(bom)
        write_json(folder/"system.json",hardware.model_dump())
        write_json(folder/"experiments.json",self.state["experiments"])
        sequence=[
            {"title":"Prepare the wing modules","groups":["wing","structure"],"action":"Inspect printed shells and cut spar stock to CAD-derived lengths. Dry-fit seams and spar alignment before bonding."},
            {"title":"Assemble the fuselage and tail","groups":["fuselage","tail","structure"],"action":"Dry-fit pod modules, boom and tail. Confirm the alignment datums and design incidence."},
            {"title":"Install propulsion and controls","groups":["power","controls"],"action":"Resolve motor fasteners, control hinges/linkages, servo mounting and wire routing before assembly. These details are open."},
            {"title":"Place battery and mission payload","groups":["power","payload"],"action":"Use the versioned positions, provide positive retention, then measure the actual installed CG."},
            {"title":"Measure before release","groups":["wing","tail","fuselage","power","controls","payload"],"action":"Complete structural, propulsion, control/access and manufacturing checks. Flight validation requires physical test evidence."},
        ]
        for step in sequence:
            step["verification_status"]="UNKNOWN"
        write_json(folder/"assembly.json",{"design_id":design.id,"status":"UNKNOWN","steps":sequence})
        notes="""# Fabrication candidate — release blocked

STEP and STL units: millimeters. Web mesh and canonical geometry: meters.
Printed shells use a foamed-PLA density assumption; calibrate material/process
coupons and slicing before manufacturing. No G-code is supplied. Inspect seam,
wall-thickness, support and build-orientation requirements before printing.
Carbon tube material/layup and joints have not been selected or validated.
Purchased parts in CAD are envelopes. Do not manufacture them from these meshes.

Open design items:
"""+"\n".join(f"- {item}" for item in geometry["coverage"]["open_items"])
        (folder/"FABRICATION.md").write_text(notes)
        manifest={"design_id":design.id,"baseline_id":design.baseline_id,"provider":self.engineer.label,
            "engineering_store":self.state["engineering_store"],"gate":self.state["gate"],
            "package_kind":"manufacturing candidate", "coverage":geometry["coverage"],
            "evaluations":self.state["evaluations"],"files":{}}
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.name!="manifest.json":
                import hashlib
                manifest["files"][str(path.relative_to(folder))]=hashlib.sha256(path.read_bytes()).hexdigest()
        write_json(folder/"manifest.json",manifest)
        archive=self.directory/"candidate-package.zip"
        with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as zip:
            for path in folder.rglob("*"):
                if path.is_file(): zip.write(path,str(path.relative_to(folder)))
        self.state["package_file"]=archive.name
        self.state["assembly_file"]=f"{design.id}/assembly.json"
