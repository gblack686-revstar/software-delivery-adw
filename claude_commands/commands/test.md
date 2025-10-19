# Testing Phase

Execute automated testing with intelligent failure resolution and retry logic.

## Parameters

- adw_id: $1 (required) - The workflow ID
- issue_number: $2 (optional) - GitHub issue number for tracking
- skip_e2e: $3 (optional) - Set to "true" to skip E2E tests

## Run

uv run python adws/adw_test.py --adw-id "$1" ${2:+--issue-number "$2"} ${3:+--skip-e2e}

## Report

Return:
- Unit test results (passed/failed/total)
- E2E test results (passed/failed/total)
- Coverage percentage
- Number of retry attempts made
- Summary of fixes applied (if any)
- Final test status (all pass / some failures remain)
