"""One public entry point for the website, CLI and reference demo."""
from __future__ import annotations

import json
import os
import shutil
import time
import zipfile
from pathlib import Path

from openv.core import (Contract, Evidence, Experiment, Requirement, Status,
                        VerificationEngine, digest, gate, uid)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False))
    temporary.replace(path)


class Pipeline:
    def __init__(self, directory: Path, engineer, store=None, domain=None):
        self.directory, self.engineer, self.store = directory,engineer,store
        self.directory.mkdir(parents=True,exist_ok=True)
        self.state={"id":directory.name,"status":"running","stage":"mission","provider":engineer.label,
            "engineering_store":"local fixture" if store is None else "Dalus MCP",
            "events":[],"versions":[],"experiments":[],"evaluations":[],"evidence":[],"stop_reason":None}
        self.started=time.monotonic()
        from openv.domains import get_domain
        self.domain=domain or get_domain()
        self.engine=VerificationEngine(self.domain.methods())

    def event(self, kind, message, **details):
        self.state["stage"]=kind
        self.state["events"].append({"kind":kind,"message":message,"elapsed_s":round(time.monotonic()-self.started,2),**details})
        self.save()

    def save(self):
        self.state["model_calls"]=self.engineer.calls
        write_json(self.directory/"run.json",self.state)

    def context(self, hardware, design, geometry):
        # Derived mass properties embed each input/source and material assumption.
        # A source, placement or geometry change therefore propagates transitively.
        return self.domain.context(hardware,design,geometry)

    def geometry(self, design, hardware):
        self.event("design","Generating parametric CAD and CAD-derived mass properties",design_id=design.id)
        directory=self.directory/design.id
        geometry=self.domain.build(design,hardware,directory)
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

    def run(self,mission_text: str,max_experiments=5,seed=None):
        try:
            return self._run(mission_text,max_experiments,seed)
        except Exception as exc:
            self.state["status"]="error"
            self.state["gate"]="UNKNOWN"
            if self.store:self.state["dalus"]=self.store.public_ref()
            self.state["stop_reason"]=f"{type(exc).__name__}: {exc}"
            self.event("error","Execution stopped; existing evidence remains version-bound")
            raise

    def _run(self,mission_text,max_experiments,seed=None):
        self.event("mission","Proposing mission requirements, architecture and initial design")
        if seed:
            definition=self.domain.read_seed(seed)
            self.state["origin"]=seed["origin"]
        else:
            definition=self.engineer.define(mission_text)
        self.state["mission_proposal"]=definition.model_dump()
        if not definition.supported:
            self.state.update(status="complete",stop_reason="unsupported_mission",gate="UNKNOWN")
            self.event("complete","Requested mission is outside current domain coverage")
            return self.state
        hardware,design=self.domain.branch(seed,definition) if seed else self.domain.define(definition,mission_text)
        user_experiment=None
        if seed:
            experiment_id=uid("user-experiment")
            design=design.model_copy(update={"parent_id":seed["origin"]["design_id"],"experiment_id":experiment_id})
            user_experiment=Experiment(id=experiment_id,problem="User requested a design or mission perturbation",
                hypothesis=seed["hypothesis"],change=seed["changes"],
                expected_effect="Recompute evidence for this branch; inspect the actual engineering response.",
                from_design=seed["origin"]["design_id"],to_design=design.id,
                before_evidence=tuple(seed["before_evidence_ids"]),invalidated_evidence=tuple(seed["before_evidence_ids"]))
            self.state["user_experiment"]=user_experiment.model_dump()
            self.state["gate"]="UNKNOWN"
            self.event("invalidated","New branch: historical evidence is retained, pending fresh verification",experiment=user_experiment.model_dump())
        self.state["system"]=hardware.model_dump()
        if self.store:
            self.state["dalus"]=self.store.create_system(hardware,design)
            if user_experiment:self.store.record_user_experiment(user_experiment)
        self.event("requirements","Mission baseline and verification contracts frozen",baseline_id=hardware.baseline_id)
        geometry=self.geometry(design,hardware)
        context=self.context(hardware,design,geometry)
        evidence,evaluations=self.verify(hardware,design,context)
        if seed:
            previous=seed["before_evaluations"]
            actual={e.requirement_id:{"before":next((p["status"] for p in previous if p["requirement_id"]==e.requirement_id),"UNKNOWN"),
                                     "after":e.status.value,"reasons":list(e.reasons)} for e in evaluations}
            experiment=user_experiment.model_copy(update={"after_evidence":tuple(e.id for e in evidence),"actual_effect":actual})
            self.state["user_experiment"]=experiment.model_dump()
            if self.store:self.store.complete_experiment(experiment)
            self.event("experiment-complete","User perturbation evaluated against explicit baseline",experiment=experiment.model_dump())
        stop="verification_only" if max_experiments==0 else "experiment_limit"
        for _ in range(max_experiments):
            if time.monotonic()-self.started>float(os.environ.get("OPENV_RUN_TIMEOUT","1800")):
                stop="time_limit"; break
            failures=[e for e in evaluations if e.status==Status.FAIL]
            if not failures:
                stop="verified_modeled_checks_with_unknowns" if any(e.status==Status.UNKNOWN for e in evaluations) else "requirements_passed"
                break
            self.event("redesign","Sending actual failure evidence to the proposing engineer")
            proposal_context={"system":hardware.model_dump(),"design":design.model_dump(),
                "evaluations":[e.model_dump() for e in evaluations],
                "verification_inputs":context,
                "evidence":[e.model_dump(exclude={"inputs"}) for e in evidence],
                "context_note":"Repeated input snapshots are supplied once in verification_inputs. Full immutable evidence retains every original input and fingerprint.",
                "experiments":self.state["experiments"][-3:]}
            if self.state.get("user_experiment"):
                proposal_context["accepted_user_experiment"]=self.state["user_experiment"]
                proposal_context["baseline_note"]=("The user explicitly authorized the recorded mission amendments. "
                    "The current numeric scenario and frozen contracts govern this run. Original mission prose and uncovered "
                    "clauses are retained for traceability; do not restore superseded numeric targets or relax current ones.")
            for attempt in range(3):
                proposal=self.engineer.redesign(proposal_context)
                experiment_id=uid("experiment")
                try:
                    candidate=self.domain.patch(design,proposal.changes,experiment_id)
                    break
                except ValueError as exc:
                    self.event("proposal-rejected",str(exc))
                    proposal_context["proposal_validation_error"]=str(exc)
                    if attempt==2:
                        raise ValueError("Proposer exhausted schema/engineering repair attempts") from exc
            # Publish invalidation before invoking CAD/solvers. All geometry-dependent
            # consumers are stale here; unrelated electrical evidence remains applicable.
            pending_context=self.domain.pending_context(context,candidate)
            pending_evaluations=self.engine.evaluate(hardware.requirements,pending_context,evidence)
            invalidated=tuple(dict.fromkeys(id for evaluation in pending_evaluations for id in evaluation.stale_evidence_ids))
            before=tuple(e.id for e in evidence)
            exp=Experiment(id=experiment_id,problem=proposal.problem,hypothesis=proposal.hypothesis,
                change=proposal.changes,expected_effect=proposal.expected_effect,from_design=design.id,to_design=candidate.id,
                before_evidence=before,invalidated_evidence=invalidated)
            self.state["experiments"].append(exp.model_dump())
            self.state["current_design_id"]=candidate.id
            self.state["evaluations"]=[e.model_dump() for e in pending_evaluations]
            self.state["gate"]="UNKNOWN"
            self.event("invalidated","Candidate committed; dependent evidence is stale",experiment=exp.model_dump())
            if self.store:
                self.store.record_experiment(hardware,design,candidate,exp,self.state["evaluations"])
            geometry=self.geometry(candidate,hardware)
            new_context=self.context(hardware,candidate,geometry)
            new_evidence,new_evaluations=self.verify(hardware,candidate,new_context,evidence)
            actual={e.requirement_id:{"before":next(old.status.value for old in evaluations if old.requirement_id==e.requirement_id),
                                     "after":e.status.value,"reasons":list(e.reasons)} for e in new_evaluations}
            exp=exp.model_copy(update={"after_evidence":tuple(e.id for e in new_evidence),"actual_effect":actual})
            self.state["experiments"][-1]=exp.model_dump()
            if self.store:
                self.store.complete_experiment(exp)
            design,context,evidence,evaluations=candidate,new_context,new_evidence,new_evaluations
            self.event("experiment-complete","Experiment recorded with actual results",experiment_id=exp.id)
        self.state["model_calls"]=self.engineer.calls
        if stop=="experiment_limit" and not any(e.status==Status.FAIL for e in evaluations):
            stop="verified_modeled_checks_with_unknowns" if any(e.status==Status.UNKNOWN for e in evaluations) else "requirements_passed"
        if seed and self.engineer.label=="Astra" and not self.engineer.calls:
            self.state["provider"]="External verification · no Astra repair needed"
        self.state["stop_reason"]=stop
        self.package(hardware,design,geometry)
        self.state["status"]="complete"
        self.event("complete","Candidate package ready; inspect verification scope and open requirements")
        return self.state

    def package(self,hardware,design,geometry):
        from openv.core import ENGINEERING_REVISION,source_revision
        if source_revision()!=ENGINEERING_REVISION:
            raise RuntimeError("Runtime source changed during this run; cannot package inconsistent regeneration source")
        self.event("package","Packaging this design version, evidence, BOM and fabrication notes")
        folder=self.directory/design.id
        write_json(folder/"system.json",hardware.model_dump())
        write_json(folder/"experiments.json",([self.state["user_experiment"]] if "user_experiment" in self.state else [])+self.state["experiments"])
        source_dir=folder/"source"
        source_dir.mkdir(exist_ok=True)
        root=Path(__file__).resolve().parent.parent
        shutil.copytree(root/"openv",source_dir/"openv",ignore=shutil.ignore_patterns("__pycache__","*.pyc"),dirs_exist_ok=True)
        for name in ("pyproject.toml","requirements-lock.txt","LICENSE"):
            shutil.copy2(root/name,source_dir/name)
        domain_files=self.domain.package(folder,hardware,design,geometry)
        manifest={"design_id":design.id,"baseline_id":design.baseline_id,"provider":self.state["provider"],
            "model_calls":self.engineer.calls,"origin":self.state.get("origin"),
            "engineering_revision":ENGINEERING_REVISION,
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
        self.state.update(domain_files)
