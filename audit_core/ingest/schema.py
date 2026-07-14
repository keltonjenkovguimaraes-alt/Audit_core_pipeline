"""
Canonical internal schema for audit_core.

Every adapter (FUNGUS-SV, or any future domain) must translate its native
format into lists of these dataclasses. Every check in audit_core/checks/
operates ONLY on these types — never on domain-specific field names.

This is the contract that makes the pipeline domain-agnostic: write one
adapter per input format, and every check works unmodified.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class MetricValue:
    """
    A single reported number, tagged with enough context to check it.

    label:        what this number is called in the source ("DEL count", "recall")
    value:        the reported numeric value
    location:     where it appears ("Table 2, row 3", "manuscript section 4.1")
    source:       file/script/timestamp provenance, e.g. "backtrack_v3.py::2026-05-02"
    group:        an identifier linking related values, e.g. all rows of the same
                  table, so arithmetic checks know what should sum to what
    parent_of:    if this value is a claimed total/subtotal of other values in
                  the same group, list which labels it should equal the sum of
                  (optional — arithmetic.py can also infer this from group + role)
    role:         "component" | "subtotal" | "total" | "standalone"
    tags:         freeform metadata (e.g. {"metric_type": "count"})
    """
    label: str
    value: float
    location: str
    source: Optional[str] = None
    group: Optional[str] = None
    parent_of: Optional[list] = None
    role: str = "standalone"
    tags: dict = field(default_factory=dict)


@dataclass
class Proportion:
    """
    A binomial proportion — numerator/denominator pair, optionally with a
    reported confidence interval and/or a reported point-estimate percentage.

    numerator/denominator: the raw counts behind the proportion
    reported_pct:          the percentage as stated in the source (for
                            cross-checking against numerator/denominator)
    reported_ci:            (low, high) tuple if a CI was reported, else None
    ci_method:              name of CI method claimed, if stated (e.g. "bootstrap")
    label/location/source:  same meaning as MetricValue
    """
    numerator: int
    denominator: int
    label: str
    location: str
    source: Optional[str] = None
    reported_pct: Optional[float] = None
    reported_ci: Optional[tuple] = None
    ci_method: Optional[str] = None


@dataclass
class NamedDefinition:
    """
    A classification rule referenced by name (e.g. "CONFIRMED", "CONTRADICTS").

    name:        the label used in the text/tables
    location:    where this usage appears
    rule_desc:   how the rule is described/implemented at this location
                 (free text or a structured predicate — used for drift detection
                 by comparing rule_desc strings/hashes across locations)
    """
    name: str
    location: str
    rule_desc: str
    source: Optional[str] = None


@dataclass
class ValidationSet:
    """
    A named set of IDs/coordinates used for some validation purpose
    (e.g. "calibration_set", "truth_set"). Used by independence.py to
    check for unexpected overlap between sets claimed to be independent.
    """
    name: str
    ids: set
    location: str
    claimed_independent_from: Optional[list] = None


@dataclass
class FormulaApplication:
    """
    A record of a formula/score applied across many data points, for
    saturation checking.

    name:    formula name (e.g. "layer4_junction_score")
    outputs: list of numeric outputs across the dataset
    inputs:  optional list of corresponding input dicts, for diagnosis
    """
    name: str
    outputs: list
    location: str
    inputs: Optional[list] = None


@dataclass
class AuditInput:
    """Top-level container an adapter produces; passed into the check runner."""
    metrics: list = field(default_factory=list)          # list[MetricValue]
    proportions: list = field(default_factory=list)       # list[Proportion]
    definitions: list = field(default_factory=list)       # list[NamedDefinition]
    validation_sets: list = field(default_factory=list)    # list[ValidationSet]
    formula_applications: list = field(default_factory=list)  # list[FormulaApplication]
    document_title: str = "Untitled audit"
