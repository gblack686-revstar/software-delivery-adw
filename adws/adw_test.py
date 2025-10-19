#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""ADW Test - AI Developer Workflow for agentic testing in isolated worktrees.

Usage:
    uv run adw_test.py --adw-id <adw-id> [--issue-number <number>] [--skip-e2e]

Workflow:
1. Load state and validate worktree exists
2. Run application test suite in worktree with automatic resolution (4 attempts for unit, 2 for E2E)
3. Report results to issue (if issue number provided)
4. Create commit with test results in worktree
5. Push and update PR

This workflow REQUIRES that adw_planning.py has been run first to create the worktree.
"""

import argparse
import json
import sys
import logging
from typing import Tuple, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    TestResult,
    E2ETestResult,
)
from adws.adw_modules.agent import execute_template
from adws.adw_modules.github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    get_repo_url,
)
from adws.adw_modules.utils import setup_logger, parse_json
from adws.adw_modules.state import ADWState
from adws.adw_modules.git_ops import commit_changes, finalize_git_operations
from adws.adw_modules.workflow_ops import (
    format_issue_message,
    create_commit,
    classify_issue,
)
from adws.adw_modules.worktree_ops import validate_worktree

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"

# Maximum number of test retry attempts after resolution
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_E2E_TEST_RETRY_ATTEMPTS = 2


def run_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None) -> AgentPromptResponse:
    """Run the test suite using the /test command."""
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}")
    test_response = execute_template(test_template_request)
    logger.debug(f"test_response: {test_response.model_dump_json(indent=2, by_alias=True)}")

    return test_response


def parse_test_results(output: str, logger: logging.Logger) -> Tuple[List[TestResult], int, int]:
    """Parse test results JSON and return (results, passed_count, failed_count)."""
    try:
        results = parse_json(output, List[TestResult])
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count
        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        return [], 0, 0


def format_test_results_comment(results: List[TestResult], passed_count: int, failed_count: int) -> str:
    """Format test results for GitHub issue comment with JSON blocks."""
    if not results:
        return "❌ No test results found"

    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    comment_parts = []

    # Failed tests section
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests section
    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Summary
    comment_parts.append("## Summary")
    comment_parts.append(f"- **Passed**: {passed_count}")
    comment_parts.append(f"- **Failed**: {failed_count}")
    comment_parts.append(f"- **Total**: {len(results)}")

    return "\n".join(comment_parts)


def run_e2e_tests(adw_id: str, logger: logging.Logger, working_dir: Optional[str] = None) -> AgentPromptResponse:
    """Run the E2E test suite using the /test_e2e command.

    Note: The test_e2e command will automatically detect and use ports from .ports.env
    in the working directory if it exists.
    """
    test_template_request = AgentTemplateRequest(
        agent_name=AGENT_E2E_TESTER,
        slash_command="/test_e2e",
        args=[],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"e2e_test_template_request: {test_template_request.model_dump_json(indent=2, by_alias=True)}")
    test_response = execute_template(test_template_request)
    logger.debug(f"e2e_test_response: {test_response.model_dump_json(indent=2, by_alias=True)}")

    return test_response


def parse_e2e_test_results(output: str, logger: logging.Logger) -> Tuple[List[E2ETestResult], int, int]:
    """Parse E2E test results JSON and return (results, passed_count, failed_count)."""
    try:
        results = parse_json(output, List[E2ETestResult])
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count
        return results, passed_count, failed_count
    except Exception as e:
        logger.error(f"Error parsing E2E test results: {e}")
        return [], 0, 0


def resolve_failed_tests(
    failed_tests: List[TestResult],
    adw_id: str,
    issue_number: Optional[str],
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """Attempt to resolve failed tests using the resolve_failed_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(f"\n=== Resolving failed test {idx + 1}/{len(failed_tests)}: {test.test_name} ===")

        test_payload = test.model_dump_json(indent=2)
        agent_name = f"test_resolver_iter{iteration}_{idx}"

        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"🔧 Attempting to resolve: {test.test_name}\n```json\n{test_payload}\n```",
                ),
            )

        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, agent_name, f"✅ Successfully resolved: {test.test_name}"),
                )
            logger.info(f"Successfully resolved: {test.test_name}")
        else:
            unresolved_count += 1
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, agent_name, f"❌ Failed to resolve: {test.test_name}"),
                )
            logger.error(f"Failed to resolve: {test.test_name}")

    return resolved_count, unresolved_count


