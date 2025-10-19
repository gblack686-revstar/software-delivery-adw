# Generate Scoping File 4: Data Models

Generate the Data Models file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 4
```

## What This Generates

**File 4: data_models.yaml**

Designs data entities, relationships, and schemas



## Report

Return:
- Confirmation that file 4_data_models.yaml was generated
- Path to the generated file
