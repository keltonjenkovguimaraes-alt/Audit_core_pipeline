"""
Tests for adapters/rnaseq_methods.py.

Values here are taken directly from the real fixture
(examples/rnaseq_real_data.json), which itself was built from the
PLOS ONE paper text and the authors' own GitHub script — not invented.
"""

from audit_core.adapters import rnaseq_methods
from audit_core.ingest.schema import AuditInput


def _minimal_raw():
    return {
        "title": "Test RNA-seq run",
        "gene_filtering": {
            "full_sample": {"total_genes": 36536, "filtered_genes": 11870, "location": "loc1"},
        },
        "denominator_full_sample": 11870,
        "discovery_counts_full_sample": [
            {"method": "DESeq2", "count": 1325, "location": "loc2"},
        ],
        "discovery_count_reruns": [
            {"method": "DESeq2", "count": 1314, "location": "loc3"},
        ],
    }


def test_adapt_returns_audit_input():
    result = rnaseq_methods.adapt(_minimal_raw())
    assert isinstance(result, AuditInput)
    assert result.document_title == "Test RNA-seq run"


def test_gene_filtering_maps_to_two_standalone_metrics():
    result = rnaseq_methods.adapt(_minimal_raw())
    labels = {m.label: m for m in result.metrics}
    assert labels["total_genes_full_sample"].value == 36536
    assert labels["filtered_genes_full_sample"].value == 11870
    assert labels["total_genes_full_sample"].role == "standalone"


def test_gene_filtering_does_not_use_shared_group():
    # deliberately not grouped, since it's not a sum relationship
    result = rnaseq_methods.adapt(_minimal_raw())
    assert all(m.group is None for m in result.metrics)


def test_discovery_count_maps_to_proportion_with_correct_denominator():
    result = rnaseq_methods.adapt(_minimal_raw())
    main = [p for p in result.proportions if p.location == "loc2"][0]
    assert main.numerator == 1325
    assert main.denominator == 11870
    assert main.label == "DESeq2_discovery_count"


def test_rerun_shares_label_with_main_entry_for_drift_detection():
    result = rnaseq_methods.adapt(_minimal_raw())
    labels = [p.label for p in result.proportions]
    assert labels.count("DESeq2_discovery_count") == 2


def test_no_ci_reported_anywhere():
    result = rnaseq_methods.adapt(_minimal_raw())
    assert all(p.reported_ci is None for p in result.proportions)


def test_adapter_does_not_populate_unsupported_types():
    """
    Deliberate: this adapter should never populate ValidationSet,
    NamedDefinition, or FormulaApplication, since the real source data
    doesn't support any of them. If a future edit adds fabricated data
    for these, this test should fail and prompt a check of provenance.
    """
    result = rnaseq_methods.adapt(_minimal_raw())
    assert result.validation_sets == []
    assert result.definitions == []
    assert result.formula_applications == []


def test_multiple_method_reruns_all_share_label_with_main():
    raw = _minimal_raw()
    raw["discovery_count_reruns"] = [
        {"method": "DESeq2", "count": 1314, "location": "a"},
        {"method": "DESeq2", "count": 1300, "location": "b"},
    ]
    result = rnaseq_methods.adapt(raw)
    matching = [p for p in result.proportions if p.label == "DESeq2_discovery_count"]
    assert len(matching) == 3  # main + 2 reruns


def test_empty_input_produces_empty_audit_input():
    result = rnaseq_methods.adapt({})
    assert result.metrics == []
    assert result.proportions == []
