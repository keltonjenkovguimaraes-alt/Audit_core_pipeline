"""
Formula/scoring sanity checks: for any formula applied across a dataset
and registered with a FormulaSpec, verify the actual outputs are
consistent with the spec (variance expected? within plausible range?).
This is what would have caught the Layer 4 saturation defect immediately.
"""

import statistics as pystats
from audit_core.formulas import custom_specs


def check_saturation(audit_input):
    results = []
    for fa in audit_input.formula_applications:
        spec = custom_specs.get_spec(fa.name)
        if spec is None:
            results.append({
                "status": "FLAG",
                "check": "formulas.no_spec",
                "location": fa.location,
                "issue": f"Formula '{fa.name}' has recorded outputs but no registered spec — "
                         f"cannot check for saturation or plausible range",
                "evidence": {"n_outputs": len(fa.outputs)},
                "suggested_direction": f"Register a FormulaSpec for '{fa.name}' describing "
                                       "expected output range and whether variance is expected.",
            })
            continue

        outputs = fa.outputs
        if len(outputs) < 2:
            continue
        std = pystats.pstdev(outputs)
        lo, hi = min(outputs), max(outputs)
        out_of_range = [v for v in outputs if v < spec.expected_range[0] or v > spec.expected_range[1]]

        if spec.expects_variance:
            threshold = spec.min_std if spec.min_std is not None else 1e-9
            if std <= threshold:
                results.append({
                    "status": "FAIL",
                    "check": "formulas.saturation",
                    "location": fa.location,
                    "issue": f"Formula '{fa.name}' is expected to vary across inputs but "
                             f"output std={std:.6f} across {len(outputs)} samples "
                             f"(range observed: {lo}-{hi})",
                    "evidence": {
                        "std": std, "min": lo, "max": hi, "n": len(outputs),
                        "spec_description": spec.description,
                    },
                    "suggested_direction": "Formula output is effectively constant — check "
                                           "for saturation (e.g. a component of the formula "
                                           "always evaluating to the same term).",
                })
            else:
                results.append({
                    "status": "PASS",
                    "check": "formulas.saturation",
                    "location": fa.location,
                    "issue": f"Formula '{fa.name}' shows expected variance (std={std:.4f})",
                    "evidence": {"std": std, "min": lo, "max": hi, "n": len(outputs)},
                    "suggested_direction": None,
                })

        if out_of_range:
            results.append({
                "status": "FLAG",
                "check": "formulas.out_of_range",
                "location": fa.location,
                "issue": f"{len(out_of_range)} of {len(outputs)} outputs from '{fa.name}' "
                         f"fall outside the expected range {spec.expected_range}",
                "evidence": {"out_of_range_sample": out_of_range[:10],
                             "expected_range": spec.expected_range},
                "suggested_direction": "Verify whether the expected range is still correct, "
                                       "or whether the formula/inputs have a defect.",
            })
    return results


def run(audit_input, registry):
    return check_saturation(audit_input)
