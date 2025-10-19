# Generate Scoping File 8: AWS Services

Generate the AWS Services file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 8
```

## What This Generates

**File 8: aws_services.yaml**

Detailed AWS service configurations

**NOTE: Can run parallel with File 11**

## Report

Return:
- Confirmation that file 8_aws_services.yaml was generated
- Path to the generated file
