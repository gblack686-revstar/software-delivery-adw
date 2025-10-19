# Generate Scoping File 6: ML Research

Generate the ML Research file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 6
```

## What This Generates

**File 6: ml_research.md**

State-of-the-art ML/AI model research using Exa

**NOTE: Can run parallel with File 11**

## Report

Return:
- Confirmation that file 6_ml_research.md was generated
- Path to the generated file
