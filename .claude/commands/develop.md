# Development Phase

Execute development phase to implement a user story in isolated worktree.

## Parameters

- adw_id: $1 (required) - The workflow ID
- story_id: $2 (required) - Story ID to implement (e.g., STORY-001)
- issue_number: $3 (optional) - GitHub issue number for tracking

## Run

uv run python adws/adw_develop.py --adw-id "$1" --story-id "$2" ${3:+--issue-number "$3"}

## Report

Return:
- Story ID implemented
- Files created/modified (with line counts)
- Tests created
- Commit hash
- Summary of changes made
