# Generate Scoping File 3: User Flows

Generate the User Flows file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 3
```

## What This Generates

**File 3: user_flows.yaml**

Designs user personas and their interaction workflows



## Report

Return:
- Confirmation that file 3_user_flows.yaml was generated
- Path to the generated file
