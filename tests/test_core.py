import pytest
from pydantic import ValidationError

from openv.core import (Contract, DesignVersion, Measurement, Method, Proposal,
                        Requirement, Status, ToolOutput, VerificationEngine, gate)


def setup():
    # A non-aircraft dimensional check exercises the same core used by the demo.
    requirement = Requirement(id="fit", statement="Bracket fits the machine", level="component",
        owner="bracket", contracts=(Contract(id="fit-c", method="caliper", metric="width",
        operator="<=", threshold=10, unit="mm", scope="nominal drawing dimension"),))
    engine = VerificationEngine([Method("caliper", "1", ("width",),
        lambda x: ToolOutput(metrics={"width": Measurement(value=x["width"], unit="mm")}, raw=x))])
    design = DesignVersion(baseline_id="baseline", parameters={"width": 9})
    return requirement, engine, design


def test_known_good_bad_and_missing():
    r, engine, d = setup()
    for width, expected in [(9, Status.PASS), (11, Status.FAIL)]:
        context = {"width": width}
        evidence = engine.verify(d, (r,), context)
        evaluation = engine.evaluate((r,), context, evidence)[0]
        assert evaluation.status == expected
        assert evaluation.evidence_ids
    assert engine.evaluate((r,), {"width": 9}, ())[0].status == Status.UNKNOWN


def test_change_invalidates_before_rerun_and_old_result_cannot_pass():
    r, engine, d = setup()
    evidence = engine.verify(d, (r,), {"width": 9})
    result = engine.evaluate((r,), {"width": 12}, evidence)[0]
    assert result.status == Status.UNKNOWN
    assert result.stale_evidence_ids == (evidence[0].id,)
    refreshed = engine.verify(d, (r,), {"width": 12}, previous=evidence)
    assert refreshed[0].id != evidence[0].id
    assert engine.evaluate((r,), {"width": 12}, refreshed)[0].status == Status.FAIL


def test_unrelated_change_reuses_exact_evidence():
    r, engine, d = setup()
    evidence = engine.verify(d, (r,), {"width": 9, "color": "red"})
    assert engine.verify(d, (r,), {"width": 9, "color": "blue"}, evidence) == evidence


def test_tool_success_without_metric_does_not_pass():
    r, _, d = setup()
    engine = VerificationEngine([Method("caliper", "1", ("width",),
        lambda x: ToolOutput(metrics={}, raw={"success": True}))])
    evidence = engine.verify(d, (r,), {"width": 9})
    assert engine.evaluate((r,), {"width": 9}, evidence)[0].status == Status.UNKNOWN


def test_units_and_assumed_claim_rejected():
    r, _, d = setup()
    for metric in [Measurement(value=9, unit="m"),
                   Measurement(value=9, unit="mm", admissible=False, reason="unmeasured")]:
        engine = VerificationEngine([Method("caliper", "1", ("width",),
            lambda x: ToolOutput(metrics={"width": metric}, raw=x))])
        e = engine.verify(d, (r,), {"width": 9})
        assert engine.evaluate((r,), {"width": 9}, e)[0].status == Status.UNKNOWN


def test_model_cannot_submit_status_or_threshold():
    for forbidden in [{"status": "PASS"}, {"threshold": 1000}, {"evidence": {}}]:
        with pytest.raises(ValidationError):
            Proposal(problem="fit", hypothesis="narrower", changes={"width": 9}, expected_effect="fits", **forbidden)


def test_empty_gate_and_missing_method_unknown():
    r, _, d = setup()
    engine = VerificationEngine([])
    assert gate((), ()) == Status.UNKNOWN
    assert engine.evaluate((r,), {}, ())[0].status == Status.UNKNOWN


def test_contract_change_tool_version_and_tampering_invalidate():
    r, engine, d = setup()
    evidence = engine.verify(d, (r,), {"width": 9})
    new_contract = r.contracts[0].model_copy(update={"threshold": 8})
    r2 = r.model_copy(update={"contracts": (new_contract,)})
    assert engine.evaluate((r2,), {"width": 9}, evidence)[0].status == Status.UNKNOWN
    engine.methods["caliper"].version = "2"
    assert engine.evaluate((r,), {"width": 9}, evidence)[0].status == Status.UNKNOWN
    engine.methods["caliper"].version = "1"
    evidence[0].output.metrics["width"] = Measurement(value=1, unit="mm")
    assert engine.evaluate((r,), {"width": 9}, evidence)[0].status == Status.UNKNOWN


def test_conflicting_current_evidence_does_not_select_favorable():
    r, engine, d = setup()
    good = engine.verify(d, (r,), {"width": 9})
    engine.methods["caliper"].run = lambda x: ToolOutput(metrics={"width": Measurement(value=11, unit="mm")}, raw=x)
    bad = engine.verify(d, (r,), {"width": 9})
    assert engine.evaluate((r,), {"width": 9}, good + bad)[0].status == Status.FAIL

