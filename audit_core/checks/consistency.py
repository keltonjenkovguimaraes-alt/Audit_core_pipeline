"""
Provenance & consistency checks: same conceptual metric (matched by
normalized label) reported with different values across locations, or
denominator (n) changing between mentions without it being flagged
elsewhere as an explicit expansion.
"""

TOLERANCE = 1e-6


def check_cross_location_drift(registry):
    results = []
    for label in registry.all_labels():
        occs = registry.occurrences(label)
        if len(occs) < 2:
            continue
        values = []
        for o in occs:
            if hasattr(o, "value"):
                values.append((o.value, o.location, o.source))
            elif hasattr(o, "numerator"):
                values.append((f"{o.numerator}/{o.denominator}", o.location, o.source))
        distinct = set(v[0] for v in values)
        if len(distinct) > 1:
            results.append({
                "status": "FLAG",
                "check": "consistency.cross_location_drift",
                "location": "; ".join(v[1] for v in values),
                "issue": f"Metric '{label}' reported with {len(distinct)} different values "
                         f"across {len(values)} locations",
                "evidence": {"occurrences": [
                    {"value": v[0], "location": v[1], "source": v[2]} for v in values
                ]},
                "suggested_direction": "Confirm which value is current; if an update is "
                                       "intentional (e.g. dataset expanded), add an explicit "
                                       "note rather than leaving both values unreconciled.",
            })
    return results


def run(audit_input, registry):
    return check_cross_location_drift(registry)
