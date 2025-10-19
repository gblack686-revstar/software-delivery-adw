# Generate Scoping File 9: Architecture Diagram

Generate the Architecture Diagram file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 9
```

## What This Generates

**File 9: architecture.mmd**

Comprehensive Mermaid architecture diagram

**NOTE: Can run parallel with File 11**

## Report

Return:
- Confirmation that file 9_architecture.mmd was generated
- Path to the generated file
