# audit_core
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21384059.svg)](https://doi.org/10.5281/zenodo.21384059)
A domain-agnostic numerical audit pipeline: flags inconsistencies in
numbers, statistics, and formulas across any results document. It never
corrects anything — every check produces evidence + a suggested
direction, for a human to decide on.

## Install

Locally (editable, for development):
```bash
git clone https://github.com/keltonjenkovguimaraes-alt/audit_core.git
cd audit_core
pip install -e .
```

Directly from GitHub, without cloning:
```bash
pip install git+https://github.com/keltonjenkovguimaraes-alt/audit_core.git
```

## Structure

- `ingest/schema.py` — canonical data types every check operates on
- `registry.py` — indexes metrics by label for cross-location checks
- `formulas/standard.py` — reference implementations (Wilson, Clopper-Pearson,
  rule-of-three, precision/recall/F1) used for comparison only
- `formulas/custom_specs.py` — register project-specific formula specs
  (expected range / expected variance) without touching the formula itself
- `checks/` — one module per check category:
  - `arithmetic.py` — subtotal/total and percentage reconciliation
  - `statistics.py` — missing/degenerate CIs, small-n bare point estimates
  - `consistency.py` — same metric, different value across locations
  - `independence.py` — overlap between validation sets claimed independent
  - `definitions.py` — drift in a named classification rule's definition
  - `formulas_check.py` — saturation / out-of-range detection for
    registered formula specs
- `runner.py` — runs all checks, returns aggregated flag-only results
- `report/pdf_report.py` — renders results into a structured PDF
- `adapters/fungus_sv.py` — the ONLY FUNGUS-SV-specific file; translates
  FUNGUS-SV's JSON schema into the canonical types above

## Usage

```python
from audit_core.adapters import fungus_sv
from audit_core.runner import run_audit
from audit_core.report.pdf_report import generate_pdf
from audit_core.formulas.custom_specs import FormulaSpec, register_spec

# 1. register any project-specific formula specs once
register_spec(FormulaSpec(
    name="layer4_junction_score",
    description="...",
    expected_range=(0.0, 1.0),
    expects_variance=True,
    min_std=0.05,
))

# 2. adapt your raw data into the canonical schema
audit_input = fungus_sv.adapt(raw_json_dict)

# 3. run all checks
report = run_audit(audit_input)

# 4. render to PDF
generate_pdf(report, "audit_report.pdf")
```

## Adding a new domain (non-FUNGUS-SV data)

Write a new file in `adapters/`, e.g. `adapters/clinical_trial.py`, that
maps your source format's fields into `MetricValue`, `Proportion`,
`NamedDefinition`, `ValidationSet`, and `FormulaApplication` objects from
`ingest/schema.py`. No changes needed anywhere else — every check module
already operates on those types.

## Demo

```bash
python3 examples/run_demo.py
```

Runs the pipeline against `examples/synthetic_manuscript.json`, a file
with deliberately planted errors covering every check category (bad
subtotal, wrong percentage, degenerate CI, cross-location value drift,
overlapping "independent" sets, definition drift, and a saturated
formula) — useful as a sanity check that the pipeline is working before
wiring in real FUNGUS-SV data.

## Publishing this to GitHub

1. Create an empty repo on GitHub (no README/license — you already have those here).
2. From this directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: audit_core pipeline"
   git branch -M main
   git remote add origin https://github.com/keltonjenkovguimaraes-alt/audit_core.git
   git push -u origin main
   ```
3. The included `.github/workflows/ci.yml` will automatically run the
   demo as a smoke test on every push/PR across Python 3.9-3.12 — no
   extra setup needed, GitHub Actions picks it up automatically.

## Contributing a new adapter

To audit a new kind of results (not FUNGUS-SV), add a file under
`audit_core/adapters/`, e.g. `adapters/my_domain.py`, that maps your
source format into the canonical types in `ingest/schema.py`. Open a PR
— no changes to `checks/` are needed for new domains.
