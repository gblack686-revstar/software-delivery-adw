#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""ADW Review - AI Developer Workflow for agentic code review in isolated worktrees.

Usage:
    uv run adw_review.py --adw-id <adw-id> [--issue-number <number>] [--skip-resolution]

Workflow:
1. Load state and validate worktree exists
2. Find spec file from worktree
3. Review implementation against specification in worktree
4. If blocker issues found and --skip-resolution not set:
   - Create patch plans for blockers (3 attempts max)
   - Implement resolutions
5. Post results as commit message
6. Commit review results in worktree
7. Push and update PR

This workflow REQUIRES that adw_planning.py has been run first to create the worktree.
"""

import argparse
import sys
import logging
import json
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

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
    create_commit,
    format_issue_message,
    implement_plan,
    find_spec_file,
)
from adws.adw_modules.utils import setup_logger, parse_json
from adws.adw_modules.data_types import (
    AgentTemplateRequest,
    ReviewResult,
    ReviewIssue,
    AgentPromptResponse,
)
from adws.adw_modules.agent import execute_template
from adws.adw_modules.worktree_ops import validate_worktree

# Agent name constants
AGENT_REVIEWER = "reviewer"
AGENT_REVIEW_PATCH_PLANNER = "review_patch_planner"

# Maximum number of review retry attempts after resolution
MAX_REVIEW_RETRY_ATTEMPTS = 3


def run_review(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> ReviewResult:
    """Run the review using the /review command."""
    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEWER,
        slash_command="/review",
        args=[adw_id, spec_file, AGENT_REVIEWER],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"review_request: {request.model_dump_json(indent=2, by_alias=True)}")
    response = execute_template(request)
    logger.debug(f"review_response: {response.model_dump_json(indent=2, by_alias=True)}")

    if not response.success:
        logger.error(f"Review failed: {response.output}")
        return ReviewResult(
            success=False,
            review_summary=f"Review failed: {response.output}",
            review_issues=[],
            screenshots=[],
            screenshot_urls=[],
        )

    # Parse the review result
    try:
        result = parse_json(response.output, ReviewResult)
        return result
    except Exception as e:
        logger.error(f"Error parsing review result: {e}")
        return ReviewResult(
            success=False,
            review_summary=f"Error parsing review result: {e}",
            review_issues=[],
            screenshots=[],
            screenshot_urls=[],
        )


def create_review_patch_plan(
    issue: ReviewIssue,
    issue_num: int,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Create a patch plan for a review issue."""
    # Build patch command with issue details
    patch_args = [
        f"Issue #{issue_num}: {issue.issue_description}",
        f"Resolution: {issue.issue_resolution}",
        f"Severity: {issue.issue_severity}",
    ]

    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEW_PATCH_PLANNER,
        slash_command="/patch",
        args=patch_args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    return execute_template(request)


def resolve_blocker_issues(
    blocker_issues: List[ReviewIssue],
    issue_number: Optional[str],
    adw_id: str,
    worktree_path: str,
    logger: logging.Logger
) -> None:
    """Resolve blocker issues by creating and implementing patches.

    Args:
        blocker_issues: List of blocker issues to resolve
        issue_number: GitHub issue number (optional)
        adw_id: ADW workflow ID
        worktree_path: Path to the worktree
        logger: Logger instance
    """
    logger.info(f"Found {len(blocker_issues)} blocker issues, attempting resolution")
    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_REVIEW_PATCH_PLANNER,
                f"🔧 Found {len(blocker_issues)} blocker issues, creating resolution plans..."
            )
        )

    # Create and implement patches for each blocker
    for i, issue in enumerate(blocker_issues, 1):
        logger.info(f"Resolving blocker {i}/{len(blocker_issues)}: {issue.issue_description}")

        # Create patch plan
        plan_response = create_review_patch_plan(issue, i, adw_id, logger, working_dir=worktree_path)

        if not plan_response.success:
            logger.error(f"Failed to create patch plan: {plan_response.output}")
            continue

        # Extract plan file path
        plan_file = plan_response.output.strip()

        # Implement the patch
        logger.info(f"Implementing patch from plan: {plan_file}")
        impl_response = implement_plan(plan_file, adw_id, logger, working_dir=worktree_path)

        if not impl_response.success:
            logger.error(f"Failed to implement patch: {impl_response.output}")
            continue

        logger.info(f"Successfully resolved blocker {i}")


