from audit_core.ingest.schema import AuditInput, MetricValue, Proportion
from audit_core.registry import MetricRegistry
from audit_core.checks import arithmetic


def _registry(audit_input):
    return MetricRegistry(audit_input)


def test_subtotals_pass_when_components_sum_correctly():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="DEL", value=40, location="T1", group="g1", role="component"),
        MetricValue(label="DUP", value=25, location="T1", group="g1", role="component"),
        MetricValue(label="Total", value=65, location="T1", group="g1", role="total"),
    ]
    results = arithmetic.check_subtotals(_registry(ai))
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_subtotals_fail_when_mismatch():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="DEL", value=40, location="T1", group="g1", role="component"),
        MetricValue(label="DUP", value=25, location="T1", group="g1", role="component"),
        MetricValue(label="INV", value=10, location="T1", group="g1", role="component"),
        MetricValue(label="Total", value=80, location="T1", group="g1", role="total"),
    ]
    results = arithmetic.check_subtotals(_registry(ai))
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert results[0]["evidence"]["computed_total"] == 75
    assert results[0]["evidence"]["stated_total"] == 80


def test_subtotals_ignored_when_no_total_present():
    ai = AuditInput()
    ai.metrics = [
        MetricValue(label="DEL", value=40, location="T1", group="g1", role="component"),
    ]
    results = arithmetic.check_subtotals(_registry(ai))
    assert results == []


def test_percentage_pass_within_rounding_tolerance():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate",
                   location="T3", reported_pct=90.0),
    ]
    results = arithmetic.check_percentages(ai)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_percentage_fail_when_mismatch():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate",
                   location="T3", reported_pct=92.5),
    ]
    results = arithmetic.check_percentages(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert round(results[0]["evidence"]["computed_pct"], 2) == 90.0


def test_percentage_zero_denominator_flagged_as_fail():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=0, denominator=0, label="edge_case",
                   location="T3", reported_pct=0.0),
    ]
    results = arithmetic.check_percentages(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"


def test_percentage_skipped_when_not_reported():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate", location="T3"),
    ]
    results = arithmetic.check_percentages(ai)
    assert results == []
