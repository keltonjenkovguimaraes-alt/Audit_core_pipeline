"""
Independence / overlap checks: given validation sets claimed to be
independent of each other, verify there's no ID/coordinate overlap.
"""


def check_overlap(audit_input):
    results = []
    sets_by_name = {vs.name: vs for vs in audit_input.validation_sets}

    for vs in audit_input.validation_sets:
        claims = vs.claimed_independent_from or []
        for other_name in claims:
            other = sets_by_name.get(other_name)
            if other is None:
                results.append({
                    "status": "FLAG",
                    "check": "independence.unknown_reference",
                    "location": vs.location,
                    "issue": f"'{vs.name}' claims independence from '{other_name}', but "
                             f"'{other_name}' was not found among registered validation sets",
                    "evidence": {"claimed_independent_from": other_name},
                    "suggested_direction": "Confirm the referenced set was actually "
                                           "provided to the audit input.",
                })
                continue
            overlap = vs.ids & other.ids
            if overlap:
                results.append({
                    "status": "FAIL",
                    "check": "independence.overlap",
                    "location": f"{vs.location} / {other.location}",
                    "issue": f"'{vs.name}' and '{other_name}' are claimed independent but "
                             f"share {len(overlap)} of {len(vs.ids)}/{len(other.ids)} IDs",
                    "evidence": {
                        "overlap_count": len(overlap),
                        "overlap_sample": list(overlap)[:10],
                        "set_a_size": len(vs.ids),
                        "set_b_size": len(other.ids),
                    },
                    "suggested_direction": "Re-derive the sets to be disjoint, or drop the "
                                           "independence claim and report the overlap.",
                })
            else:
                results.append({
                    "status": "PASS",
                    "check": "independence.overlap",
                    "location": vs.location,
                    "issue": f"'{vs.name}' and '{other_name}' confirmed disjoint",
                    "evidence": {"set_a_size": len(vs.ids), "set_b_size": len(other.ids)},
                    "suggested_direction": None,
                })
    return results


def run(audit_input, registry):
    return check_overlap(audit_input)
