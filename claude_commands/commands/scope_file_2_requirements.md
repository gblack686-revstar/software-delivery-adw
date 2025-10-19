# Generate Scoping File 2: Requirements Analysis

Generate the requirements analysis file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 2
```

## What This Generates

**File 2: requirements_analysis.md**

Extracts and analyzes technical requirements from the discovery brief:
- Business requirements and KPIs
- Functional and non-functional requirements
- Performance, scalability, security requirements
- Constraints and assumptions
- Risk assessment

## Dependencies

- File 1 (discovery_brief.md) must exist

## Report

Return:
- Confirmation that file 2_requirements_analysis.md was generated
- Path to the generated file
- Summary of key requirements identified
