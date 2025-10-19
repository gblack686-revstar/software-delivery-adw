# Discovery Phase

Execute the discovery phase to gather client requirements and qualify the project.

## Instructions

This command runs the ADW discovery agent to:
- Gather client/deal information
- Qualify the project opportunity
- Generate discovery brief document
- Initialize ADW state with unique workflow ID

## Run

```bash
uv run adws/adw_discovery.py
```

## What This Does

1. **Prompts for Project Information:**
   - Client name and contact
   - Project description and goals
   - Tech stack preferences
   - Timeline and budget
   - Success criteria

2. **Generates Discovery Brief:**
   - Creates `specs/{adw_id}/1_discovery_brief.md`
   - Documents all gathered requirements
   - Qualifies the opportunity

3. **Initializes State:**
   - Creates unique ADW ID (8-character hash)
   - Initializes state file at `agents/{adw_id}/adw_state.json`
   - Marks discovery phase as started

## Output

After completion, you will receive:
- **ADW ID**: Unique identifier for this workflow (save this!)
- **Discovery Brief**: Located at `specs/{adw_id}/1_discovery_brief.md`

## Next Steps

After discovery completes successfully, run:
```bash
/scope
```

## Usage Examples

**Interactive Mode:**
```bash
uv run adws/adw_discovery.py
```

**With Pre-defined Information:**
```bash
uv run adws/adw_discovery.py --deal-info "Build a Task Manager API with FastAPI, PostgreSQL, React frontend. Deploy to AWS."
```

**With Specific ADW ID:**
```bash
uv run adws/adw_discovery.py --adw-id abc12345 --deal-info "..."
```

## Report

Return:
- The ADW ID generated
- Path to the discovery brief created
- Confirmation that state was initialized
