import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from audit_core.adapters import rnaseq_methods
from audit_core.runner import run_audit

with open(os.path.join(os.path.dirname(__file__), "rnaseq_real_data.json")) as f:
    raw = json.load(f)

audit_input = rnaseq_methods.adapt(raw)
report = run_audit(audit_input)

print(f"=== {report['document_title']} ===")
print(f"Summary: {report['summary']}\n")
for r in report["results"]:
    if r["status"] == "PASS":
        continue
    print(f"[{r['status']}] {r['check']}")
    print(f"  Location: {r['location']}")
    print(f"  Issue: {r['issue']}")
    print()
