# Deployment Phase

Execute AWS infrastructure deployment using CDK configurations.

## Parameters

- adw_id: $1 (required) - The workflow ID
- environment: $2 (required) - Target environment (dev|staging|production)
- issue_number: $3 (optional) - GitHub issue number for tracking

## Run

uv run python adws/adw_deploy.py --adw-id "$1" --environment "$2" ${3:+--issue-number "$3"}

## Report

Return:
- Environment deployed to
- All stack names with status
- Stack outputs (URLs, endpoints)
- Deployment duration
- Health check results
- Cost estimate for environment
- Next steps recommendation
