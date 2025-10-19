# Configuration Management

Execute configuration management operations for local and cloud environments.

## Parameters

- adw_id: $1 (required) - The workflow ID
- action: $2 (required) - Action to perform (generate|validate|sync|load|set|get)
- Additional parameters depend on action

## Run

uv run python adws/adw_config.py --adw-id "$1" --action "$2" "${@:3}"

## Report

Return (varies by action):
- generate: List of template files created
- validate: Validation status (pass/fail)
- sync: Number of parameters synced
- load: All configuration key-value pairs
- set: Confirmation of value set
- get: Key value
