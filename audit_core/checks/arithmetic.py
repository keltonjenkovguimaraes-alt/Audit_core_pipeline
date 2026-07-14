"""
Arithmetic reconciliation checks.

These never fix anything — they recompute a relationship independently
and flag a mismatch. Domain-agnostic: operates purely on MetricValue.group
/ .role and Proportion numerator/denominator/reported_pct.
"""

TOLERANCE = 1e-6


def check_subtotals(registry):
    """
    For every group of MetricValues, if there's a value with role=="total"
    and one or more with role in ("component","subtotal"), verify the
    components sum to the total.
    """
    results = []
    for group_name, values in registry.groups().items():
        total_entries = [v for v in values if v.role == "total"]
        component_entries = [v for v in values if v.role in ("component", "subtotal")]
        if not total_entries or not component_entries:
            continue
        computed = sum(v.value for v in component_entries)
        for total in total_entries:
            diff = computed - total.value
            if abs(diff) > TOLERANCE:
                results.append({
                    "status": "FAIL",
                    "check": "arithmetic.subtotals",
                    "location": total.location,
                    "issue": f"Components in group '{group_name}' sum to {computed}, "
                             f"but stated total is {total.value}",
                    "evidence": {
                        "components": [(v.label, v.value) for v in component_entries],
                        "stated_total": total.value,
                        "computed_total": computed,
                        "difference": diff,
                    },
                    "suggested_direction": "Re-check whether all components are included, "
                                            "or whether the total was updated independently.",
                })
            else:
                results.append({
                    "status": "PASS",
                    "check": "arithmetic.subtotals",
                    "location": total.location,
                    "issue": f"Group '{group_name}' reconciles correctly",
                    "evidence": {"computed_total": computed, "stated_total": total.value},
                    "suggested_direction": None,
                })
    return results


def check_percentages(audit_input):
    """
    For every Proportion with a reported_pct, verify it matches
    numerator/denominator within rounding tolerance (0.06 percentage
    points, i.e. allows for standard rounding to 1 decimal place).
    """
    results = []
    ROUND_TOLERANCE = 0.06
    for p in audit_input.proportions:
        if p.reported_pct is None:
            continue
        if p.denominator == 0:
            results.append({
                "status": "FAIL",
                "check": "arithmetic.percentages",
                "location": p.location,
                "issue": f"'{p.label}' has denominator 0 but a percentage is reported "
                         f"({p.reported_pct})",
                "evidence": {"numerator": p.numerator, "denominator": p.denominator,
                             "reported_pct": p.reported_pct},
                "suggested_direction": "Undefined ratio — verify what this percentage "
                                       "was actually computed from.",
            })
            continue
        computed_pct = 100.0 * p.numerator / p.denominator
        diff = computed_pct - p.reported_pct
        if abs(diff) > ROUND_TOLERANCE:
            results.append({
                "status": "FAIL",
                "check": "arithmetic.percentages",
                "location": p.location,
                "issue": f"'{p.label}' reported as {p.reported_pct}%, but "
                         f"{p.numerator}/{p.denominator} = {computed_pct:.2f}%",
                "evidence": {"numerator": p.numerator, "denominator": p.denominator,
                             "reported_pct": p.reported_pct, "computed_pct": computed_pct,
                             "difference_pp": diff},
                "suggested_direction": "Check whether numerator/denominator match what "
                                       "was actually used to compute the stated percentage.",
            })
        else:
            results.append({
                "status": "PASS",
                "check": "arithmetic.percentages",
                "location": p.location,
                "issue": f"'{p.label}' percentage reconciles correctly",
                "evidence": {"computed_pct": computed_pct, "reported_pct": p.reported_pct},
                "suggested_direction": None,
            })
    return results


def run(audit_input, registry):
    return check_subtotals(registry) + check_percentages(audit_input)
