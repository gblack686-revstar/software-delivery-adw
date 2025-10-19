#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "boto3>=1.26.0"]
# ///

"""ADW Test Infrastructure - AI Developer Workflow for AWS infrastructure testing.

Usage:
    uv run adw_test_infra.py --adw-id <adw-id> [--issue-number <number>]

Workflow:
1. Load state and validate infrastructure configuration exists
2. Validate CDK stacks are deployed
3. Run infrastructure tests:
   - CDK stack validation
   - Resource existence checks
   - Connectivity tests
   - Security group rules
   - IAM permissions
4. Capture test results
5. Post results to issue (if provided)
6. Update state with infrastructure test results

This workflow REQUIRES that infrastructure has been deployed (via adw_deploy.py or manually).
"""

import argparse
import sys
import logging
import json
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState
from adws.adw_modules.github import make_issue_comment
from adws.adw_modules.workflow_ops import format_issue_message
from adws.adw_modules.utils import setup_logger, parse_json
from adws.adw_modules.data_types import (
    AgentTemplateRequest,
    InfrastructureTestResult,
)
from adws.adw_modules.agent import execute_template
from adws.adw_modules.aws_cdk_helper import (
    get_stack_outputs,
    get_stack_status,
)

# Agent name constants
AGENT_INFRA_TESTER = "infra_tester"

# Maximum number of test retry attempts
MAX_INFRA_TEST_RETRY_ATTEMPTS = 2


def run_infrastructure_tests(
    adw_id: str,
    cdk_app_dir: str,
    logger: logging.Logger,
) -> Tuple[bool, str]:
    """Run infrastructure tests using the /test_infra command.

    Args:
        adw_id: ADW workflow ID
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance

    Returns:
        Tuple of (success, output/error_message)
    """
    request = AgentTemplateRequest(
        agent_name=AGENT_INFRA_TESTER,
        slash_command="/test_infra",
        args=[cdk_app_dir],
        adw_id=adw_id,
        working_dir=None,
    )

    logger.debug(f"infra_test_request: {request.model_dump_json(indent=2, by_alias=True)}")
    response = execute_template(request)
    logger.debug(f"infra_test_response: {response.model_dump_json(indent=2, by_alias=True)}")

    return response.success, response.output


def validate_cdk_stacks(state: ADWState, logger: logging.Logger) -> Tuple[bool, List[str]]:
    """Validate that CDK stacks are deployed and healthy.

    Args:
        state: ADW state containing infrastructure config
        logger: Logger instance

    Returns:
        Tuple of (all_healthy, list_of_errors)
    """
    infra_config = state.get_infrastructure_config()

    if not infra_config:
        return False, ["No infrastructure configuration found in state"]

    if not infra_config.cdk_config_path:
        return False, ["No CDK config path found in infrastructure configuration"]

    # Get CDK app directory
    cdk_app_dir = Path(infra_config.cdk_output_dir)
    if not cdk_app_dir.exists():
        return False, [f"CDK output directory not found: {cdk_app_dir}"]

    errors = []
    all_healthy = True

    # Validate each stack
    stacks = state.get_cdk_stacks()
    if not stacks:
        return False, ["No CDK stacks found in state"]

    for stack in stacks:
        logger.info(f"Validating stack: {stack.stack_name}")

        # Check stack status
        status = get_stack_status(stack.stack_name, str(cdk_app_dir), logger)

        if not status:
            errors.append(f"Stack {stack.stack_name} not found")
            all_healthy = False
            continue

        if status != "deployed":
            errors.append(f"Stack {stack.stack_name} status is {status}, expected 'deployed'")
            all_healthy = False

    return all_healthy, errors


