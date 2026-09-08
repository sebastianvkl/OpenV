"""One small public service: static UI, bounded jobs and versioned artifacts."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()
ROOT=Path(__file__).resolve().parent.parent
ARTIFACTS=Path(os.environ.get("OPENV_ARTIFACTS",str(ROOT/"artifacts"))).resolve()
ARTIFACTS.mkdir(parents=True,exist_ok=True)
active=None
background_tasks=set()
admission_lock=asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    from openv.pipeline import write_json
    for file in ARTIFACTS.glob("*/run.json"):
        try:
            data=json.loads(file.read_text())
            if data["status"] in ("running","queued"):
                data.update(status="interrupted",stop_reason="service_restarted")
                write_json(file,data)
        except (KeyError,ValueError):
            pass
    yield
    if active and active.returncode is None:
        active.terminate()
        try: await asyncio.wait_for(active.wait(),5)
        except asyncio.TimeoutError: active.kill()


app=FastAPI(title="OpenV engineering pipeline",lifespan=lifespan)


class RunRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    mission: str = Field(min_length=10,max_length=4000)
    offline: bool = False
    source_run_id: str | None = None
    source_design_id: str | None = None
    parameter_changes: dict[str,float] = Field(default_factory=dict)
    mission_changes: dict[str,float] = Field(default_factory=dict)
    verify_only: bool = False


@app.get("/api/config")
def config():
    return {"model":os.environ.get("OPENV_MODEL","gpt-6-astra"),
        "astra_ready":bool(os.environ.get("OPENAI_API_KEY")),
        "dalus_authorized":(Path(os.environ.get("OPENV_AUTH_DIR",str(ROOT/".openv")))/"dalus-tokens.json").exists(),
        "store":os.environ.get("OPENV_STORE","local"),
        "fixtures_enabled":os.environ.get("OPENV_ALLOW_FIXTURES")=="1",
        "busy":active is not None and active.returncode is None}


@app.get("/api/runs")
def runs():
    records=[]
    for path in sorted(ARTIFACTS.glob("*/run.json"),key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            d=json.loads(path.read_text())
            item={k:d.get(k) for k in ("id","status","stage","provider","gate","current_design_id")}
            hardware=d.get("system",{})
            scenario=hardware.get("scenario",{})
            version=next((v for v in d.get("versions",[]) if v["id"]==d.get("current_design_id")),None)
            if version:
                from openv.core import digest
                item.update(scenario=scenario,visualization_file=d.get("visualization_file"),
                    comparison_key=digest({"parameters":version["parameters"],
                        "components":hardware.get("components"),"requirements":hardware.get("requirements"),
                        "scenario":{k:v for k,v in scenario.items() if k not in ("cruise_mps","altitude_m","load_factor")}}))
            records.append(item)
        except ValueError:
            continue
    return records[:50]


@app.get("/api/runs/{run_id}")
def run(run_id:str):
    if not run_id.replace("-","").isalnum(): raise HTTPException(404)
    path=ARTIFACTS/run_id/"run.json"
    if not path.exists(): raise HTTPException(404)
    return json.loads(path.read_text())


@app.post("/api/runs",status_code=202)
async def create_run(request:RunRequest):
    async with admission_lock:
        return await admit_run(request)


async def admit_run(request:RunRequest):
    global active
    if active and active.returncode is None:
        raise HTTPException(409,"An engineering run is active. Please wait for it to finish.")
    if request.offline and os.environ.get("OPENV_ALLOW_FIXTURES")!="1":
        raise HTTPException(403,"Offline fixture runs are disabled on this deployment.")
    if not request.offline and not request.verify_only and not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(503,"Astra credentials are not configured. Published runs remain inspectable.")
    seed=None
    if request.source_run_id:
        parent=run(request.source_run_id)
        version=next((v for v in parent.get("versions",[]) if v["id"]==(request.source_design_id or parent.get("current_design_id"))),None)
        if version is None:raise HTTPException(422,"Choose an existing design version")
        from openv.aircraft import Mission,Parameters
        from pydantic import ValidationError
        if not set(request.parameter_changes).issubset(Parameters.model_fields):raise HTTPException(422,"Unknown design parameter")
        if not set(request.mission_changes).issubset(set(Mission.model_fields)-{"text"}):raise HTTPException(422,"Unknown mission parameter")
        try:
            p=Parameters.model_validate({**version["parameters"],**request.parameter_changes})
            m=Mission.model_validate({**parent["system"]["scenario"],**request.mission_changes})
        except ValidationError as exc:raise HTTPException(422,str(exc)) from exc
        actual_parameters={k:v for k,v in request.parameter_changes.items() if version["parameters"][k]!=v}
        actual_mission={k:v for k,v in request.mission_changes.items() if parent["system"]["scenario"][k]!=v}
        baseline_changed=bool(actual_mission)
        seed={"system":parent["system"],"definition":{"supported":True,"mission":m.model_dump(),"parameters":p.model_dump(),
            "rationale":"Explicit user perturbation of existing canonical state", "uncovered_clauses":parent.get("mission_proposal",{}).get("uncovered_clauses",[])},
            "origin":{"run_id":request.source_run_id,"design_id":version["id"],"baseline_id":version["baseline_id"],"mission_amended":baseline_changed},
            "before_evaluations":parent.get("evaluations",[]),"before_evidence_ids":[e["id"] for e in parent.get("evidence",[])],
            "changes":{**actual_parameters,**{f"mission.{k}":v for k,v in actual_mission.items()}},
            "hypothesis":"Explore the effect of the requested parameter/mission change using independent engineering checks."}
        # Historical versions must use their own evidence, not the current run's.
        history=ARTIFACTS/request.source_run_id/version["id"]/"verification.json"
        if history.exists():
            evidence=json.loads(history.read_text());seed["before_evaluations"]=evidence["evaluations"]
            seed["before_evidence_ids"]=[e["id"] for e in evidence["evidence"]]
    elif request.verify_only or request.parameter_changes or request.mission_changes:
        raise HTTPException(422,"A source design is required for perturbation/verification-only runs")
    now=time.time()
    recent=sum(1 for p in ARTIFACTS.glob("*/run.json") if now-p.stat().st_ctime<86400)
    if recent>=int(os.environ.get("OPENV_MAX_DAILY_RUNS","20")):
        raise HTTPException(429,"Today's configured engineering run budget is exhausted.")
    from openv.core import uid
    from openv.pipeline import write_json
    run_id=uid("run")
    folder=ARTIFACTS/run_id
    folder.mkdir()
    log=(folder/"execution.log").open("w")
    command=[sys.executable,"-m","openv.cli",request.mission,"--run-id",run_id,
             "--max-experiments",os.environ.get("OPENV_MAX_EXPERIMENTS","5")]
    if request.offline:command.append("--offline")
    if seed:
        write_json(folder/"seed.json",seed)
        command.extend(["--seed",str(folder/"seed.json")])
    if request.verify_only:command.append("--verify-only")
    active=await asyncio.create_subprocess_exec(*command,cwd=ROOT,stdout=log,stderr=log)
    process=active
    async def supervise():
        try:
            await asyncio.wait_for(process.wait(),float(os.environ.get("OPENV_RUN_TIMEOUT","1800"))+30)
            if process.returncode:
                path=folder/"run.json"
                data=json.loads(path.read_text()) if path.exists() else {"id":run_id}
                if data.get("status") not in ("error","interrupted"):
                    data.update(status="error",gate="UNKNOWN",stop_reason="worker_failed",stage="error")
                    write_json(path,data)
        except asyncio.TimeoutError:
            process.kill();await process.wait()
            path=folder/"run.json"
            data=json.loads(path.read_text()) if path.exists() else {"id":run_id}
            data.update(status="interrupted",stage="interrupted",gate="UNKNOWN",stop_reason="hard_time_limit")
            write_json(path,data)
        finally:
            log.close()
    task=asyncio.create_task(supervise())
    background_tasks.add(task);task.add_done_callback(background_tasks.discard)
    return {"id":run_id,"status":"queued"}


@app.get("/artifacts/{run_id}/{relative:path}")
def artifact(run_id:str,relative:str):
    if not run_id.replace("-","").isalnum():raise HTTPException(404)
    root=(ARTIFACTS/run_id).resolve()
    file=(root/relative).resolve()
    if not file.is_relative_to(root) or not file.is_file() or file.suffix not in {".json",".stl",".step",".zip",".csv",".md"}:
        raise HTTPException(404)
    return FileResponse(file)


DIST=ROOT/"web/dist"
if DIST.exists():
    app.mount("/",StaticFiles(directory=DIST,html=True),name="web")
