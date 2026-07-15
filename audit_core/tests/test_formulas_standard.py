import pytest
from audit_core.formulas import standard


def test_wilson_score_interval_known_case():
    # 36/40 = 0.9; Wilson 95% CI should bracket 0.9 and be narrower than [0,1]
    low, high = standard.wilson_score_interval(36, 40)
    assert 0.0 < low < 0.9 < high < 1.0


def test_wilson_score_interval_handles_zero_successes():
    low, high = standard.wilson_score_interval(0, 40)
    assert low == 0.0
    assert 0.0 < high < 0.2


def test_wilson_score_interval_handles_all_successes():
    low, high = standard.wilson_score_interval(40, 40)
    assert high == 1.0
    assert 0.8 < low < 1.0


def test_wilson_score_interval_rejects_zero_n():
    with pytest.raises(ValueError):
        standard.wilson_score_interval(0, 0)


def test_clopper_pearson_interval_is_wider_or_equal_to_wilson_at_extremes():
    # Clopper-Pearson is conservative; at k=0 it should give upper bound >= Wilson's
    cp_low, cp_high = standard.clopper_pearson_interval(0, 40)
    w_low, w_high = standard.wilson_score_interval(0, 40)
    assert cp_high >= w_high


def test_rule_of_three_bound_matches_known_formula():
    assert standard.rule_of_three_bound(40) == pytest.approx(3 / 40)
    assert standard.rule_of_three_bound(30) == pytest.approx(0.1)


def test_rule_of_three_rejects_zero_n():
    with pytest.raises(ValueError):
        standard.rule_of_three_bound(0)


def test_is_rule_of_three_valid_n():
    assert standard.is_rule_of_three_valid_n(30) is True
    assert standard.is_rule_of_three_valid_n(29) is False
    assert standard.is_rule_of_three_valid_n(12) is False


def test_precision_recall_f1_known_values():
    # TP=36, FP=4, FN=4 -> precision=recall=0.9, f1=0.9
    assert standard.precision(36, 4) == pytest.approx(0.9)
    assert standard.recall(36, 4) == pytest.approx(0.9)
    assert standard.f1_score(36, 4, 4) == pytest.approx(0.9)


def test_precision_recall_handle_zero_denominator():
    assert standard.precision(0, 0) is None
    assert standard.recall(0, 0) is None
    assert standard.f1_score(0, 0, 0) is None


def test_f1_asymmetric_precision_recall():
    # precision=1.0 (TP=10,FP=0), recall=10/60=0.1667 -> f1 should be closer to
    # the smaller value than a plain arithmetic mean would be
    p = standard.precision(10, 0)
    r = standard.recall(10, 50)
    f1 = standard.f1_score(10, 0, 50)
    arithmetic_mean = (p + r) / 2
    assert f1 < arithmetic_mean