def format_infra_test_results(
    stack_validation: Tuple[bool, List[str]],
    test_results: Optional[str],
    logger: logging.Logger
) -> str:
    """Format infrastructure test results for GitHub comment.

    Args:
        stack_validation: Tuple of (success, errors) from stack validation
        test_results: Test output from infrastructure tests
        logger: Logger instance

    Returns:
        Formatted markdown string
    """
    parts = ["## 🏗️ Infrastructure Test Results\n"]

    # Stack validation section
    parts.append("### CDK Stack Validation")
    if stack_validation[0]:
        parts.append("✅ All CDK stacks are healthy and deployed")
    else:
        parts.append("❌ Stack validation failed:")
        for error in stack_validation[1]:
            parts.append(f"- {error}")

    parts.append("")

    # Infrastructure tests section
    if test_results:
        parts.append("### Infrastructure Tests")
        parts.append(test_results)
    else:
        parts.append("### Infrastructure Tests")
        parts.append("⚠️ No infrastructure test results available")

    return "\n".join(parts)


def main():
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="ADW Test Infrastructure - AWS infrastructure testing")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--issue-number", help="GitHub issue number (optional)")
    args = parser.parse_args()

    adw_id = args.adw_id
    issue_number = args.issue_number

    # Load state
    logger = setup_logger(adw_id, "adw_test_infra")
    state = ADWState.load(adw_id, logger)

    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        print(f"Error: No state found for ADW ID: {adw_id}")
        print("Run adw_planning.py first to create state")
        sys.exit(1)

    logger.info(f"ADW Test Infrastructure starting - ID: {adw_id}, Issue: {issue_number}")

    # Check if infrastructure is deployed
    if not state.get("infrastructure_deployed", False):
        logger.error("Infrastructure not marked as deployed in state")
        print("Error: Infrastructure not deployed")
        print("Run adw_deploy.py first to deploy infrastructure")
        if issue_number:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ Infrastructure not deployed. Run adw_deploy.py first.")
            )
        sys.exit(1)

    # Get infrastructure config
    infra_config = state.get_infrastructure_config()
    if not infra_config:
        logger.error("No infrastructure configuration found")
        print("Error: No infrastructure configuration found")
        sys.exit(1)

    cdk_app_dir = infra_config.cdk_output_dir
    logger.info(f"Using CDK app directory: {cdk_app_dir}")

    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"✅ Starting infrastructure testing\n🏗️ CDK App: {cdk_app_dir}"
            )
        )

    # Validate CDK stacks
    logger.info("Validating CDK stacks...")
    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_INFRA_TESTER, "🔍 Validating CDK stacks...")
        )

    stack_validation = validate_cdk_stacks(state, logger)

    if not stack_validation[0]:
        logger.error(f"Stack validation failed: {stack_validation[1]}")
        if issue_number:
            error_msg = "\n".join([f"- {e}" for e in stack_validation[1]])
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, AGENT_INFRA_TESTER, f"❌ Stack validation failed:\n{error_msg}")
            )

    # Run infrastructure tests
    logger.info("Running infrastructure tests...")
    if issue_number:
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_INFRA_TESTER, "🧪 Running infrastructure tests...")
        )

    test_success, test_output = run_infrastructure_tests(adw_id, cdk_app_dir, logger)

    if test_success:
        logger.info("Infrastructure tests passed")
    else:
        logger.error(f"Infrastructure tests failed: {test_output}")

    # Format and post results
    summary = format_infra_test_results(stack_validation, test_output, logger)

    if issue_number:
        make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_INFRA_TESTER, summary))

    # Create infrastructure test result
    test_result = InfrastructureTestResult(
        test_name="infrastructure_validation",
        passed=stack_validation[0] and test_success,
        test_output=test_output if test_output else "Stack validation completed",
        timestamp=datetime.now()
    )

    # Update state
    state.add_infrastructure_test_result(test_result)
    state.mark_infrastructure_tested(stack_validation[0] and test_success)
    state.save("adw_test_infra")

    logger.info("Infrastructure testing completed")
    if issue_number:
        if stack_validation[0] and test_success:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "✅ Infrastructure testing completed successfully!")
            )
        else:
            make_issue_comment(
                issue_number,
                format_issue_message(adw_id, "ops", "❌ Infrastructure testing completed with failures")
            )

    # Exit with appropriate code
    if not (stack_validation[0] and test_success):
        logger.error("Infrastructure tests failed")
        sys.exit(1)
    else:
        logger.info("All infrastructure tests passed")


if __name__ == "__main__":
    main()
