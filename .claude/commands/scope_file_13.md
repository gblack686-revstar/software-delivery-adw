# Generate Scoping File 13: Validation Gates

Generate the Validation Gates file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 13
```

## What This Generates

**File 13: validation_gates.yaml**

Success criteria and quality gates

**NOTE: Can run parallel with Files 10,12,14**

## Report

Return:
- Confirmation that file 13_validation_gates.yaml was generated
- Path to the generated file
