"""
Statistical validity checks. Flag-only: never substitutes a corrected CI
into the source data, only computes what the reference formula WOULD say
and reports it alongside the original as a suggestion.
"""

from audit_core.formulas import standard

SMALL_N_THRESHOLD = 30


def _is_degenerate(numerator, denominator):
    return numerator == 0 or numerator == denominator


def check_missing_ci(audit_input):
    results = []
    for p in audit_input.proportions:
        if p.reported_ci is None:
            results.append({
                "status": "FLAG",
                "check": "statistics.missing_ci",
                "location": p.location,
                "issue": f"'{p.label}' ({p.numerator}/{p.denominator}) is reported as a "
                         f"bare proportion with no confidence interval",
                "evidence": {"numerator": p.numerator, "denominator": p.denominator},
                "suggested_direction": "Consider reporting a Wilson score or "
                                       "Clopper-Pearson interval alongside the point estimate.",
            })
    return results


def check_degenerate_ci(audit_input):
    """
    Flags proportions where the sample is degenerate (all-success or
    all-failure) — a case where naive methods (e.g. percentile bootstrap)
    silently produce a collapsed/meaningless interval like [1.0, 1.0].
    """
    results = []
    for p in audit_input.proportions:
        if not _is_degenerate(p.numerator, p.denominator):
            continue
        wilson = standard.wilson_score_interval(p.numerator, p.denominator)
        cp = standard.clopper_pearson_interval(p.numerator, p.denominator)
        flag = {
            "status": "FLAG",
            "check": "statistics.degenerate_ci",
            "location": p.location,
            "issue": f"'{p.label}' is a degenerate sample ({p.numerator}/{p.denominator}) — "
                     f"any naive CI method (e.g. percentile bootstrap) will collapse to a "
                     f"single point and understate uncertainty",
            "evidence": {
                "numerator": p.numerator,
                "denominator": p.denominator,
                "reported_ci": p.reported_ci,
                "reference_wilson_ci": tuple(round(x, 4) for x in wilson),
                "reference_clopper_pearson_ci": tuple(round(x, 4) for x in cp),
            },
            "suggested_direction": "Report Wilson score or Clopper-Pearson interval instead "
                                   "of a naive method for this degenerate case (values shown "
                                   "for comparison only — verify independently before use).",
        }
        if p.numerator == 0:
            if standard.is_rule_of_three_valid_n(p.denominator):
                bound = standard.rule_of_three_bound(p.denominator)
                flag["evidence"]["reference_rule_of_three_upper_bound"] = round(bound, 4)
            else:
                flag["evidence"]["note"] = (
                    f"n={p.denominator} < 30 — rule-of-three approximation not considered "
                    f"valid here; exact Clopper-Pearson bound shown instead"
                )
        results.append(flag)
    return results


def check_small_n_point_estimate(audit_input):
    """Flags proportions at small n reported with neither a CI nor any caveat."""
    results = []
    for p in audit_input.proportions:
        if p.denominator < SMALL_N_THRESHOLD and p.reported_ci is None:
            results.append({
                "status": "FLAG",
                "check": "statistics.small_n",
                "location": p.location,
                "issue": f"'{p.label}' is based on n={p.denominator} (< {SMALL_N_THRESHOLD}) "
                         f"and reported as a bare point estimate",
                "evidence": {"numerator": p.numerator, "denominator": p.denominator},
                "suggested_direction": "At this sample size the point estimate alone is "
                                       "likely to overstate precision; consider an exact "
                                       "interval and/or explicitly caveating n.",
            })
    return results


def run(audit_input, registry):
    return (
        check_missing_ci(audit_input)
        + check_degenerate_ci(audit_input)
        + check_small_n_point_estimate(audit_input)
    )
