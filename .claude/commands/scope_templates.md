# Scoping Phase (Manual Templates)

Execute template-based scoping to generate skeleton files for manual completion.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase
- context: $2 (optional) - Additional context for scoping

## Run

uv run python adws/adw_scoping_templates.py --adw-id "$1" ${2:+--context "$2"}

## Report

Return:
- List of all 13 template files created
- Path to CDK configuration templates
- Instructions for manual completion
- Estimated time to complete manually (2-4 hours)
- Next steps guidance