def run_tests_with_resolution(
    adw_id: str,
    issue_number: Optional[str],
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[TestResult], int, int, AgentPromptResponse]:
    """Run tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count, last_test_response).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0
    test_response = None

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Test Run Attempt {attempt}/{max_attempts} ===")

        test_response = run_tests(adw_id, logger, worktree_path)

        if not test_response.success:
            logger.error(f"Error running tests: {test_response.output}")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, AGENT_TESTER, f"❌ Error running tests: {test_response.output}"),
                )
            break

        results, passed_count, failed_count = parse_test_results(test_response.output, logger)

        if failed_count == 0:
            logger.info("All tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(f"Reached maximum retry attempts ({max_attempts}), stopping")
            break

        logger.info("\n=== Attempting to resolve failed tests ===")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"🔧 Found {failed_count} failed tests. Attempting resolution..."),
            )

        failed_tests = [test for test in results if not test.passed]
        resolved, unresolved = resolve_failed_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        if resolved > 0:
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", f"✅ Resolved {resolved}/{failed_count} failed tests"),
                )
            logger.info(f"\n=== Re-running tests after resolving {resolved} tests ===")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id, AGENT_TESTER, f"🔄 Re-running tests (attempt {attempt + 1}/{max_attempts})..."
                    ),
                )
        else:
            logger.info("No tests were resolved, stopping retry attempts")
            break

    if attempt == max_attempts and failed_count > 0:
        logger.warning(f"Reached maximum retry attempts ({max_attempts}) with {failed_count} failures remaining")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"⚠️ Reached maximum retry attempts ({max_attempts}) with {failed_count} failures"
                ),
            )

    return results, passed_count, failed_count, test_response


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: Optional[str],
    logger: logging.Logger,
    worktree_path: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """Attempt to resolve failed E2E tests using the resolve_failed_e2e_test command.
    Returns (resolved_count, unresolved_count).
    """
    resolved_count = 0
    unresolved_count = 0

    for idx, test in enumerate(failed_tests):
        logger.info(f"\n=== Resolving failed E2E test {idx + 1}/{len(failed_tests)}: {test.test_name} ===")

        test_payload = test.model_dump_json(indent=2)
        agent_name = f"e2e_test_resolver_iter{iteration}_{idx}"

        resolve_request = AgentTemplateRequest(
            agent_name=agent_name,
            slash_command="/resolve_failed_e2e_test",
            args=[test_payload],
            adw_id=adw_id,
            working_dir=worktree_path,
        )

        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, agent_name, f"🔧 Attempting to resolve E2E test: {test.test_name}\n```json\n{test_payload}\n```"
                ),
            )

        response = execute_template(resolve_request)

        if response.success:
            resolved_count += 1
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, agent_name, f"✅ Successfully resolved E2E test: {test.test_name}"),
                )
            logger.info(f"Successfully resolved E2E test: {test.test_name}")
        else:
            unresolved_count += 1
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, agent_name, f"❌ Failed to resolve E2E test: {test.test_name}"),
                )
            logger.error(f"Failed to resolve E2E test: {test.test_name}")

    return resolved_count, unresolved_count


def run_e2e_tests_with_resolution(
    adw_id: str,
    issue_number: Optional[str],
    logger: logging.Logger,
    worktree_path: str,
    max_attempts: int = MAX_E2E_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[E2ETestResult], int, int]:
    """Run E2E tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== E2E Test Run Attempt {attempt}/{max_attempts} ===")

        e2e_response = run_e2e_tests(adw_id, logger, worktree_path)

        if not e2e_response.success:
            logger.error(f"Error running E2E tests: {e2e_response.output}")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, AGENT_E2E_TESTER, f"❌ Error running E2E tests: {e2e_response.output}"),
                )
            break

        results, passed_count, failed_count = parse_e2e_test_results(e2e_response.output, logger)

        if not results:
            logger.warning("No E2E test results to process")
            break

        if failed_count == 0:
            logger.info("All E2E tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(f"Reached maximum E2E retry attempts ({max_attempts}), stopping")
            break

        logger.info("\n=== Attempting to resolve failed E2E tests ===")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"🔧 Found {failed_count} failed E2E tests. Attempting resolution..."),
            )

        failed_tests = [test for test in results if not test.passed]
        resolved, unresolved = resolve_failed_e2e_tests(
            failed_tests, adw_id, issue_number, logger, worktree_path, iteration=attempt
        )

        if resolved > 0:
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(adw_id, "ops", f"✅ Resolved {resolved}/{failed_count} failed E2E tests"),
                )
            logger.info(f"\n=== Re-running E2E tests after resolving {resolved} tests ===")
            if issue_number:
                make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id, AGENT_E2E_TESTER, f"🔄 Re-running E2E tests (attempt {attempt + 1}/{max_attempts})..."
                    ),
                )
        else:
            logger.info("No E2E tests were resolved, stopping retry attempts")
            break

    if attempt == max_attempts and failed_count > 0:
        logger.warning(f"Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures remaining")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"⚠️ Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures"
                ),
            )

    return results, passed_count, failed_count


