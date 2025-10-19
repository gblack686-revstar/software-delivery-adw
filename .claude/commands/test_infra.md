# Infrastructure Testing Phase

Execute infrastructure validation and health checks for deployed AWS resources.

## Parameters

- adw_id: $1 (required) - The workflow ID
- issue_number: $2 (optional) - GitHub issue number for tracking

## Run

uv run python adws/adw_test_infra.py --adw-id "$1" ${2:+--issue-number "$2"}

## Report

Return:
- Total resources validated
- Pass count
- Warning count
- Failure count
- List of all failed checks (if any)
- List of warnings (if any)
- Overall infrastructure health status
- Recommendation (ready for use / needs fixes)
