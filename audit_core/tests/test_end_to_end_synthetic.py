"""
End-to-end regression test: the synthetic_manuscript.json fixture has
exactly one planted error per check category. This test locks in that
every category still fires as expected, so a future refactor can't
silently break a check without a test failing.
"""

import json
import os
import pytest

from audit_core.adapters import fungus_sv
from audit_core.formulas import custom_specs
from audit_core.runner import run_audit

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "examples", "synthetic_manuscript.json"
)


@pytest.fixture(autouse=True)
def clean_spec_registry():
    original = dict(custom_specs._SPECS)
    yield
    custom_specs._SPECS.clear()
    custom_specs._SPECS.update(original)


@pytest.fixture
def synthetic_report():
    custom_specs.register_spec(custom_specs.FormulaSpec(
        name="layer4_junction_score",
        description="Breakpoint junction confidence score.",
        expected_range=(0.0, 1.0),
        expects_variance=True,
        min_std=0.05,
    ))
    with open(FIXTURE_PATH) as f:
        raw = json.load(f)
    audit_input = fungus_sv.adapt(raw)
    return run_audit(audit_input)


def _find(report, check_name, status=None):
    return [r for r in report["results"]
            if r["check"] == check_name and (status is None or r["status"] == status)]


def test_bad_subtotal_caught(synthetic_report):
    hits = _find(synthetic_report, "arithmetic.subtotals", "FAIL")
    assert len(hits) == 1
    assert hits[0]["evidence"]["difference"] == -5


def test_wrong_percentages_caught(synthetic_report):
    hits = _find(synthetic_report, "arithmetic.percentages", "FAIL")
    # two planted percentage mismatches (INV and DEL rows)
    assert len(hits) == 2


def test_degenerate_ci_caught(synthetic_report):
    hits = _find(synthetic_report, "statistics.degenerate_ci", "FLAG")
    assert len(hits) == 1
    assert hits[0]["evidence"]["numerator"] == 0


def test_missing_ci_caught(synthetic_report):
    hits = _find(synthetic_report, "statistics.missing_ci", "FLAG")
    # INV row and DUP_falsepos row both lack a CI
    assert len(hits) == 2


def test_small_n_caught(synthetic_report):
    hits = _find(synthetic_report, "statistics.small_n", "FLAG")
    assert len(hits) == 1
    assert hits[0]["evidence"]["denominator"] == 12


def test_cross_location_drift_caught(synthetic_report):
    hits = _find(synthetic_report, "consistency.cross_location_drift", "FLAG")
    assert len(hits) == 1
    assert "total_strains" in hits[0]["issue"]


def test_overlap_caught(synthetic_report):
    hits = _find(synthetic_report, "independence.overlap", "FAIL")
    assert len(hits) == 1
    assert hits[0]["evidence"]["overlap_count"] == 2


def test_definition_drift_caught(synthetic_report):
    hits = _find(synthetic_report, "definitions.drift", "FLAG")
    assert len(hits) == 1


def test_saturation_caught(synthetic_report):
    hits = _find(synthetic_report, "formulas.saturation", "FAIL")
    assert len(hits) == 1


def test_summary_counts_are_internally_consistent(synthetic_report):
    summary = synthetic_report["summary"]
    total_results = len(synthetic_report["results"])
    assert summary["PASS"] + summary["FLAG"] + summary["FAIL"] == total_results
