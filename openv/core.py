"""Domain-independent contracts, immutable evidence and deterministic evaluation.

This module has no model API, CAD library or aircraft formulas. A model proposal
never contains an evaluation or evidence object.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

CORE_REVISION=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]


def source_revision():
    """Conservative provenance for cross-module engineering dependencies."""
    root=Path(__file__).parent
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob("*.py"))}
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()


ENGINEERING_REVISION=source_revision()


def uid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def digest(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Status(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Property(Record):
    value: float | str
    unit: str
    quality: Literal["sourced", "measured", "computed", "assumed", "estimated"]
    source: str


class Component(Record):
    id: str
    name: str
    manufacturer: str | None = None
    part_number: str | None = None
    revision: str = "1"
    properties: dict[str, Property] = Field(default_factory=dict)


class Interface(Record):
    id: str
    endpoints: tuple[str, ...]
    kind: str
    definition: dict[str, Any]
    requirement_ids: tuple[str, ...] = ()


class Contract(Record):
    id: str
    method: str
    metric: str
    operator: Literal[">=", "<=", "=="]
    threshold: float
    unit: str
    scope: str
    revision: str = "1"


class Requirement(Record):
    id: str
    statement: str
    level: Literal["mission", "system", "integration", "component"]
    owner: str
    contracts: tuple[Contract, ...]
    mandatory: bool = True
    origin: str = "mission"


class DesignVersion(Record):
    id: str = Field(default_factory=lambda: uid("design"))
    parent_id: str | None = None
    baseline_id: str
    parameters: dict[str, float]
    component_ids: tuple[str, ...] = ()
    experiment_id: str | None = None


class HardwareSystem(Record):
    id: str = Field(default_factory=lambda: uid("system"))
    mission: str
    baseline_id: str
    domain: str
    architecture: dict[str, Any]
    requirements: tuple[Requirement, ...]
    components: tuple[Component, ...]
    interfaces: tuple[Interface, ...]
    scenario: dict[str, Any]


class Measurement(Record):
    value: float | None
    unit: str
    admissible: bool = True
    reason: str = ""


class ToolOutput(Record):
    metrics: dict[str, Measurement]
    raw: dict[str, Any]
    assumptions: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()


class Evidence(Record):
    id: str = Field(default_factory=lambda: uid("evidence"))
    design_id: str
    baseline_id: str
    method: str
    tool_version: str
    fingerprint: str
    inputs: dict[str, Any]
    output: ToolOutput
    output_hash: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Evaluation(Record):
    requirement_id: str
    status: Status
    evidence_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    stale_evidence_ids: tuple[str, ...] = ()


class Experiment(Record):
    id: str
    problem: str
    hypothesis: str
    change: dict[str, float]
    expected_effect: str
    from_design: str
    to_design: str
    before_evidence: tuple[str, ...]
    invalidated_evidence: tuple[str, ...]
    after_evidence: tuple[str, ...] = ()
    actual_effect: dict[str, Any] = Field(default_factory=dict)


class Proposal(Record):
    problem: str
    hypothesis: str
    changes: dict[str, float]
    expected_effect: str


class Method:
    def __init__(self, name: str, version: str, dependencies: tuple[str, ...],
                 run: Callable[[dict[str, Any]], ToolOutput]):
        self.name, self.version = name, version
        self.dependencies, self.run = dependencies, run
        import inspect
        module=inspect.getmodule(run)
        source=Path(module.__file__) if module and getattr(module,"__file__",None) else None
        self.source_hash=hashlib.sha256(source.read_bytes()).hexdigest() if source and source.is_file() else "unavailable"

    def inputs(self, context: dict[str, Any]) -> dict[str, Any]:
        return {key: context[key] for key in self.dependencies}

    def fingerprint(self, context: dict[str, Any], contracts: tuple[Contract, ...]) -> str:
        return digest({"method": self.name, "version": self.version, "graph": 1,"core_revision":CORE_REVISION,
                       "engineering_revision":ENGINEERING_REVISION,"method_source_hash":self.source_hash,
                       "inputs": self.inputs(context),
                       "contracts": [c.model_dump() for c in contracts if c.method == self.name]})


class VerificationEngine:
    def __init__(self, methods: list[Method]):
        self.methods = {m.name: m for m in methods}

    def verify(self, design: DesignVersion, requirements: tuple[Requirement, ...],
               context: dict[str, Any], previous: tuple[Evidence, ...] = ()) -> tuple[Evidence, ...]:
        contracts = tuple(c for r in requirements for c in r.contracts)
        outputs = []
        for name in dict.fromkeys(c.method for c in contracts):
            method = self.methods.get(name)
            if method is None:
                continue
            fingerprint = method.fingerprint(context, contracts)
            reusable = [e for e in previous if e.method == name and e.fingerprint == fingerprint
                        and digest(e.output) == e.output_hash]
            if reusable:
                outputs.extend(reusable)
                continue
            inputs = method.inputs(context)
            try:
                output = method.run(inputs)
                digest(output)  # Reject non-JSON/nonfinite solver data before admission.
            except Exception as exc:
                output = ToolOutput(metrics={}, raw={"error": f"{type(exc).__name__}: {exc}"})
            outputs.append(Evidence(design_id=design.id, baseline_id=design.baseline_id,
                                    method=name, tool_version=method.version, fingerprint=fingerprint,
                                    inputs=inputs, output=output, output_hash=digest(output)))
        return tuple(outputs)

    def evaluate(self, requirements: tuple[Requirement, ...], context: dict[str, Any],
                 evidence: tuple[Evidence, ...]) -> tuple[Evaluation, ...]:
        contracts = tuple(c for r in requirements for c in r.contracts)
        results = []
        for requirement in requirements:
            states, ids, stale, reasons = [], [], [], []
            for contract in requirement.contracts:
                method = self.methods.get(contract.method)
                matches = []
                if method:
                    expected = method.fingerprint(context, contracts)
                    for item in evidence:
                        if item.method != method.name:
                            continue
                        if item.fingerprint != expected:
                            stale.append(item.id)
                        elif item.output_hash == digest(item.output) and item.tool_version == method.version:
                            matches.append(item)
                if not matches:
                    states.append(Status.UNKNOWN)
                    reasons.append(f"{contract.id}: no current admissible evidence")
                    continue
                for item in matches:
                    metric = item.output.metrics.get(contract.metric)
                    if (metric is None or metric.value is None or not metric.admissible
                            or metric.unit != contract.unit or not math.isfinite(metric.value)):
                        states.append(Status.UNKNOWN)
                        reasons.append(f"{contract.id}: {metric.reason if metric else 'metric absent'}")
                        ids.append(item.id)
                        continue
                    value, target = metric.value, contract.threshold
                    passed = {">=": value >= target, "<=": value <= target, "==": value == target}[contract.operator]
                    states.append(Status.PASS if passed else Status.FAIL)
                    ids.append(item.id)
                    reasons.append(f"{contract.metric}: {value:.5g} {contract.unit} {contract.operator} {target:g}")
            status = (Status.FAIL if Status.FAIL in states else
                      Status.PASS if states and all(s == Status.PASS for s in states) else Status.UNKNOWN)
            results.append(Evaluation(requirement_id=requirement.id, status=status,
                                      evidence_ids=tuple(dict.fromkeys(ids)), reasons=tuple(reasons),
                                      stale_evidence_ids=tuple(dict.fromkeys(stale))))
        return tuple(results)


def gate(requirements: tuple[Requirement, ...], evaluations: tuple[Evaluation, ...]) -> Status:
    indexed = {e.requirement_id: e.status for e in evaluations}
    states = [indexed.get(r.id, Status.UNKNOWN) for r in requirements if r.mandatory]
    if Status.FAIL in states:
        return Status.FAIL
    return Status.PASS if states and all(s == Status.PASS for s in states) else Status.UNKNOWN
