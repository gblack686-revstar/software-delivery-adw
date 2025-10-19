# Generate Scoping File 14: LLM Prompts

Generate the LLM Prompts file for the scoping phase.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase

## Run

```bash
uv run python adws/adw_scoping_modular.py --adw-id "$1" --file-num 14
```

## What This Generates

**File 14: llm_prompts.yaml**

AI agent configurations

**NOTE: Can run parallel with Files 10,12,13**

## Report

Return:
- Confirmation that file 14_llm_prompts.yaml was generated
- Path to the generated file
