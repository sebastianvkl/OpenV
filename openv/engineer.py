"""Proposal adapters. Neither adapter can issue a verification verdict."""
from __future__ import annotations

import json
import os
from typing import Literal

from pydantic import Field, ValidationError

from openv.aircraft import Mission, Parameters
from openv.core import Proposal, Record


class MissionProposal(Record):
    supported: bool
    mission: Mission
    parameters: Parameters
    rationale: str
    uncovered_clauses: list[str]


class ParameterChange(Record):
    parameter: Literal[tuple(Parameters.model_fields)]
    value: float


class RedesignProposal(Record):
    """Closed wire schema: strict structured outputs cannot accept open maps."""
    problem: str
    hypothesis: str
    changes: list[ParameterChange]
    expected_effect: str


INSTRUCTIONS = """You are the proposing engineer in OpenV, a verification-first hardware V pipeline.
AI-generated hardware is a hypothesis. You cannot decide PASS, modify verifier code,
author evidence, change sourced data, or relax a frozen requirement to hide failure.
Use only the schema's fields and the supported conventional electric motor-glider family.
The runtime owns reviewed verification contracts and deterministic comparisons.
Current limits: one NACA2412 high wing, NACA0012 conventional tail, pusher motor,
3S 1300mAh battery allocation, foamed PLA shells and carbon tube spar. Many vendor
dimensions, materials and installation details are assumptions. Endurance/physical
flight and assembly remain UNKNOWN without the necessary evidence.
For initial mission decomposition, preserve every explicit user numeric target and
list every clause outside the schema or supported family in uncovered_clauses.
If a number cannot fit the schema, mark supported=false rather than relaxing it.
For unspecified targets choose a feasible provisional reference mission.
For redesign, use the ACTUAL failed measurements, current inputs and experiment
history. Propose a specific bounded parameter patch, explain mechanism and tradeoffs.
Do not pretend a change is proven until the external verifier reruns. Battery/payload
placement affect CG; increasing span changes mass, bending and stability; tail sizing
changes neutral point and mass. Consider coupled constraints and avoid repeated changes.
Geometry frame: meters, x aft from nose, y right, z up. Wing LE x=.28m, tail LE x=.88m.
Prefer small well-reasoned changes. Do not fabricate a failed first design for theater.
"""


class AstraEngineer:
    label = "Astra"

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(timeout=150,max_retries=1)
        self.model = os.environ.get("OPENV_MODEL", "gpt-6-astra")
        self.calls = []

    def _request(self, schema, task):
        task=dict(task)
        for attempt in range(3):
            # Preserve response provenance even when Pydantic's engineering
            # validators reject a syntactically valid structured model output.
            raw=self.client.responses.with_raw_response.parse(model=self.model,
                instructions=INSTRUCTIONS,input=json.dumps(task,allow_nan=False),
                text_format=schema,reasoning={"effort":"high"},max_output_tokens=6000)
            body=raw.http_response.json()
            record={"response_id":body.get("id"),"model":body.get("model"),
                "usage":body.get("usage"),"validation":"pending"}
            self.calls.append(record)
            try:
                response=raw.parse()
                if response.output_parsed is None:
                    record["validation"]="no_proposal"
                    raise RuntimeError("Astra returned no admissible structured proposal")
                record["validation"]="accepted_proposal"
                return response.output_parsed
            except ValidationError as exc:
                rejection=exc.errors(include_url=False,include_context=False)
                record.update(validation="rejected",errors=rejection)
                task["previous_proposal"]=[c["text"] for item in body.get("output",[])
                    for c in item.get("content",[]) if c.get("type")=="output_text"]
                task["validation_errors"]=rejection
                task["repair_instruction"]="Correct these input/geometry violations without changing the mission or protected contracts."
                if attempt==2:raise ValueError("Astra exhausted three structured-proposal validation attempts") from exc

    def define(self, mission_text):
        return self._request(MissionProposal, {"task":"Decompose the mission and propose initial design parameters.",
            "original_mission":mission_text,"parameter_bounds":Parameters.model_json_schema(),
            "geometry_constraints":["2 * spar_wall_m < spar_od_m",
                "spar_od_m + 2 * skin_m <= 0.10 * chord_m * taper"],
            "mission_bounds":Mission.model_json_schema()})

    def redesign(self, context):
        result = self._request(RedesignProposal, {"task":"Propose one engineering experiment from actual failure evidence.",
            "context":context,"allowed_parameters":Parameters.model_json_schema()})
        changes={entry.parameter:entry.value for entry in result.changes}
        if len(changes)!=len(result.changes):
            raise ValueError("Astra proposed duplicate parameter changes")
        return Proposal(problem=result.problem,hypothesis=result.hypothesis,
            changes=changes,expected_effect=result.expected_effect)


class FixtureEngineer:
    """Deterministic development fixture, visibly labeled in every artifact.

This is for testing without a model account, not an Astra demonstration.
"""
    label = "Offline fixture · no Astra call"
    calls = []

    def define(self, mission_text):
        return MissionProposal(supported=True,mission=Mission(text=mission_text),parameters=Parameters(),
            rationale="Explicit offline reference fixture; input text is retained but numeric targets are fixture defaults.",
            uncovered_clauses=["Offline fixture does not decompose arbitrary natural-language requirements."])

    def redesign(self, context):
        failures = {e["requirement_id"] for e in context["evaluations"] if e["status"]=="FAIL"}
        p=context["design"]["parameters"]
        if "stability-min" in failures:
            changes={"battery_x_m":max(.12,p["battery_x_m"]-.10)}
            why="Move battery forward to move CG ahead of the computed neutral point."
        elif "stability-max" in failures:
            changes={"battery_x_m":min(.46,p["battery_x_m"]+.08)}
            why="Move battery aft to reduce excessive modeled static margin."
        elif failures & {"spar","deflection"}:
            changes={"spar_od_m":min(.016,p["spar_od_m"]+.002)}
            why="Increase spar second moment of area to reduce stress and deflection."
        elif failures & {"trim","alpha"}:
            changes={"chord_m":min(.28,p["chord_m"]+.025)}
            why="Increase lifting area to reduce required lift coefficient."
        else:
            changes={"skin_m":max(.0004,p["skin_m"]-.0001)}
            why="Reduce modeled shell mass; manufacturing thickness remains unverified."
        return Proposal(problem=", ".join(sorted(failures)),hypothesis=why,changes=changes,
                        expected_effect="Fixture hypothesis only; compare fresh independent evidence.")


class VerificationOnlyEngineer:
    label="User experiment · external verification"
    calls=[]

    def define(self, mission_text):
        raise RuntimeError("Verification-only runs require an existing canonical design")

    def redesign(self, context):
        raise RuntimeError("Connect Astra to propose an engineering repair")
