# Generate Scoping File 11: Security & RBAC

Generate the Security & RBAC file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 11
```

## What This Generates

**File 11: security_rbac.md**

Complete security blueprint

**NOTE: Can run parallel with File 6**

## Report

Return:
- Confirmation that file 11_security_rbac.md was generated
- Path to the generated file
