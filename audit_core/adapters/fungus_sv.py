"""
FUNGUS-SV adapter: translates FUNGUS-SV's project-specific JSON/log
schema into the canonical audit_core.ingest.schema types.

This is the ONLY file in the whole pipeline that should know about
FUNGUS-SV concepts (SV types, backtrack scripts, Layer 4 scoring, etc).
Every check module operates purely on the canonical types this produces.

NOTE: field names below (sv_type, layer4_score, contig_id, etc.) are
illustrative placeholders based on what's been discussed. Once real
FUNGUS-SV JSON/log samples are provided, this parser should be adjusted
to match the actual field names/structure.
"""

from audit_core.ingest.schema import (
    AuditInput, MetricValue, Proportion, NamedDefinition,
    ValidationSet, FormulaApplication,
)


def adapt(raw: dict) -> AuditInput:
    """
    raw: parsed JSON expected to loosely resemble:
      {
        "sv_counts": {"DEL": 40, "DUP": 25, "INV": 10, "Total": 80},
        "confirmation_rates": [
            {"sv_type": "INV", "confirmed": 9, "total": 12, "location": "Table 3"}
        ],
        "definitions": [
            {"name": "CONFIRMED", "rule": "...", "location": "Methods 2.3"}
        ],
        "validation_sets": [
            {"name": "calibration_set", "ids": [...], "location": "...",
             "independent_from": ["truth_set"]}
        ],
        "layer_scores": [
            {"name": "layer4_junction_score", "outputs": [...], "location": "..."}
        ]
      }
    """
    audit_input = AuditInput(document_title=raw.get("title", "FUNGUS-SV audit"))

    sv_counts = raw.get("sv_counts", {})
    if sv_counts:
        total_key = next((k for k in sv_counts if k.lower() == "total"), None)
        for label, value in sv_counts.items():
            role = "total" if label == total_key else "component"
            audit_input.metrics.append(MetricValue(
                label=label, value=value, location="sv_counts table",
                group="sv_type_counts", role=role,
            ))

    for row in raw.get("confirmation_rates", []):
        audit_input.proportions.append(Proportion(
            numerator=row["confirmed"],
            denominator=row["total"],
            label=f"{row['sv_type']}_confirmation_rate",
            location=row.get("location", "confirmation_rates table"),
            reported_pct=row.get("reported_pct"),
            reported_ci=tuple(row["reported_ci"]) if row.get("reported_ci") else None,
        ))

    for d in raw.get("definitions", []):
        audit_input.definitions.append(NamedDefinition(
            name=d["name"], location=d.get("location", "unspecified"),
            rule_desc=d["rule"],
        ))

    for vs in raw.get("validation_sets", []):
        audit_input.validation_sets.append(ValidationSet(
            name=vs["name"], ids=set(vs["ids"]), location=vs.get("location", "unspecified"),
            claimed_independent_from=vs.get("independent_from"),
        ))

    for fs in raw.get("layer_scores", []):
        audit_input.formula_applications.append(FormulaApplication(
            name=fs["name"], outputs=fs["outputs"], location=fs.get("location", "unspecified"),
        ))

    # generic standalone metrics (e.g. same-named quantity restated elsewhere
    # in the manuscript, for cross-location drift checking)
    for m in raw.get("metrics", []):
        audit_input.metrics.append(MetricValue(
            label=m["label"], value=m["value"], location=m.get("location", "unspecified"),
            role=m.get("role", "standalone"),
        ))

    return audit_input

