# Generate Scoping File 7: AWS Native Analysis

Generate the AWS Native Analysis file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 7
```

## What This Generates

**File 7: aws_native_analysis.md**

Evaluates AWS-native vs non-native service options

**NOTE: Can run parallel with File 11**

## Report

Return:
- Confirmation that file 7_aws_native_analysis.md was generated
- Path to the generated file