def post_comprehensive_test_summary(
    issue_number: Optional[str],
    adw_id: str,
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger,
):
    """Post a comprehensive test summary including both unit and E2E tests."""
    if not issue_number:
        return

    summary = "# 🧪 Comprehensive Test Results\n\n"

    # Unit test section
    if results:
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        summary += "## Unit Tests\n\n"
        summary += f"- **Total**: {len(results)}\n"
        summary += f"- **Passed**: {passed_count} ✅\n"
        summary += f"- **Failed**: {failed_count} ❌\n\n"

        failed_tests = [test for test in results if not test.passed]
        if failed_tests:
            summary += "### Failed Unit Tests:\n"
            for test in failed_tests:
                summary += f"- ❌ {test.test_name}\n"
            summary += "\n"

    # E2E test section
    if e2e_results:
        e2e_passed_count = sum(1 for test in e2e_results if test.passed)
        e2e_failed_count = len(e2e_results) - e2e_passed_count

        summary += "## E2E Tests\n\n"
        summary += f"- **Total**: {len(e2e_results)}\n"
        summary += f"- **Passed**: {e2e_passed_count} ✅\n"
        summary += f"- **Failed**: {e2e_failed_count} ❌\n\n"

        e2e_failed_tests = [test for test in e2e_results if not test.passed]
        if e2e_failed_tests:
            summary += "### Failed E2E Tests:\n"
            for result in e2e_failed_tests:
                summary += f"- ❌ {result.test_name}\n"
                if result.screenshots:
                    summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    failed_count = sum(1 for test in results if not test.passed) if results else 0
    e2e_failed_count = sum(1 for test in e2e_results if not test.passed) if e2e_results else 0
    total_failures = failed_count + e2e_failed_count

    if total_failures > 0:
        summary += f"\n### ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        total_tests = len(results) + len(e2e_results)
        summary += f"\n### ✅ Overall Status: PASSED\n"
        summary += f"All {total_tests} tests passed successfully!\n"

    make_issue_comment(issue_number, format_issue_message(adw_id, "test_summary", summary))
    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def main():
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="ADW Test - Automated testing workflow")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--issue-number", help="GitHub issue number (optional)")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    args = parser.parse_args()

    adw_id = args.adw_id
    issue_number = args.issue_number
    skip_e2e = args.skip_e2e

    # Load state
    logger = setup_logger(adw_id, "adw_test")
    state = ADWState.load(adw_id, logger)

    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        print(f"Error: No state found for ADW ID: {adw_id}")
        print("Run adw_planning.py first to create the worktree and state")
        sys.exit(1)

    logger.info(f"ADW Test starting - ID: {adw_id}, Issue: {issue_number}, Skip E2E: {skip_e2e}")

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        print(f"Error: Worktree validation failed: {error}")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\nRun adw_planning.py first"),
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
                f"✅ Starting isolated testing phase\n"
                f"🏠 Worktree: {worktree_path}\n"
                f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                f"🧪 E2E Tests: {'Skipped' if skip_e2e else 'Enabled'}",
            ),
        )

    # Run unit tests with resolution
    logger.info("Running unit tests in worktree with automatic resolution")
    if issue_number:
        make_issue_comment(
            issue_number, format_issue_message(adw_id, AGENT_TESTER, "🧪 Running unit tests in isolated environment...")
        )

    results, passed_count, failed_count, test_response = run_tests_with_resolution(adw_id, issue_number, logger, worktree_path)

    if results:
        comment = format_test_results_comment(results, passed_count, failed_count)
        if issue_number:
            make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_TESTER, comment))
        logger.info(f"Test results: {passed_count} passed, {failed_count} failed")
    else:
        logger.warning("No test results found in output")
        if issue_number:
            make_issue_comment(
                issue_number, format_issue_message(adw_id, AGENT_TESTER, "⚠️ No test results found in output")
            )

    # Run E2E tests if not skipped
    e2e_results = []
    e2e_passed = 0
    e2e_failed = 0
    if not skip_e2e:
        logger.info("Running E2E tests in worktree with automatic resolution")
        if issue_number:
            make_issue_comment(
                issue_number, format_issue_message(adw_id, AGENT_E2E_TESTER, "🌐 Running E2E tests in isolated environment...")
            )

        e2e_results, e2e_passed, e2e_failed = run_e2e_tests_with_resolution(adw_id, issue_number, logger, worktree_path)

        if e2e_results:
            logger.info(f"E2E test results: {e2e_passed} passed, {e2e_failed} failed")

    # Post comprehensive summary
    post_comprehensive_test_summary(issue_number, adw_id, results, e2e_results, logger)

    # Check total failures
    total_failures = failed_count + (e2e_failed if not skip_e2e and e2e_results else 0)
    if total_failures > 0:
        logger.warning(f"Tests completed with {total_failures} failures - continuing to commit results")

    # Commit test results
    if issue_number:
        try:
            github_repo_url = get_repo_url()
            repo_path = extract_repo_path(github_repo_url)
            issue = fetch_issue(issue_number, repo_path)

            # Get or create issue classification
            issue_command = state.get("issue_class")
            if not issue_command:
                logger.info("No issue classification in state, running classify_issue")
                issue_command, error = classify_issue(issue, adw_id, logger)
                if error:
                    logger.error(f"Error classifying issue: {error}")
                    issue_command = "/feature"
                else:
                    state.update(issue_class=issue_command)
                    state.save("adw_test")

            # Create commit
            logger.info("Creating test commit")
            commit_msg, error = create_commit(AGENT_TESTER, issue, issue_command, adw_id, logger, worktree_path)

            if error:
                logger.error(f"Error creating commit message: {error}")
                if issue_number:
                    make_issue_comment(
                        issue_number, format_issue_message(adw_id, AGENT_TESTER, f"❌ Error creating commit message: {error}")
                    )
                sys.exit(1)

            # Commit changes
            success, error = commit_changes(commit_msg, cwd=worktree_path)

            if not success:
                logger.error(f"Error committing test results: {error}")
                make_issue_comment(
                    issue_number, format_issue_message(adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}")
                )
                sys.exit(1)

            logger.info(f"Committed test results: {commit_msg}")
            make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_TESTER, "✅ Test results committed"))

            # Finalize git operations
            finalize_git_operations(state, logger, cwd=worktree_path)

        except Exception as e:
            logger.error(f"Error in git operations: {e}")
            if issue_number:
                make_issue_comment(issue_number, format_issue_message(adw_id, "ops", f"❌ Error in git operations: {e}"))

    # Update state
    state.update_phase("test", completed=(total_failures == 0), failed_count=total_failures)
    state.save("adw_test")

    logger.info("Isolated testing phase completed")
    if issue_number:
        make_issue_comment(issue_number, format_issue_message(adw_id, "ops", "✅ Isolated testing phase completed"))

    # Exit with appropriate code
    if total_failures > 0:
        logger.error(f"Test workflow completed with {total_failures} failures")
        if issue_number:
            make_issue_comment(
                issue_number, format_issue_message(adw_id, "ops", f"❌ Test workflow completed with {total_failures} failures")
            )
        sys.exit(1)
    else:
        logger.info("All tests passed successfully")
        if issue_number:
            make_issue_comment(issue_number, format_issue_message(adw_id, "ops", "✅ All tests passed successfully!"))


if __name__ == "__main__":
    main()
