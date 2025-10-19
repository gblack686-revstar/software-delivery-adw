# Scoping Phase (AI-Powered)

Execute AI-powered scoping with sequential reasoning to generate comprehensive technical architecture.

**Recommended approach** - Fast, automated, high-quality scoping using AI.

**Alternative:** For manual template-based scoping, use `/scope_templates` instead.

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase
- context: $2 (optional) - Additional context for scoping

## Instructions

This command runs the ADW scoping agent using Claude Code CLI subprocess to:
- Generate 13 scoping files sequentially with cumulative context
- Perform ML research using Exa API before infrastructure selection
- Generate AWS service specifications
- Create CDK infrastructure configurations
- Generate cost estimates

**IMPORTANT:** This phase requires:
- Claude Code CLI installed (`claude --version`)
- ANTHROPIC_API_KEY in .env
- EXA_API_KEY in .env (for ML research)
- Discovery phase completed

## Run

```bash
# Validate parameters
if [ -z "$1" ]; then
  echo "Error: adw_id is required"
  echo "Usage: /scope <adw_id> [context]"
  exit 1
fi

ADW_ID="$1"
CONTEXT="${2:-}"

# Run scoping with optional context
if [ -n "$CONTEXT" ]; then
  uv run python adws/adw_scoping.py --adw-id "$ADW_ID" --context "$CONTEXT"
else
  uv run python adws/adw_scoping.py --adw-id "$ADW_ID"
fi
```

## Report

Return:
- List of all 14 files generated
- Path to CDK configuration directory
- Confirmation that scoping phase completed
- Estimated AWS costs from cost estimate file
