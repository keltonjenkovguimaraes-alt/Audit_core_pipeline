"""
Definition-drift checks: a named classification rule (e.g. "CONFIRMED")
should have exactly one canonical definition. Flags any location whose
rule_desc differs from the first-registered ("canonical") one.
"""

from difflib import SequenceMatcher

SIMILARITY_THRESHOLD = 0.92  # below this, treat as a differing definition


def _similarity(a, b):
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def check_definition_drift(audit_input):
    results = []
    canonical = {}
    for d in audit_input.definitions:
        key = d.name.strip().lower()
        if key not in canonical:
            canonical[key] = d
            continue
        ref = canonical[key]
        sim = _similarity(ref.rule_desc, d.rule_desc)
        if sim < SIMILARITY_THRESHOLD:
            results.append({
                "status": "FLAG",
                "check": "definitions.drift",
                "location": d.location,
                "issue": f"Definition of '{d.name}' at {d.location} differs from the "
                         f"canonical definition first seen at {ref.location}",
                "evidence": {
                    "canonical_definition": ref.rule_desc,
                    "canonical_location": ref.location,
                    "this_definition": d.rule_desc,
                    "similarity": round(sim, 3),
                },
                "suggested_direction": "Register a single canonical definition for "
                                       f"'{d.name}' and confirm every usage matches it.",
            })
    return results


def run(audit_input, registry):
    return check_definition_drift(audit_input)
