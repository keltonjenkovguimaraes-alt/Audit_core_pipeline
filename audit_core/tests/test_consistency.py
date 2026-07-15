from audit_core.ingest.schema import AuditInput, MetricValue, Proportion
from audit_core.registry import MetricRegistry
from audit_core.checks import consistency


def test_same_value_across_locations_not_flagged():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="total_strains", value=12, location="Abstract"),
        MetricValue(label="total_strains", value=12, location="Methods"),
    ]
    results = consistency.check_cross_location_drift(MetricRegistry(ai))
    assert results == []


def test_drifted_value_across_locations_flagged():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="total_strains", value=12, location="Abstract"),
        MetricValue(label="total_strains", value=15, location="Methods"),
    ]
    results = consistency.check_cross_location_drift(MetricRegistry(ai))
    assert len(results) == 1
    assert results[0]["status"] == "FLAG"
    assert results[0]["check"] == "consistency.cross_location_drift"


def test_label_matching_is_case_and_whitespace_insensitive():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="Total Strains", value=12, location="Abstract"),
        MetricValue(label="  total strains  ", value=15, location="Methods"),
    ]
    results = consistency.check_cross_location_drift(MetricRegistry(ai))
    assert len(results) == 1


def test_single_occurrence_not_flagged():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="total_strains", value=12, location="Abstract"),
    ]
    results = consistency.check_cross_location_drift(MetricRegistry(ai))
    assert results == []


def test_drift_detection_works_across_proportions_too():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=9, denominator=12, label="INV_confirmation", location="Table 3"),
        Proportion(numerator=9, denominator=15, label="INV_confirmation", location="Abstract"),
    ]
    results = consistency.check_cross_location_drift(MetricRegistry(ai))
    assert len(results) == 1