def build_review_summary(review_result: ReviewResult) -> str:
    """Build a formatted summary of the review results for GitHub comment.

    Args:
        review_result: The review result containing summary, issues, and screenshots

    Returns:
        Formatted markdown string for GitHub comment
    """
    summary_parts = [f"## 📊 Review Summary\n\n{review_result.review_summary}"]

    # Add review issues grouped by severity
    if review_result.review_issues:
        summary_parts.append("\n## 🔍 Issues Found")

        # Group by severity
        blockers = [i for i in review_result.review_issues if i.issue_severity == "blocker"]
        tech_debts = [i for i in review_result.review_issues if i.issue_severity == "tech_debt"]
        skippables = [i for i in review_result.review_issues if i.issue_severity == "skippable"]

        if blockers:
            summary_parts.append(f"\n### 🚨 Blockers ({len(blockers)})")
            for issue in blockers:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_path:
                    summary_parts.append(f"  - Screenshot: `{issue.screenshot_path}`")

        if tech_debts:
            summary_parts.append(f"\n### ⚠️ Tech Debt ({len(tech_debts)})")
            for issue in tech_debts:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_path:
                    summary_parts.append(f"  - Screenshot: `{issue.screenshot_path}`")

        if skippables:
            summary_parts.append(f"\n### 💡 Skippable ({len(skippables)})")
            for issue in skippables:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_path:
                    summary_parts.append(f"  - Screenshot: `{issue.screenshot_path}`")

    # Add screenshots section
    if review_result.screenshots:
        summary_parts.append(f"\n## 📸 Screenshots")
        summary_parts.append(f"Captured {len(review_result.screenshots)} screenshots\n")
        for i, screenshot_path in enumerate(review_result.screenshots):
            summary_parts.append(f"- Screenshot {i+1}: `{screenshot_path}`")

    return "\n".join(summary_parts)


