"""
Top-level entry point: run every check module against an AuditInput and
return the aggregated, flag-only results. Never modifies audit_input.
"""

from audit_core.registry import MetricRegistry
from audit_core.checks import arithmetic, statistics, consistency, independence, definitions, formulas_check

CHECK_MODULES = [arithmetic, statistics, consistency, independence, definitions, formulas_check]


def run_audit(audit_input):
    registry = MetricRegistry(audit_input)
    all_results = []
    for module in CHECK_MODULES:
        all_results.extend(module.run(audit_input, registry))

    summary = {
        "PASS": sum(1 for r in all_results if r["status"] == "PASS"),
        "FLAG": sum(1 for r in all_results if r["status"] == "FLAG"),
        "FAIL": sum(1 for r in all_results if r["status"] == "FAIL"),
    }
    return {
        "document_title": audit_input.document_title,
        "results": all_results,
        "summary": summary,
    }
