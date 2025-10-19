# Generate Scoping File 5: Data Schema ERD

Generate the Data Schema ERD file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 5
```

## What This Generates

**File 5: data_schema.mmd**

Visual entity relationship diagram in Mermaid format



## Report

Return:
- Confirmation that file 5_data_schema.mmd was generated
- Path to the generated file
