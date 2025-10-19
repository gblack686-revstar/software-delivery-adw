# Scoping Phase (Modular with Parallel Execution)

Execute AI-powered scoping with modular file generation, dependency management, and parallel execution.

**New modular approach** - Individual file control, parallel execution, better debugging.

**Alternatives:**
- `/scope_file_N` - Generate individual files (2-14)
- `/scope_templates` - Manual template-based scoping

## Parameters

- adw_id: $1 (required) - The workflow ID from discovery phase
- flags: $2+ (optional) - Additional flags (--force, --no-parallel, etc.)

## Instructions

This command runs the modular scoping agent with:
- Individual file generation with dependency tracking
- Parallel execution for independent files (Files 6+11, Files 10+12+13+14)
- Context summarization to prevent window overflow
- Resume capability (skips existing files)
- ML research using Exa API (File 6)

**IMPORTANT:** This phase requires:
- Claude Code CLI installed (`claude --version`)
- ANTHROPIC_API_KEY in .env
- EXA_API_KEY in .env (for ML research)
- Discovery phase completed

## Modular Commands

**Generate all missing files** (recommended):
```bash
/scope <adw_id>
```

**Generate specific file**:
```bash
/scope_file_2 <adw_id>  # Requirements analysis
/scope_file_3 <adw_id>  # User flows
...
/scope_file_14 <adw_id> # LLM prompts
```

**Parallel execution groups**:
- Files 6+11 run in parallel (ML research + Security) after File 5
- Files 10+12+13+14 run in parallel after File 9

## Run

```bash
# Validate parameters
if [ -z "$1" ]; then
  echo "Error: adw_id is required"
  echo "Usage: /scope <adw_id> [--force] [--no-parallel]"
  exit 1
fi

ADW_ID="$1"
shift  # Remove first parameter

# Run modular scoping with all remaining arguments as flags
uv run python adws/adw_scoping_modular.py --adw-id "$ADW_ID" --all "$@"
```

## Options

- `--force` - Regenerate files even if they exist
- `--no-parallel` - Disable parallel execution (run sequentially)
- `--context-mode full|summarized|smart` - Control context size (default: smart)

## Examples

```bash
# Generate all missing files with defaults
/scope abc123

# Force regenerate all files
/scope abc123 --force

# Sequential execution only
/scope abc123 --no-parallel

# Full context mode (may hit window limits)
/scope abc123 --context-mode full
```

## Report

Return:
- List of files generated (and which were skipped)
- Which files ran in parallel
- Path to CDK configuration directory
- Confirmation that scoping phase completed
- Estimated AWS costs from cost estimate file
- Any files that failed to generate
