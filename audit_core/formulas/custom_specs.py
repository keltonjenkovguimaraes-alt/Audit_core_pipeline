"""
Registration point for project-specific formulas that aren't textbook
standard (e.g. a custom breakpoint-junction weighted score).

A "spec" declares what the formula is SUPPOSED to do — expected output
range, and whether it's expected to vary meaningfully across the input
distribution — WITHOUT reimplementing or fixing the formula itself.
checks/formulas_check.py compares actual FormulaApplication outputs
against the spec and flags mismatches (e.g. near-zero variance when
variance was expected).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FormulaSpec:
    name: str
    description: str
    expected_range: tuple            # (min, max) plausible output
    expects_variance: bool = True    # should output vary across dataset?
    min_std: Optional[float] = None  # if set, flag if std falls below this


_SPECS = {}


def register_spec(spec: FormulaSpec):
    _SPECS[spec.name] = spec


def get_spec(name: str):
    return _SPECS.get(name)


def all_specs():
    return dict(_SPECS)
