#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml", "pydantic"]
# ///

"""Planning Agent - Implementation plan and agile stories with worktree isolation.

Usage:
    uv run adw_planning.py --adw-id <adw-id> [--issue-number <number>] [--sprints 4]

Workflow:
1. Load or create state
2. Create isolated worktree with unique ports
3. Generate implementation plan (PRD and agile stories)
4. Commit plan in worktree
5. Push and create/update PR

This workflow creates an isolated git worktree under trees/<adw_id>/ for
parallel execution without interference.
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState
from adws.adw_modules.git_ops import commit_changes, finalize_git_operations
from adws.adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adws.adw_modules.workflow_ops import (
    classify_issue,
    create_commit,
    format_issue_message,
    ensure_adw_id,
    AGENT_PLANNER,
)
from adws.adw_modules.utils import setup_logger
from adws.adw_modules.data_types import GitHubIssue, AgentTemplateRequest
from adws.adw_modules.agent import execute_template
from adws.adw_modules.worktree_ops import (
    create_worktree,
    validate_worktree,
    get_ports_for_adw,
    is_port_available,
    find_next_available_ports,
    setup_worktree_environment,
)


def generate_branch_name_from_adw(adw_id: str, sprints: int) -> str:
    """Generate a branch name for the planning phase.

    Args:
        adw_id: ADW workflow ID
        sprints: Number of sprints

    Returns:
        Branch name string
    """
    return f"plan-{sprints}sprint-{adw_id}"


def create_planning_files(adw_id: str, sprints: int, specs_dir: Path, logger: logging.Logger) -> tuple[Path, Path]:
    """Create PRD and stories template files.

    Args:
        adw_id: ADW workflow ID
        sprints: Number of sprints
        specs_dir: Directory to create files in
        logger: Logger instance

    Returns:
        Tuple of (prd_path, stories_path)
    """
    # Create PRD
    prd_path = specs_dir / "7_planning_prd.md"
    logger.info(f"Creating PRD at: {prd_path}")

    with open(prd_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Implementation Plan

**ADW ID:** {adw_id}
**Timeline:** {sprints} sprints (approx. {sprints * 2} weeks)

## Executive Summary

[Provide 1-2 paragraph overview of the project]

## Features by Priority

### P0: MVP Features
1. Feature 1
2. Feature 2

### P1: Launch Features
1. Feature 3

## Sprint Breakdown

### Sprint 1
**Goal:** Infrastructure setup
**Stories:** STORY-001, STORY-002

### Sprint 2
**Goal:** Core features
**Stories:** STORY-003, STORY-004

## Technical Approach

[Describe overall technical approach]

## Risks and Mitigations

1. **Risk:** Description
   **Mitigation:** How to address
""")

    # Create Stories
    stories_path = specs_dir / "8_agile_stories.yaml"
    logger.info(f"Creating stories at: {stories_path}")

    with open(stories_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Agile Stories

stories:
  - id: STORY-001
    title: "Set up AWS infrastructure"
    user_story: "As a developer, I want the AWS infrastructure provisioned"
    description: |
      Set up CDK project and provision core AWS services
    acceptance_criteria:
      - CDK project initialized
      - Core AWS services deployed
      - Infrastructure tagged appropriately
    dependencies: []
    sprint: 1
    priority: P0
    estimated_hours: 16

  - id: STORY-002
    title: "Implement user authentication"
    user_story: "As a user, I want to register and login"
    description: |
      Implement authentication flow with Cognito
    acceptance_criteria:
      - Registration endpoint working
      - Login endpoint working
      - JWT tokens issued
    dependencies:
      - STORY-001
    sprint: 1
    priority: P0
    estimated_hours: 12
""")

    return prd_path, stories_path


def main():
    """Main entry point for planning agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Planning Agent")
    parser.add_argument("--adw-id", help="Workflow ID (will be created if not provided)")
    parser.add_argument("--issue-number", help="GitHub issue number (optional)")
    parser.add_argument("--sprints", type=int, default=4, help="Number of sprints")
    args = parser.parse_args()

    # Ensure ADW ID exists with initialized state
    temp_logger = setup_logger(args.adw_id, "adw_planning") if args.adw_id else None
    adw_id = ensure_adw_id(args.issue_number, args.adw_id, temp_logger)

    # Load the state that was created/found by ensure_adw_id
    state = ADWState.load(adw_id, temp_logger)

    # Ensure state has the adw_id field
    if not state.get("adw_id"):
        state.update(adw_id=adw_id)

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_planning")
    logger.info(f"ADW Planning starting - ID: {adw_id}, Issue: {args.issue_number}, Sprints: {args.sprints}")

    print(f"\n>>> Starting Planning Phase")
    print(f"ADW ID: {adw_id}")
    print(f"Sprints: {args.sprints}")

    # Check prerequisites
    scoping_complete = state.get("scoping.user_flows")
    if not scoping_complete:
        logger.warning("Scoping phase not complete, continuing anyway")
        print("⚠️ Warning: Scoping phase not complete")

    # Get issue if provided
    issue: Optional[GitHubIssue] = None
    issue_number = args.issue_number
    repo_path = None

    if issue_number:
        try:
            github_repo_url = get_repo_url()
            repo_path = extract_repo_path(github_repo_url)
            issue = fetch_issue(issue_number, repo_path)
            logger.info(f"Fetched issue #{issue_number}")

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "✅ Starting isolated planning phase")
            )
        except Exception as e:
            logger.warning(f"Could not fetch issue: {e}")
            print(f"⚠️ Warning: Could not fetch issue: {e}")

    # Check if worktree already exists
    valid, error = validate_worktree(adw_id, state)
    if valid:
        logger.info(f"Using existing worktree for {adw_id}")
        worktree_path = state.get("worktree_path")
        backend_port = state.get("backend_port")
        frontend_port = state.get("frontend_port")
        print(f"✅ Using existing worktree: {worktree_path}")
    else:
        # Allocate ports for this instance
        backend_port, frontend_port = get_ports_for_adw(adw_id)

        # Check port availability
        if not (is_port_available(backend_port) and is_port_available(frontend_port)):
            logger.warning(f"Deterministic ports {backend_port}/{frontend_port} are in use, finding alternatives")
            backend_port, frontend_port = find_next_available_ports(adw_id)

        logger.info(f"Allocated ports - Backend: {backend_port}, Frontend: {frontend_port}")
        state.update(backend_port=backend_port, frontend_port=frontend_port)
        state.save("adw_planning")

        # Generate branch name
        branch_name = generate_branch_name_from_adw(adw_id, args.sprints)
        state.update(branch_name=branch_name)
        state.save("adw_planning")
        logger.info(f"Will create branch in worktree: {branch_name}")

        # Create worktree
        logger.info(f"Creating worktree for {adw_id}")
        print(f"\n🌳 Creating isolated worktree...")

        worktree_path, error = create_worktree(adw_id, branch_name, logger)

        if error:
            logger.error(f"Error creating worktree: {error}")
            print(f"❌ Error creating worktree: {error}")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", f"❌ Error creating worktree: {error}")
                )
            sys.exit(1)

        state.update(worktree_path=worktree_path)
        state.save("adw_planning")
        logger.info(f"Created worktree at {worktree_path}")
        print(f"✅ Created worktree: {worktree_path}")

        # Setup worktree environment (create .ports.env)
        setup_worktree_environment(worktree_path, backend_port, frontend_port, logger)

        # Run install_worktree command to set up the isolated environment
        logger.info("Setting up isolated environment with custom ports")
        print(f"🔧 Setting up environment (Backend: {backend_port}, Frontend: {frontend_port})...")

        install_request = AgentTemplateRequest(
            agent_name="ops",
            slash_command="/install_worktree",
            args=[worktree_path, str(backend_port), str(frontend_port)],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        install_response = execute_template(install_request)
        if not install_response.success:
            logger.error(f"Error setting up worktree: {install_response.output}")
            print(f"❌ Error setting up worktree: {install_response.output}")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", f"❌ Error setting up worktree: {install_response.output}")
                )
            sys.exit(1)

        logger.info("Worktree environment setup complete")
        print(f"✅ Environment setup complete")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"✅ Working in isolated worktree: {worktree_path}\n"
                f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}"
            )
        )

    # Create planning files in specs directory (outside worktree)
    specs_dir = Path(f"specs/{adw_id}")
    specs_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📄 Creating planning documents...")
    prd_path, stories_path = create_planning_files(adw_id, args.sprints, specs_dir, logger)

    print(f"   [OK] Created: {prd_path}")
    print(f"   [OK] Created: {stories_path}")

    # Update state
    state.update_phase(
        "planning",
        started=True,
        completed=False,
        sprints=args.sprints,
        prd=str(prd_path),
        stories=str(stories_path),
        total_stories=2
    )
    state.save("adw_planning")

    # Commit planning files (in worktree)
    if issue:
        # Classify issue if not already done
        issue_command = state.get("issue_class")
        if not issue_command:
            logger.info("No issue classification in state, classifying now")
            from adws.adw_modules.workflow_ops import classify_issue
            issue_command, error = classify_issue(issue, adw_id, logger)
            if error:
                logger.error(f"Error classifying issue: {error}")
                issue_command = "/feature"
            else:
                state.update(issue_class=issue_command)
                state.save("adw_planning")

        # Create commit message
        logger.info("Creating planning commit")
        commit_msg, error = create_commit(AGENT_PLANNER, issue, issue_command, adw_id, logger, worktree_path)

        if not error:
            # Commit the plan (in worktree)
            success, error = commit_changes(commit_msg, cwd=worktree_path)

            if success:
                logger.info(f"Committed plan: {commit_msg}")
                print(f"\n✅ Plan committed")

                if issue_number:
                    make_issue_comment(
                        issue_number,
                        format_issue_message(adw_id, AGENT_PLANNER, "✅ Plan committed")
                    )

                # Finalize git operations (push and PR)
                finalize_git_operations(state, logger, cwd=worktree_path)

                if issue_number:
                    make_issue_comment(
                        issue_number,
                        format_issue_message(adw_id, "ops", "✅ Isolated planning phase completed")
                    )
            else:
                logger.error(f"Error committing plan: {error}")
                print(f"❌ Error committing plan: {error}")

    print(f"\n[SUCCESS] Planning templates created!")
    print(f"\nReview files in: {specs_dir}")
    print(f"Worktree: {worktree_path}")
    print(f"\nNext steps:")
    print(f"  - Review and edit planning documents")
    print(f"  - Run: uv run adws/adw_develop.py --story-id STORY-001 --adw-id {adw_id}")

    # Save final state
    state.save("adw_planning")


if __name__ == "__main__":
    main()
