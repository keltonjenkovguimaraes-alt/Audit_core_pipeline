"""
Demo: run audit_core end-to-end against the synthetic manuscript,
which has deliberately planted errors covering every check category.
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from audit_core.adapters import fungus_sv
from audit_core.formulas.custom_specs import FormulaSpec, register_spec
from audit_core.runner import run_audit
from audit_core.report.pdf_report import generate_pdf

# Register the project-specific formula spec once. This does NOT fix the
# formula — it just declares what "correct behavior" should look like so
# the saturation check has something to compare against.
register_spec(FormulaSpec(
    name="layer4_junction_score",
    description="Breakpoint junction confidence score; should discriminate "
                 "between well- and poorly-supported junctions across the dataset.",
    expected_range=(0.0, 1.0),
    expects_variance=True,
    min_std=0.05,  # anything below this is suspiciously flat
))

with open(os.path.join(os.path.dirname(__file__), "synthetic_manuscript.json")) as f:
    raw = json.load(f)

audit_input = fungus_sv.adapt(raw)
report = run_audit(audit_input)

print(f"=== {report['document_title']} ===")
print(f"Summary: {report['summary']}\n")
for r in report["results"]:
    if r["status"] == "PASS":
        continue
    print(f"[{r['status']}] {r['check']}")
    print(f"  Location: {r['location']}")
    print(f"  Issue: {r['issue']}")
    if r["suggested_direction"]:
        print(f"  Suggested direction: {r['suggested_direction']}")
    print()

pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "synthetic_audit_report.pdf")
pdf_path = os.path.abspath(pdf_path)
generate_pdf(report, pdf_path)
print(f"PDF report written to: {pdf_path}")
