"""
Adapter for the RNA-seq differential analysis methods comparison paper
(PLOS ONE, 2022, DOI: 10.1371/journal.pone.0264246).

Source data: real-data (non-simulated) discovery counts from the authors'
own analysis script (RNASeq_examples.R), applied to the Bottomly et al.
mouse strain RNA-seq dataset.

WHY THIS ADAPTER IS SMALLER THAN fungus_sv.py: the source material only
gives us aggregate counts, not gene-level ID lists or per-condition
FDR/power tables (those live in supplementary PDFs we couldn't access).
So this adapter deliberately does NOT populate ValidationSet,
NamedDefinition, or FormulaApplication — using those types here would
mean inventing data the source doesn't actually provide.
"""

from audit_core.ingest.schema import AuditInput, MetricValue, Proportion


def adapt(raw: dict) -> AuditInput:
    audit_input = AuditInput(document_title=raw.get("title", "RNA-seq methods comparison"))

    # --- Gene filtering: sequential before/after facts, not a sum ---
    # These get distinct labels per sample size on purpose: full_sample and
    # subsample_n3 are genuinely different denominators (different number of
    # mice used), not the same metric restated. Using the same label for
    # both would cause consistency.py to falsely flag this as drift.
    filtering = raw.get("gene_filtering", {})
    for sample_key, info in filtering.items():
        audit_input.metrics.append(MetricValue(
            label=f"total_genes_{sample_key}", value=info["total_genes"],
            location=info["location"], role="standalone",
        ))
        audit_input.metrics.append(MetricValue(
            label=f"filtered_genes_{sample_key}", value=info["filtered_genes"],
            location=info["location"], role="standalone",
        ))

    denom = raw.get("denominator_full_sample")

    # --- Per-method discovery counts: each is "N genes out of 11,870" ---
    # Modeled as Proportion (not MetricValue) specifically so
    # statistics.check_missing_ci fires — the paper reports these as bare
    # counts with no confidence interval anywhere, which is a genuine,
    # verifiable finding, not a false positive.
    for row in raw.get("discovery_counts_full_sample", []):
        audit_input.proportions.append(Proportion(
            numerator=row["count"], denominator=denom,
            label=f"{row['method']}_discovery_count",
            location=row["location"],
        ))

    # --- Re-run variants: same label as above, different location/value ---
    # This is what makes consistency.check_cross_location_drift fire for
    # DESeq2, baySeq, and SAMSeq — genuine drift found in the authors' own
    # script comments, not staged for this demo.
    for row in raw.get("discovery_count_reruns", []):
        audit_input.proportions.append(Proportion(
            numerator=row["count"], denominator=denom,
            label=f"{row['method']}_discovery_count",
            location=row["location"],
        ))

    return audit_input
