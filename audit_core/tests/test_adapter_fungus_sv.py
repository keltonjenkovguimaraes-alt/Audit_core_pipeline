"""
Tests for adapters/fungus_sv.py.

NOTE: field names in these fixtures follow the placeholder schema
documented in fungus_sv.py's docstring (sv_type, layer4_score, contig_id,
etc.) since real FUNGUS-SV JSON/log samples haven't been wired in yet.
Once real samples are available, these fixtures should be updated to
match the actual field names, and this file doubles as a regression
test that the adapter still produces correct canonical objects.
"""

from audit_core.adapters import fungus_sv
from audit_core.ingest.schema import AuditInput


def test_adapt_returns_audit_input():
    raw = {"title": "Test FUNGUS-SV run"}
    result = fungus_sv.adapt(raw)
    assert isinstance(result, AuditInput)
    assert result.document_title == "Test FUNGUS-SV run"


def test_adapt_uses_default_title_when_missing():
    result = fungus_sv.adapt({})
    assert result.document_title == "FUNGUS-SV audit"


def test_adapt_sv_counts_maps_to_metric_values():
    raw = {
        "sv_counts": {"DEL": 40, "DUP": 25, "INV": 10, "Total": 75}
    }
    result = fungus_sv.adapt(raw)
    assert len(result.metrics) == 4
    by_label = {m.label: m for m in result.metrics}
    assert by_label["DEL"].value == 40
    assert by_label["DEL"].role == "component"
    assert by_label["Total"].value == 75
    assert by_label["Total"].role == "total"
    # all should share the same group so arithmetic.check_subtotals can reconcile them
    assert len({m.group for m in result.metrics}) == 1


def test_adapt_sv_counts_total_key_matching_is_case_insensitive():
    raw = {"sv_counts": {"DEL": 10, "total": 10}}
    result = fungus_sv.adapt(raw)
    by_label = {m.label: m for m in result.metrics}
    assert by_label["total"].role == "total"
    assert by_label["DEL"].role == "component"


def test_adapt_no_total_key_all_components():
    raw = {"sv_counts": {"DEL": 10, "DUP": 5}}
    result = fungus_sv.adapt(raw)
    assert all(m.role == "component" for m in result.metrics)


def test_adapt_confirmation_rates_maps_to_proportions():
    raw = {
        "confirmation_rates": [
            {"sv_type": "INV", "confirmed": 9, "total": 12,
             "reported_pct": 90.0, "location": "Table 3"},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert len(result.proportions) == 1
    p = result.proportions[0]
    assert p.numerator == 9
    assert p.denominator == 12
    assert p.label == "INV_confirmation_rate"
    assert p.reported_pct == 90.0
    assert p.reported_ci is None


def test_adapt_confirmation_rates_with_ci():
    raw = {
        "confirmation_rates": [
            {"sv_type": "DEL", "confirmed": 36, "total": 40,
             "reported_ci": [0.85, 0.97]},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert result.proportions[0].reported_ci == (0.85, 0.97)


def test_adapt_definitions():
    raw = {
        "definitions": [
            {"name": "CONFIRMED", "rule": "strict rule", "location": "Methods 2.3"},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert len(result.definitions) == 1
    assert result.definitions[0].name == "CONFIRMED"
    assert result.definitions[0].rule_desc == "strict rule"


def test_adapt_validation_sets():
    raw = {
        "validation_sets": [
            {"name": "calibration_set", "ids": ["a", "b", "c"], "location": "M2.1",
             "independent_from": ["truth_set"]},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert len(result.validation_sets) == 1
    vs = result.validation_sets[0]
    assert vs.ids == {"a", "b", "c"}
    assert vs.claimed_independent_from == ["truth_set"]


def test_adapt_layer_scores():
    raw = {
        "layer_scores": [
            {"name": "layer4_junction_score", "outputs": [0.1, 0.5, 0.9],
             "location": "Layer 4 module"},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert len(result.formula_applications) == 1
    assert result.formula_applications[0].outputs == [0.1, 0.5, 0.9]


def test_adapt_generic_metrics():
    raw = {
        "metrics": [
            {"label": "total_strains", "value": 12, "location": "Abstract"},
            {"label": "total_strains", "value": 15, "location": "Methods"},
        ]
    }
    result = fungus_sv.adapt(raw)
    assert len(result.metrics) == 2
    assert all(m.role == "standalone" for m in result.metrics)


def test_adapt_handles_completely_empty_input():
    result = fungus_sv.adapt({})
    assert result.metrics == []
    assert result.proportions == []
    assert result.definitions == []
    assert result.validation_sets == []
    assert result.formula_applications == []


def test_adapt_missing_location_defaults_to_unspecified():
    raw = {"definitions": [{"name": "X", "rule": "some rule"}]}
    result = fungus_sv.adapt(raw)
    assert result.definitions[0].location == "unspecified"
