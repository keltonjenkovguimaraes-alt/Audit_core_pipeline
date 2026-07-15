from audit_core.ingest.schema import AuditInput, NamedDefinition
from audit_core.checks import definitions


def test_identical_definitions_not_flagged():
    ai = AuditInput()
    ai.definitions = [
        NamedDefinition(name="CONFIRMED", location="Methods 2.3",
                        rule_desc="Both breakpoint coordinates match ground truth within 50bp."),
        NamedDefinition(name="CONFIRMED", location="Supplementary Table 3",
                        rule_desc="Both breakpoint coordinates match ground truth within 50bp."),
    ]
    results = definitions.check_definition_drift(ai)
    assert results == []


def test_drifted_definition_flagged():
    ai = AuditInput()
    ai.definitions = [
        NamedDefinition(name="CONFIRMED", location="Methods 2.3",
                        rule_desc="Both breakpoint coordinates match ground truth within 50bp "
                                  "AND the SV type matches."),
        NamedDefinition(name="CONFIRMED", location="Supplementary Table 3",
                        rule_desc="SV type matches ground truth, including PARTIAL coordinate matches."),
    ]
    results = definitions.check_definition_drift(ai)
    assert len(results) == 1
    assert results[0]["status"] == "FLAG"
    assert results[0]["check"] == "definitions.drift"


def test_minor_wording_difference_not_flagged():
    ai = AuditInput()
    ai.definitions = [
        NamedDefinition(name="CONFIRMED", location="Methods 2.3",
                        rule_desc="Both breakpoint coordinates match ground truth within 50bp."),
        NamedDefinition(name="CONFIRMED", location="Discussion",
                        rule_desc="both breakpoint coordinates match ground truth within 50bp"),
    ]
    results = definitions.check_definition_drift(ai)
    assert results == []


def test_different_named_definitions_dont_interfere():
    ai = AuditInput()
    ai.definitions = [
        NamedDefinition(name="CONFIRMED", location="Methods 2.3", rule_desc="Strict rule A."),
        NamedDefinition(name="CONTRADICTS", location="Methods 2.4", rule_desc="Different rule B."),
    ]
    results = definitions.check_definition_drift(ai)
    assert results == []
