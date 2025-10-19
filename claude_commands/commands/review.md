# Code Review Phase

Execute automated code review with severity classification and blocker resolution.

## Parameters

- adw_id: $1 (required) - The workflow ID
- issue_number: $2 (optional) - GitHub issue number for tracking

## Run

uv run python adws/adw_review.py --adw-id "$1" ${2:+--issue-number "$2"}

## Report

Return:
- Total issues found
- Blocker count (resolved / remaining)
- Tech debt count
- Skippable count
- List of all blocker issues with resolution status
- Recommendation: proceed to deploy or fix remaining blockers
