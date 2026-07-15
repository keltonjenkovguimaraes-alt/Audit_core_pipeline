from audit_core.ingest.schema import AuditInput, Proportion
from audit_core.checks import statistics


def test_missing_ci_flagged():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate", location="T3"),
    ]
    results = statistics.check_missing_ci(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FLAG"
    assert results[0]["check"] == "statistics.missing_ci"


def test_ci_present_not_flagged_as_missing():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate", location="T3",
                   reported_ci=(0.85, 0.97)),
    ]
    results = statistics.check_missing_ci(ai)
    assert results == []


def test_degenerate_ci_zero_successes_flagged_with_rule_of_three():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=0, denominator=40, label="FP_rate", location="T3"),
    ]
    results = statistics.check_degenerate_ci(ai)
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "FLAG"
    assert "reference_wilson_ci" in r["evidence"]
    assert "reference_clopper_pearson_ci" in r["evidence"]
    # n=40 >= 30, so rule-of-three bound should be included
    assert "reference_rule_of_three_upper_bound" in r["evidence"]
    assert abs(r["evidence"]["reference_rule_of_three_upper_bound"] - 0.075) < 1e-9


def test_degenerate_ci_zero_successes_small_n_uses_note_not_rule_of_three():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=0, denominator=12, label="rare_event", location="T3"),
    ]
    results = statistics.check_degenerate_ci(ai)
    assert len(results) == 1
    evidence = results[0]["evidence"]
    assert "reference_rule_of_three_upper_bound" not in evidence
    assert "note" in evidence


def test_degenerate_ci_all_successes_flagged():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=15, denominator=15, label="perfect_rate", location="T3"),
    ]
    results = statistics.check_degenerate_ci(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FLAG"


def test_non_degenerate_proportion_not_flagged():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate", location="T3"),
    ]
    results = statistics.check_degenerate_ci(ai)
    assert results == []


def test_small_n_without_ci_flagged():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=9, denominator=12, label="INV_rate", location="T3"),
    ]
    results = statistics.check_small_n_point_estimate(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FLAG"


def test_small_n_with_ci_not_flagged():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=9, denominator=12, label="INV_rate", location="T3",
                   reported_ci=(0.4, 0.97)),
    ]
    results = statistics.check_small_n_point_estimate(ai)
    assert results == []


def test_large_n_without_ci_not_flagged_as_small_n():
    ai = AuditInput()
    ai.proportions = [
        Proportion(numerator=36, denominator=40, label="DEL_rate", location="T3"),
    ]
    results = statistics.check_small_n_point_estimate(ai)
    assert results == []
