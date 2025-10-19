# Claude Commands Setup Guide

## The Problem

**TL;DR**: OneDrive and/or Windows antivirus automatically delete directories starting with a dot (`.claude`), causing slash commands to disappear.

### What's Happening

1. Claude Code CLI expects commands in `.claude/commands/` by default
2. OneDrive/Windows antivirus actively deletes directories starting with `.`
3. This creates a cycle: `.claude/` appears → immediately deleted → repeats
4. Commands are safely stored in git as `claude_commands/commands/` instead

## The Solution

### Current State

- ✅ **All 26 commands are safe in git**: `claude_commands/commands/`
- ✅ **Protected from deletion**: `claude_commands/` is not dot-prefixed
- ❌ **Claude CLI can't find them**: CLI looks in `.claude/commands/`

### Workaround Options

#### Option 1: Create Temporary Symlink (Recommended for quick testing)

```bash
# Create junction (Windows symlink) - may still get deleted by OneDrive
mklink /J .claude claude_commands

# If it gets deleted, recreate it before running claude commands
# This is temporary and will be deleted by OneDrive/antivirus
```

#### Option 2: Copy Commands Temporarily

```bash
# Copy commands to .claude before using Claude CLI
cp -r claude_commands/.claude .claude

# Use Claude CLI
claude

# .claude will be auto-deleted by OneDrive shortly after
```

#### Option 3: Disable OneDrive for This Directory (Best permanent solution)

1. Right-click on the `software-delivery-adw` folder
2. Select "Always keep on this device" or exclude from OneDrive sync
3. Create permanent symlink:
   ```bash
   mklink /J .claude claude_commands
   ```

#### Option 4: Add OneDrive Exception

1. Open OneDrive settings
2. Go to "Sync and backup" → "Advanced settings"
3. Add `software-delivery-adw\.claude` to exclusions
4. Create permanent symlink:
   ```bash
   mklink /J .claude claude_commands
   ```

## Files in claude_commands/commands/

All 26 slash commands are available:

### Core ADW Workflow (12 commands)
1. `discover.md` - Discovery phase
2. `scope.md` - Full scoping (uses modular approach)
3. `planning.md` - Planning phase
4. `develop.md` - Development phase
5. `test.md` - Testing phase
6. `review.md` - Review phase
7. `deploy.md` - Deployment phase
8. `test_infra.md` - Infrastructure testing
9. `config.md` - Configuration management
10. `install_worktree.md` - Worktree setup
11. `resolve_failed_test.md` - Test failure resolution
12. `resolve_failed_e2e_test.md` - E2E test failure resolution

### Modular Scoping (13 commands)
1. `scope_file_2_requirements.md` - Requirements analysis
2. `scope_file_3_user_flows.md` - User flow design
3. `scope_file_4_data_models.md` - Data model design
4. `scope_file_5_data_schema.md` - ERD generation
5. `scope_file_6_ml_research.md` - ML/AI research
6. `scope_file_7_aws_analysis.md` - AWS service analysis
7. `scope_file_8_aws_services.md` - AWS service selection
8. `scope_file_9_architecture.md` - Architecture design
9. `scope_file_10_cdk_constructs.md` - CDK code generation
10. `scope_file_11_security.md` - Security analysis
11. `scope_file_12_cost_estimate.md` - Cost estimation
12. `scope_file_13_validation_gates.md` - Validation gates
13. `scope_file_14_llm_prompts.md` - LLM prompt templates

## Git Commits

The rename from `.claude/` to `claude_commands/` was done in commit `b5ce0e4`:

```
b5ce0e4 CRITICAL FIX: Rename .claude → claude_commands to prevent deletion
d97acc1 CRITICAL FIX: Disable .claude backup/restore logic that was causing deletions
```

## Never Do This

❌ **Do NOT rename `claude_commands/` back to `.claude/`** - it will be auto-deleted by OneDrive/antivirus within seconds

❌ **Do NOT commit `.claude/` to git** - it won't persist on disk

## Troubleshooting

### .claude keeps appearing and disappearing

This is expected. Something (likely Claude Code CLI) creates `.claude/`, then OneDrive/antivirus immediately deletes it. This is harmless - your commands are safe in `claude_commands/`.

### Slash commands not working in Claude CLI

You need to either:
1. Create a temporary junction: `mklink /J .claude claude_commands`
2. Or use the Python scripts directly: `uv run python adws/adw_scoping_modular.py`

### How to use slash commands

If you want to use slash commands like `/scope` or `/discover`:

1. Create temporary junction before starting Claude CLI:
   ```bash
   mklink /J .claude claude_commands
   ```

2. Start Claude CLI immediately:
   ```bash
   claude
   ```

3. Use your slash commands (they'll work until OneDrive deletes .claude)

Alternatively, call the Python scripts directly without needing slash commands:
```bash
# Instead of /discover
uv run python adws/adw_discovery.py --adw-id my_project

# Instead of /scope
uv run python adws/adw_scoping_modular.py --adw-id my_project --all
```

## Investigation Results

From commit history and testing:
- **Root cause**: OneDrive and/or Windows Defender Antivirus
- **Deletion speed**: <5 seconds after creation
- **Affected directories**: Any starting with `.` (dot prefix)
- **Unaffected**: `claude_commands/` (no dot prefix) - persists indefinitely
- **Evidence**: Renamed directory persisted, original .claude deleted repeatedly
