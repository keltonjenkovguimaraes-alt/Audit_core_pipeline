import pytest
from audit_core.ingest.schema import AuditInput, FormulaApplication
from audit_core.formulas import custom_specs
from audit_core.checks import formulas_check


@pytest.fixture(autouse=True)
def clean_spec_registry():
    """Custom specs are stored in a module-level dict; isolate tests from each other."""
    original = dict(custom_specs._SPECS)
    yield
    custom_specs._SPECS.clear()
    custom_specs._SPECS.update(original)


def test_saturated_formula_flagged_as_fail():
    custom_specs.register_spec(custom_specs.FormulaSpec(
        name="layer4_score", description="test", expected_range=(0.0, 1.0),
        expects_variance=True, min_std=0.05,
    ))
    ai = AuditInput()
    ai.formula_applications = [
        FormulaApplication(name="layer4_score",
                           outputs=[0.98, 0.99, 0.98, 1.0, 0.99],
                           location="Layer 4 module"),
    ]
    results = formulas_check.check_saturation(ai)
    saturation_results = [r for r in results if r["check"] == "formulas.saturation"]
    assert len(saturation_results) == 1
    assert saturation_results[0]["status"] == "FAIL"


def test_varying_formula_passes():
    custom_specs.register_spec(custom_specs.FormulaSpec(
        name="layer4_score", description="test", expected_range=(0.0, 1.0),
        expects_variance=True, min_std=0.05,
    ))
    ai = AuditInput()
    ai.formula_applications = [
        FormulaApplication(name="layer4_score",
                           outputs=[0.1, 0.4, 0.9, 0.3, 0.7, 0.55],
                           location="Layer 4 module"),
    ]
    results = formulas_check.check_saturation(ai)
    saturation_results = [r for r in results if r["check"] == "formulas.saturation"]
    assert len(saturation_results) == 1
    assert saturation_results[0]["status"] == "PASS"


def test_missing_spec_flagged():
    ai = AuditInput()
    ai.formula_applications = [
        FormulaApplication(name="unregistered_formula", outputs=[0.1, 0.2, 0.3],
                           location="somewhere"),
    ]
    results = formulas_check.check_saturation(ai)
    assert len(results) == 1
    assert results[0]["check"] == "formulas.no_spec"


def test_out_of_range_outputs_flagged():
    custom_specs.register_spec(custom_specs.FormulaSpec(
        name="bounded_score", description="test", expected_range=(0.0, 1.0),
        expects_variance=True, min_std=0.01,
    ))
    ai = AuditInput()
    ai.formula_applications = [
        FormulaApplication(name="bounded_score",
                           outputs=[0.1, 0.5, 1.4, 0.3, -0.2],
                           location="somewhere"),
    ]
    results = formulas_check.check_saturation(ai)
    range_results = [r for r in results if r["check"] == "formulas.out_of_range"]
    assert len(range_results) == 1
    assert range_results[0]["evidence"]["out_of_range_sample"] == [1.4, -0.2]


def test_single_output_skipped():
    custom_specs.register_spec(custom_specs.FormulaSpec(
        name="single_score", description="test", expected_range=(0.0, 1.0),
    ))
    ai = AuditInput()
    ai.formula_applications = [
        FormulaApplication(name="single_score", outputs=[0.5], location="somewhere"),
    ]
    results = formulas_check.check_saturation(ai)
    assert results == []
