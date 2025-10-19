# Planning Phase

Execute planning phase with isolated worktree creation and agile story generation.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery/scoping
- sprints: $2 (optional, default: 4) - Number of sprints to plan
- issue_number: $3 (optional) - GitHub issue number for tracking

## Run

uv run python adws/adw_planning.py --adw-id "$1" --sprints "${2:-4}" ${3:+--issue-number "$3"}

## Report

Return:
- Worktree location
- Allocated backend and frontend ports
- Number of stories created
- Sprint breakdown
- Branch name
