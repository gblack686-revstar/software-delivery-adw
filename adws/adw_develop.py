#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml", "pydantic"]
# ///

"""Developer Agent - Feature implementation in isolated worktrees.

Usage:
    uv run adw_develop.py --story-id STORY-001 --adw-id <adw-id> [--issue-number <number>]

Workflow:
1. Load state and validate worktree exists
2. Read story details from planning files
3. Implement feature in isolated worktree
4. Commit changes in worktree
5. Push and update PR

This workflow REQUIRES that adw_planning.py has been run first to create the worktree.
"""

import argparse
import sys
import logging
import yaml
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
    implement_plan,
)
from adws.adw_modules.utils import setup_logger
from adws.adw_modules.data_types import GitHubIssue
from adws.adw_modules.worktree_ops import validate_worktree

AGENT_IMPLEMENTOR = "sdlc_implementor"


def find_story_details(story_id: str, stories_path: str, logger: logging.Logger) -> Optional[dict]:
    """Find story details from stories YAML file.

    Args:
        story_id: Story ID to find (e.g., "STORY-001")
        stories_path: Path to stories YAML file
        logger: Logger instance

    Returns:
        Story details dict or None if not found
    """
    try:
        with open(stories_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        stories = data.get('stories', [])
        for story in stories:
            if story.get('id') == story_id:
                return story

        logger.error(f"Story {story_id} not found in {stories_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading stories file: {e}")
        return None


def create_implementation_plan_from_story(
    story: dict,
    adw_id: str,
    worktree_path: str,
    logger: logging.Logger
) -> Optional[str]:
    """Create a simple implementation plan file from story details.

    Args:
        story: Story details dict
        adw_id: ADW workflow ID
        worktree_path: Path to worktree
        logger: Logger instance

    Returns:
        Path to plan file (relative to worktree) or None on error
    """
    try:
        # Create plans directory in worktree
        plans_dir = Path(worktree_path) / "plans"
        plans_dir.mkdir(exist_ok=True)

        # Create plan file
        plan_filename = f"{story['id'].lower()}_plan.md"
        plan_path = plans_dir / plan_filename

        # Format acceptance criteria
        criteria_lines = []
        for criterion in story.get('acceptance_criteria', []):
            criteria_lines.append(f"- [ ] {criterion}")

        # Write plan
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(f"""# Implementation Plan: {story['title']}

**Story ID:** {story['id']}
**ADW ID:** {adw_id}
**Sprint:** {story.get('sprint', 'TBD')}
**Priority:** {story.get('priority', 'P1')}
**Estimated Hours:** {story.get('estimated_hours', 'TBD')}

## User Story
{story.get('user_story', 'N/A')}

## Description
{story.get('description', 'N/A')}

## Dependencies
{', '.join(story.get('dependencies', [])) if story.get('dependencies') else 'None'}

## Acceptance Criteria
{chr(10).join(criteria_lines)}

## Implementation Tasks

### 1. Setup
- Review requirements
- Identify affected components

### 2. Implementation
- Implement core functionality
- Add error handling
- Add logging

### 3. Testing
- Unit tests
- Integration tests
- E2E tests (if applicable)

### 4. Documentation
- Update README if needed
- Add inline documentation
- Update API docs if applicable

## Technical Notes
- Follow existing code patterns
- Ensure AWS best practices
- Use CDK constructs where applicable
""")

        # Return relative path from worktree
        return f"plans/{plan_filename}"

    except Exception as e:
        logger.error(f"Error creating plan file: {e}")
        return None


def main():
    """Main entry point for developer agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Developer Agent")
    parser.add_argument("--story-id", required=True, help="Story ID to implement (e.g., STORY-001)")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--issue-number", help="GitHub issue number (optional)")
    args = parser.parse_args()

    adw_id = args.adw_id
    story_id = args.story_id
    issue_number = args.issue_number

    # Load state
    logger = setup_logger(adw_id, "adw_develop")
    state = ADWState.load(adw_id, logger)

    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        print(f"❌ Error: No state found for ADW ID: {adw_id}")
        print("Run adw_planning.py first to create the worktree and state")
        sys.exit(1)

    logger.info(f"ADW Develop starting - ID: {adw_id}, Story: {story_id}, Issue: {issue_number}")

    print(f"\n💻 Starting Development Phase")
    print(f"📋 ADW ID: {adw_id}")
    print(f"🎫 Story: {story_id}")

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        print(f"❌ Error: Worktree validation failed: {error}")
        print("Run adw_planning.py first to create the worktree")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\nRun adw_planning.py first")
            )
        sys.exit(1)

    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")
    print(f"🏠 Worktree: {worktree_path}")

    # Get issue if provided
    issue: Optional[GitHubIssue] = None
    if issue_number:
        try:
            github_repo_url = get_repo_url()
            repo_path = extract_repo_path(github_repo_url)
            issue = fetch_issue(issue_number, repo_path)
            logger.info(f"Fetched issue #{issue_number}")

            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"✅ Starting development for {story_id}")
            )
        except Exception as e:
            logger.warning(f"Could not fetch issue: {e}")
            print(f"⚠️ Warning: Could not fetch issue: {e}")

    # Check prerequisites
    stories_path = state.get("planning.stories")
    if not stories_path:
        logger.error("Planning phase not complete - no stories file found")
        print("❌ Error: Planning phase not complete")
        print("Run adw_planning.py first")
        sys.exit(1)

    # Read story details
    print(f"\n📖 Reading story from: {stories_path}")
    story = find_story_details(story_id, stories_path, logger)

    if not story:
        print(f"❌ Error: Story {story_id} not found in {stories_path}")
        sys.exit(1)

    print(f"✅ Found story: {story['title']}")
    logger.info(f"Story details: {story}")

    # Create implementation plan from story
    print(f"\n📝 Creating implementation plan...")
    plan_file = create_implementation_plan_from_story(story, adw_id, worktree_path, logger)

    if not plan_file:
        print(f"❌ Error: Could not create implementation plan")
        sys.exit(1)

    print(f"✅ Plan created: {plan_file}")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"📝 Implementation plan created: {plan_file}")
        )

    # Implement the feature using workflow_ops
    print(f"\n🚀 Implementing feature in worktree...")
    logger.info(f"Implementing plan: {plan_file}")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"🚀 Implementing {story_id} in isolated environment...")
        )

    impl_response = implement_plan(plan_file, adw_id, logger, agent_name=AGENT_IMPLEMENTOR, working_dir=worktree_path)

    if not impl_response.success:
        logger.error(f"Implementation failed: {impl_response.output}")
        print(f"❌ Implementation failed: {impl_response.output}")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"❌ Implementation failed: {impl_response.output}")
            )
        sys.exit(1)

    print(f"✅ Implementation complete!")
    logger.info("Implementation successful")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_IMPLEMENTOR, f"✅ {story_id} implementation complete")
        )

    # Update state
    if "development" not in state._extended_data:
        state._extended_data["development"] = {"features": []}

    state.update_phase("development", started=True)

    # Add feature to state
    feature_data = {
        "story_id": story_id,
        "status": "implemented",
        "plan_file": plan_file,
        "branch": state.get("branch_name")
    }

    state._extended_data["development"]["features"].append(feature_data)
    state.save("adw_develop")

    # Commit changes if we have an issue
    if issue:
        # Classify issue if not already done
        issue_command = state.get("issue_class")
        if not issue_command:
            logger.info("No issue classification in state, classifying now")
            issue_command, error = classify_issue(issue, adw_id, logger)
            if error:
                logger.error(f"Error classifying issue: {error}")
                issue_command = "/feature"
            else:
                state.update(issue_class=issue_command)
                state.save("adw_develop")

        # Create commit message
        logger.info("Creating implementation commit")
        commit_msg, error = create_commit(AGENT_IMPLEMENTOR, issue, issue_command, adw_id, logger, worktree_path)

        if not error:
            # Commit changes (in worktree)
            success, error = commit_changes(commit_msg, cwd=worktree_path)

            if success:
                logger.info(f"Committed implementation: {commit_msg}")
                print(f"\n✅ Implementation committed")

                if issue_number:
                    make_issue_comment(
                        issue_number,
                        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementation committed")
                    )

                # Finalize git operations (push and PR)
                finalize_git_operations(state, logger, cwd=worktree_path)

                if issue_number:
                    make_issue_comment(
                        issue_number,
                        format_issue_message(adw_id, "ops", f"✅ {story_id} development phase completed")
                    )
            else:
                logger.error(f"Error committing implementation: {error}")
                print(f"❌ Error committing: {error}")

    print(f"\n✅ Development tracking initialized for {story_id}")
    print(f"\n🎯 Next steps:")
    print(f"   uv run adws/adw_test.py --adw-id {adw_id} --issue-number {issue_number if issue_number else '<issue>'}")
    print(f"   uv run adws/adw_review.py --adw-id {adw_id} --issue-number {issue_number if issue_number else '<issue>'}")

    # Save final state
    state.save("adw_develop")


if __name__ == "__main__":
    main()
