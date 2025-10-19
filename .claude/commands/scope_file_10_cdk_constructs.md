# Generate Scoping File 10: CDK Constructs

Generate the CDK Constructs file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 10
```

## What This Generates

**File 10: cdk_constructs.md**

CDK construct library recommendations

**NOTE: Can run parallel with Files 12,13,14**

## Report

Return:
- Confirmation that file 10_cdk_constructs.md was generated
- Path to the generated file
