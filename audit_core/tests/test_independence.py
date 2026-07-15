from audit_core.ingest.schema import AuditInput, ValidationSet
from audit_core.checks import independence


def test_disjoint_sets_pass():
    ai = AuditInput()
    ai.validation_sets = [
        ValidationSet(name="calibration_set", ids={"a", "b", "c"}, location="M2.1",
                      claimed_independent_from=["truth_set"]),
        ValidationSet(name="truth_set", ids={"d", "e", "f"}, location="M2.2"),
    ]
    results = independence.check_overlap(ai)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_overlapping_sets_fail():
    ai = AuditInput()
    ai.validation_sets = [
        ValidationSet(name="calibration_set", ids={"a", "b", "c"}, location="M2.1",
                      claimed_independent_from=["truth_set"]),
        ValidationSet(name="truth_set", ids={"c", "d", "e"}, location="M2.2"),
    ]
    results = independence.check_overlap(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert results[0]["evidence"]["overlap_count"] == 1


def test_reference_to_unknown_set_flagged():
    ai = AuditInput()
    ai.validation_sets = [
        ValidationSet(name="calibration_set", ids={"a", "b"}, location="M2.1",
                      claimed_independent_from=["nonexistent_set"]),
    ]
    results = independence.check_overlap(ai)
    assert len(results) == 1
    assert results[0]["check"] == "independence.unknown_reference"


def test_no_independence_claims_produces_no_results():
    ai = AuditInput()
    ai.validation_sets = [
        ValidationSet(name="some_set", ids={"a", "b"}, location="M2.1"),
    ]
    results = independence.check_overlap(ai)
    assert results == []