def main():
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="ADW Review - Automated code review workflow")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--issue-number", help="GitHub issue number (optional)")
    parser.add_argument("--skip-resolution", action="store_true", help="Skip automatic blocker resolution")
    args = parser.parse_args()

    adw_id = args.adw_id
    issue_number = args.issue_number
    skip_resolution = args.skip_resolution

    # Load state
    logger = setup_logger(adw_id, "adw_review")
    state = ADWState.load(adw_id, logger)

    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        print(f"Error: No state found for ADW ID: {adw_id}")
        print("Run adw_planning.py first to create the worktree and state")
        sys.exit(1)

    logger.info(f"ADW Review starting - ID: {adw_id}, Issue: {issue_number}, Skip Resolution: {skip_resolution}")

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        print(f"Error: Worktree validation failed: {error}")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\nRun adw_planning.py first")
            )
        sys.exit(1)

    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")

    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"✅ Starting isolated review phase\n"
                f"🏠 Worktree: {worktree_path}\n"
                f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                f"🔧 Issue Resolution: {'Disabled' if skip_resolution else 'Enabled'}"
            )
        )

    # Find spec file from current branch (in worktree)
    logger.info("Looking for spec file in worktree")
    spec_file = find_spec_file(state, logger)

    if not spec_file:
        error_msg = "Could not find spec file for review"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        if issue_number:
            make_issue_comment(issue_number, format_issue_message(adw_id, "ops", f"❌ {error_msg}"))
        sys.exit(1)

    logger.info(f"Found spec file: {spec_file}")
    if issue_number:
        make_issue_comment(issue_number, format_issue_message(adw_id, "ops", f"📋 Found spec file: {spec_file}"))

    # Run review with retry logic
    review_attempt = 0
    review_result = None

    while review_attempt < MAX_REVIEW_RETRY_ATTEMPTS:
        review_attempt += 1

        # Run the review (executing in worktree)
        logger.info(f"Running review (attempt {review_attempt}/{MAX_REVIEW_RETRY_ATTEMPTS})")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_REVIEWER,
                    f"🔍 Reviewing implementation against spec (attempt {review_attempt}/{MAX_REVIEW_RETRY_ATTEMPTS})..."
                )
            )

        review_result = run_review(spec_file, adw_id, logger, working_dir=worktree_path)

        # Check if we have blocker issues
        blocker_issues = [
            issue for issue in review_result.review_issues
            if issue.issue_severity == "blocker"
        ]

        # If no blockers or skip resolution, we're done
        if not blocker_issues or skip_resolution:
            break

        # We have blockers and need to resolve them
        resolve_blocker_issues(blocker_issues, issue_number, adw_id, worktree_path, logger)

        # If this was the last attempt, break regardless
        if review_attempt >= MAX_REVIEW_RETRY_ATTEMPTS - 1:
            break

        # Otherwise, we'll retry the review
        logger.info("Retrying review after resolving blockers")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_REVIEWER, "🔄 Retrying review after resolving blockers...")
            )

    # Post review results
    if review_result:
        # Build and post the summary comment
        summary = build_review_summary(review_result)
        if issue_number:
            make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_REVIEWER, summary))

        # Save review results to state
        state.update_phase(
            "review",
            completed=review_result.success,
            blocker_count=sum(1 for i in review_result.review_issues if i.issue_severity == "blocker"),
            tech_debt_count=sum(1 for i in review_result.review_issues if i.issue_severity == "tech_debt"),
            skippable_count=sum(1 for i in review_result.review_issues if i.issue_severity == "skippable")
        )
        state.save("adw_review")

    # Commit review results if we have an issue number
    if issue_number:
        try:
            github_repo_url = get_repo_url()
            repo_path = extract_repo_path(github_repo_url)
            issue = fetch_issue(issue_number, repo_path)

            # Get issue classification from state
            issue_command = state.get("issue_class", "/feature")

            # Create commit message
            logger.info("Creating review commit")
            commit_msg, error = create_commit(AGENT_REVIEWER, issue, issue_command, adw_id, logger, worktree_path)

            if error:
                logger.error(f"Error creating commit message: {error}")
                make_issue_comment(
                    issue_number, format_issue_message(adw_id, AGENT_REVIEWER, f"❌ Error creating commit message: {error}")
                )
                sys.exit(1)

            # Commit the review results (in worktree)
            success, error = commit_changes(commit_msg, cwd=worktree_path)

            if not success:
                logger.error(f"Error committing review: {error}")
                make_issue_comment(
                    issue_number, format_issue_message(adw_id, AGENT_REVIEWER, f"❌ Error committing review: {error}")
                )
                sys.exit(1)

            logger.info(f"Committed review: {commit_msg}")
            make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_REVIEWER, "✅ Review committed"))

            # Finalize git operations (push and PR)
            finalize_git_operations(state, logger, cwd=worktree_path)

        except Exception as e:
            logger.error(f"Error in git operations: {e}")
            make_issue_comment(issue_number, format_issue_message(adw_id, "ops", f"❌ Error in git operations: {e}"))

    logger.info("Isolated review phase completed")
    if issue_number:
        make_issue_comment(issue_number, format_issue_message(adw_id, "ops", "✅ Isolated review phase completed"))

    # Exit with appropriate code based on blockers
    if review_result:
        blocker_count = sum(1 for i in review_result.review_issues if i.issue_severity == "blocker")
        if blocker_count > 0:
            logger.error(f"Review completed with {blocker_count} unresolved blockers")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", f"❌ Review completed with {blocker_count} unresolved blockers")
                )
            sys.exit(1)


if __name__ == "__main__":
    main()
