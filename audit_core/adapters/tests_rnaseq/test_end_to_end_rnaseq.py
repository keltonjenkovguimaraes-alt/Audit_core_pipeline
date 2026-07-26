"""
End-to-end regression test against the real RNA-seq data fixture.
Locks in that the genuine drift/missing-CI findings keep firing.
"""

import json
import os

from audit_core.adapters import rnaseq_methods
from audit_core.runner import run_audit

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "examples", "rnaseq_real_data.json"
)


def _report():
    with open(FIXTURE_PATH) as f:
        raw = json.load(f)
    return run_audit(rnaseq_methods.adapt(raw))


def _find(report, check_name, status=None):
    return [r for r in report["results"]
            if r["check"] == check_name and (status is None or r["status"] == status)]


def test_all_discovery_counts_flagged_missing_ci():
    report = _report()
    hits = _find(report, "statistics.missing_ci", "FLAG")
    # 9 main methods + 7 rerun entries = 16
    assert len(hits) == 16


def test_deseq2_rerun_drift_caught():
    report = _report()
    hits = _find(report, "consistency.cross_location_drift", "FLAG")
    deseq2_hit = [h for h in hits if "deseq2" in h["issue"].lower()]
    assert len(deseq2_hit) == 1
    assert "2 different values" in deseq2_hit[0]["issue"]


def test_bayseq_rerun_drift_caught_with_three_values():
    report = _report()
    hits = _find(report, "consistency.cross_location_drift", "FLAG")
    bayseq_hit = [h for h in hits if "bayseq" in h["issue"].lower()]
    assert len(bayseq_hit) == 1
    assert "3 different values" in bayseq_hit[0]["issue"]


def test_samseq_rerun_drift_caught_with_five_values():
    report = _report()
    hits = _find(report, "consistency.cross_location_drift", "FLAG")
    samseq_hit = [h for h in hits if "samseq" in h["issue"].lower()]
    assert len(samseq_hit) == 1
    assert "5 different values" in samseq_hit[0]["issue"]


def test_no_fails_or_passes_given_data_scope():
    """
    Documents the honest scope of this adapter: since we only populate
    Proportion and standalone MetricValue (no groups, no validation sets,
    no definitions, no formulas), arithmetic/independence/definitions/
    formulas_check should all produce nothing -- not because they're
    broken, but because that data was never provided.
    """
    report = _report()
    assert report["summary"]["PASS"] == 0
    assert report["summary"]["FAIL"] == 0
    assert report["summary"]["FLAG"] == 19
