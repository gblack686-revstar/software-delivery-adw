# Claude Commands Setup Guide

## The Problem (CORRECTED)

**ROOT CAUSE**: The backup/restore logic in `adws/adw_modules/agent.py` was causing `.claude` directory deletions.

### What Was Happening

1. **Initial Issue**: `.claude/commands/` directory kept disappearing
2. **First Theory** (INCORRECT): OneDrive/antivirus deleting dot-prefixed directories
3. **Actual Cause**: agent.py was doing this:
   ```python
   # Move .claude to temp directory before running Claude CLI
   shutil.move(claude_dir, backup_path)

   # ... run Claude CLI ...

   # Try to restore .claude after (would fail on interruptions)
   shutil.move(backup_path, claude_dir)
   ```
4. **Why It Failed**: If the process was interrupted, `.claude` wouldn't be restored

### Evidence

- ✅ `.docker` persists (dot-prefixed directories work fine)
- ✅ Test `.claude` directory persists for 30+ seconds
- ✅ Disabling backup/restore logic fixed the issue (commit `d97acc1`)
- ❌ OneDrive/antivirus theory was wrong

## The Solution (IMPLEMENTED)

### Current State

1. **Fixed**: Disabled backup/restore logic in agent.py (commit `d97acc1`)
2. **Safe Storage**: Commands stored in git as `claude_commands/` (commit `b5ce0e4`)
3. **Compatibility**: Junction created `.claude → claude_commands`
4. **Result**: Slash commands work, no deletions

### Directory Structure

```
software-delivery-adw/
├── .claude/                    → junction to claude_commands/
├── claude_commands/
│   └── commands/              ← actual commands stored here (in git)
│       ├── discover.md
│       ├── scope.md
│       ├── scope_file_2_requirements.md
│       └── ... (26 commands total)
```

### How It Works

- **Git tracks**: `claude_commands/commands/` (real files)
- **Claude CLI sees**: `.claude/commands/` (junction points to claude_commands)
- **Junction**: Windows junction persists indefinitely, no deletion

## Available Commands

### Core ADW Workflow (12 commands)
1. `/discover` - Discovery phase
2. `/scope` - Full scoping (uses modular approach)
3. `/planning` - Planning phase
4. `/develop` - Development phase
5. `/test` - Testing phase
6. `/review` - Review phase
7. `/deploy` - Deployment phase
8. `/test_infra` - Infrastructure testing
9. `/config` - Configuration management
10. `/install_worktree` - Worktree setup
11. `/resolve_failed_test` - Test failure resolution
12. `/resolve_failed_e2e_test` - E2E test failure resolution

### Modular Scoping (13 commands)
1. `/scope_file_2_requirements` - Requirements analysis
2. `/scope_file_3_user_flows` - User flow design
3. `/scope_file_4_data_models` - Data model design
4. `/scope_file_5_data_schema` - ERD generation
5. `/scope_file_6_ml_research` - ML/AI research (can run parallel with #11)
6. `/scope_file_7_aws_analysis` - AWS service analysis
7. `/scope_file_8_aws_services` - AWS service selection
8. `/scope_file_9_architecture` - Architecture design
9. `/scope_file_10_cdk_constructs` - CDK code generation (can run parallel with #12, #13, #14)
10. `/scope_file_11_security` - Security analysis (can run parallel with #6)
11. `/scope_file_12_cost_estimate` - Cost estimation (can run parallel with #10, #13, #14)
12. `/scope_file_13_validation_gates` - Validation gates (can run parallel with #10, #12, #14)
13. `/scope_file_14_llm_prompts` - LLM prompt templates (can run parallel with #10, #12, #13)

## Git History

### Commits Related to This Issue

```
d97acc1 - CRITICAL FIX: Disable .claude backup/restore logic that was causing deletions
b5ce0e4 - CRITICAL FIX: Rename .claude → claude_commands to prevent deletion
e5c9972 - Update .gitignore and README to reflect claude_commands/ structure
4e3cf9b - Add comprehensive guide (WRONG theory about OneDrive)
```

### What Actually Fixed It

**Commit `d97acc1`** - Disabled this problematic code in agent.py:
```python
# DISABLED: .claude backup logic was causing .claude directory to be deleted
# The backup/restore mechanism was fragile and caused data loss on interruptions
```

## Troubleshooting

### Junction missing after git operations

If the junction gets removed (e.g., after `git clean`), recreate it:

```bash
cd "C:\Users\gblac\OneDrive\Desktop\tac\software-delivery-adw"
cmd //c "mklink /J .claude claude_commands"
```

### Slash commands not working

1. Verify junction exists:
   ```bash
   ls -la .claude/commands/
   ```

2. If missing, recreate junction:
   ```bash
   cmd //c "mklink /J .claude claude_commands"
   ```

3. Verify Claude CLI can find commands:
   ```bash
   ls -la .claude/commands/ | wc -l  # Should show 26+ files
   ```

### Using commands without slash notation

You can call Python scripts directly:

```bash
# Instead of /discover
uv run python adws/adw_discovery.py --adw-id my_project

# Instead of /scope
uv run python adws/adw_scoping_modular.py --adw-id my_project --all

# Individual scoping files
uv run python adws/adw_scoping_modular.py --adw-id my_project --file-num 2
```

## Never Do This

❌ **Do NOT re-enable the backup/restore logic in agent.py** - it causes data loss on interruptions

❌ **Do NOT delete claude_commands/** - that's where the real commands are stored

❌ **Do NOT commit .claude/ to git** - it's a junction, not a real directory

## Summary

**Problem**: agent.py backup/restore logic was fragile and caused `.claude` deletions
**Fix**: Disabled the backup/restore code
**Current State**: Commands in `claude_commands/`, junction at `.claude`, everything works
**Maintenance**: Recreate junction if needed after git operations
