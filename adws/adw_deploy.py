#!/usr/bin/env python3
"""
ADW Deploy - AWS CDK Infrastructure Deployment

Deploys AWS infrastructure using CDK configurations generated during scoping phase.
Supports environment-specific deployments with automatic validation and rollback.

Usage:
    uv run adws/adw_deploy.py --adw-id <adw-id> [--environment dev|staging|production] [--issue-number <number>]

Features:
    - Deploy CDK stacks with environment-specific configuration
    - Automatic pre-deployment validation
    - Post-deployment health checks
    - Rollback on failure
    - GitHub issue integration
    - State tracking with deployment history
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState
from adws.adw_modules.data_types import (
    InfrastructureConfig,
    CDKStackInfo,
    AWSResource,
)
from adws.adw_modules.aws_cdk_helper import (
    deploy_cdk_stack,
    destroy_cdk_stack,
    validate_cdk_app,
    get_stack_outputs,
)
from adws.adw_modules.utils import setup_logger
from adws.adw_modules.github import post_github_comment

# Configuration
AGENT_DEPLOYER = "deployer"
SUPPORTED_ENVIRONMENTS = ["dev", "staging", "production"]


def validate_cdk_configuration(adw_id: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """
    Validate CDK configuration exists and is valid.

    Args:
        adw_id: Workflow ID
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    logger.info("Validating CDK configuration...")

    specs_dir = Path("specs") / adw_id
    cdk_config_dir = specs_dir / "cdk_config"

    # Check if CDK config directory exists
    if not cdk_config_dir.exists():
        return False, f"CDK configuration not found at {cdk_config_dir}. Run /scope first."

    # Check for cdk_config.yaml
    cdk_config_file = cdk_config_dir / "cdk_config.yaml"
    if not cdk_config_file.exists():
        return False, f"CDK configuration file not found: {cdk_config_file}"

    # Check for setup script
    setup_script = cdk_config_dir / "setup_parameters.sh"
    if not setup_script.exists():
        logger.warning(f"Parameter setup script not found: {setup_script}")

    logger.info("✅ CDK configuration validated")
    return True, None


def setup_parameter_store(adw_id: str, environment: str, logger: logging.Logger) -> bool:
    """
    Set up AWS Parameter Store with configuration values.

    Args:
        adw_id: Workflow ID
        environment: Target environment
        logger: Logger instance

    Returns:
        True if successful
    """
    logger.info(f"Setting up Parameter Store for {environment}...")

    specs_dir = Path("specs") / adw_id
    setup_script = specs_dir / "cdk_config" / "setup_parameters.sh"

    if not setup_script.exists():
        logger.warning("No parameter setup script found, skipping Parameter Store setup")
        return True

    # Execute the setup script
    import subprocess

    try:
        result = subprocess.run(
            ["bash", str(setup_script), environment],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("✅ Parameter Store configured")
        if result.stdout:
            logger.debug(f"Setup output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to setup Parameter Store: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Error running setup script: {e}")
        return False


def deploy_infrastructure(
    adw_id: str,
    environment: str,
    logger: logging.Logger,
    require_approval: bool = False,
) -> Tuple[bool, List[CDKStackInfo]]:
    """
    Deploy AWS infrastructure using CDK.

    Args:
        adw_id: Workflow ID
        environment: Target environment
        logger: Logger instance
        require_approval: Whether to require manual approval

    Returns:
        Tuple of (success, list of deployed stacks)
    """
    logger.info(f"Deploying infrastructure to {environment}...")

    specs_dir = Path("specs") / adw_id
    cdk_app_dir = specs_dir / "cdk_config"

    # Validate CDK app before deployment
    valid, error = validate_cdk_app(str(cdk_app_dir), logger)
    if not valid:
        logger.error(f"❌ CDK app validation failed: {error}")
        return False, []

    # Load CDK configuration to get stack names
    import yaml

    cdk_config_file = cdk_app_dir / "cdk_config.yaml"
    with open(cdk_config_file, "r") as f:
        cdk_config = yaml.safe_load(f)

    # Get stack name from config
    stack_name = cdk_config.get("stack_name", f"{adw_id}-{environment}-stack")

    # Deploy the stack
    logger.info(f"Deploying stack: {stack_name}")

    parameters = {
        "Environment": environment,
        "ADWId": adw_id,
    }

    success, stack_info = deploy_cdk_stack(
        stack_name=stack_name,
        cdk_app_dir=str(cdk_app_dir),
        logger=logger,
        require_approval=require_approval,
        parameters=parameters,
    )

    if not success:
        logger.error(f"❌ Failed to deploy stack: {stack_name}")
        return False, []

    logger.info(f"✅ Stack deployed successfully: {stack_name}")

    # Get stack outputs
    outputs = get_stack_outputs(stack_name, logger)
    if outputs and stack_info:
        stack_info.outputs = outputs
        logger.info(f"Stack outputs: {outputs}")

    return True, [stack_info] if stack_info else []


def run_post_deployment_checks(
    adw_id: str,
    stacks: List[CDKStackInfo],
    logger: logging.Logger,
) -> Tuple[bool, str]:
    """
    Run post-deployment health checks.

    Args:
        adw_id: Workflow ID
        stacks: List of deployed stacks
        logger: Logger instance

    Returns:
        Tuple of (success, results_message)
    """
    logger.info("Running post-deployment health checks...")

    if not stacks:
        return False, "No stacks to validate"

    all_healthy = True
    results = []

    for stack in stacks:
        logger.info(f"Checking stack: {stack.stack_name}")

        # Check stack status
        if stack.status != "deployed":
            all_healthy = False
            results.append(f"❌ {stack.stack_name}: {stack.status}")
            continue

        # Check resources
        if not stack.resources:
            logger.warning(f"No resources found in stack {stack.stack_name}")

        results.append(f"✅ {stack.stack_name}: Deployed successfully")

        # Log outputs
        if stack.outputs:
            results.append(f"   Outputs: {len(stack.outputs)} values")

    results_message = "\n".join(results)

    if all_healthy:
        logger.info("✅ All health checks passed")
    else:
        logger.error("❌ Some health checks failed")

    return all_healthy, results_message


def rollback_deployment(
    adw_id: str,
    stacks: List[CDKStackInfo],
    logger: logging.Logger,
) -> bool:
    """
    Rollback failed deployment by destroying stacks.

    Args:
        adw_id: Workflow ID
        stacks: List of stacks to destroy
        logger: Logger instance

    Returns:
        True if rollback successful
    """
    logger.warning("Rolling back deployment...")

    specs_dir = Path("specs") / adw_id
    cdk_app_dir = specs_dir / "cdk_config"

    rollback_success = True

    for stack in stacks:
        logger.info(f"Destroying stack: {stack.stack_name}")

        success = destroy_cdk_stack(
            stack_name=stack.stack_name,
            cdk_app_dir=str(cdk_app_dir),
            logger=logger,
            force=True,
        )

        if not success:
            logger.error(f"❌ Failed to destroy stack: {stack.stack_name}")
            rollback_success = False
        else:
            logger.info(f"✅ Stack destroyed: {stack.stack_name}")

    return rollback_success


def update_deployment_state(
    state: ADWState,
    stacks: List[CDKStackInfo],
    environment: str,
    success: bool,
    logger: logging.Logger,
) -> None:
    """
    Update state with deployment information.

    Args:
        state: ADW state instance
        stacks: List of deployed stacks
        environment: Target environment
        success: Whether deployment was successful
        logger: Logger instance
    """
    logger.info("Updating deployment state...")

    # Get or create infrastructure config
    infra_config = state.get("infrastructure_config")
    if not infra_config:
        infra_config = InfrastructureConfig(
            environment=environment,
            resource_prefix=state.adw_id,
            stacks=[],
        )
    else:
        # Convert dict to InfrastructureConfig if needed
        if isinstance(infra_config, dict):
            infra_config = InfrastructureConfig(**infra_config)

    # Update environment
    infra_config.environment = environment

    # Update or add stacks
    for stack in stacks:
        existing_stack = next(
            (s for s in infra_config.stacks if s.stack_name == stack.stack_name),
            None,
        )

        if existing_stack:
            # Update existing stack
            existing_stack.status = stack.status
            existing_stack.resources = stack.resources
            existing_stack.outputs = stack.outputs
        else:
            # Add new stack
            infra_config.stacks.append(stack)

    # Update state
    state.update_infrastructure_config(infra_config)
    state.mark_infrastructure_deployed(success)

    # Add deployment phase data
    deployment_data = state.get("deployment", {})
    deployment_data.update({
        "started": True,
        "completed": success,
        "environment": environment,
        "stacks_count": len(stacks),
        "last_deployment": {
            "environment": environment,
            "success": success,
            "stacks": [s.stack_name for s in stacks],
        }
    })
    state.update("deployment", deployment_data)

    state.save()
    logger.info("✅ Deployment state updated")


def post_deployment_summary(
    issue_number: Optional[str],
    adw_id: str,
    environment: str,
    stacks: List[CDKStackInfo],
    success: bool,
    health_check_results: str,
    logger: logging.Logger,
) -> None:
    """
    Post deployment summary to GitHub issue.

    Args:
        issue_number: GitHub issue number
        adw_id: Workflow ID
        environment: Target environment
        stacks: List of deployed stacks
        success: Whether deployment was successful
        health_check_results: Health check results
        logger: Logger instance
    """
    if not issue_number:
        return

    logger.info(f"Posting deployment summary to issue #{issue_number}")

    status_emoji = "✅" if success else "❌"
    status_text = "Successful" if success else "Failed"

    # Build stack summary
    stack_summary = []
    for stack in stacks:
        stack_summary.append(f"- **{stack.stack_name}**: {stack.status}")
        if stack.outputs:
            for key, value in stack.outputs.items():
                stack_summary.append(f"  - {key}: `{value}`")

    comment = f"""## {status_emoji} Deployment {status_text}

**ADW ID:** {adw_id}
**Environment:** {environment}

### Deployed Stacks
{chr(10).join(stack_summary) if stack_summary else "No stacks deployed"}

### Health Checks
```
{health_check_results}
```

### Next Steps
{"- Infrastructure is ready for testing" if success else "- Review deployment errors and retry"}
{"- Run `/test_infra` to validate infrastructure" if success else "- Check CloudFormation console for details"}
"""

    post_github_comment(issue_number, comment, logger)


def main():
    """Main deployment workflow."""
    parser = argparse.ArgumentParser(description="Deploy AWS infrastructure using CDK")
    parser.add_argument("--adw-id", required=True, help="ADW workflow ID")
    parser.add_argument(
        "--environment",
        choices=SUPPORTED_ENVIRONMENTS,
        default="dev",
        help="Target environment (default: dev)",
    )
    parser.add_argument("--issue-number", help="GitHub issue number")
    parser.add_argument(
        "--require-approval",
        action="store_true",
        help="Require manual approval before deployment",
    )
    parser.add_argument(
        "--skip-parameter-setup",
        action="store_true",
        help="Skip Parameter Store setup",
    )
    parser.add_argument(
        "--no-rollback",
        action="store_true",
        help="Skip automatic rollback on failure",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("adw_deploy", level=logging.INFO)

    logger.info("=" * 60)
    logger.info("🚀 Starting Deployment Phase")
    logger.info("=" * 60)
    logger.info(f"📋 ADW ID: {args.adw_id}")
    logger.info(f"🌍 Environment: {args.environment}")
    if args.issue_number:
        logger.info(f"🔗 GitHub Issue: #{args.issue_number}")
    logger.info("")

    # Initialize state
    state = ADWState(adw_id=args.adw_id, logger=logger)

    # Check if scoping is complete
    scoping = state.get("scoping", {})
    if not scoping.get("completed"):
        logger.warning("⚠️ Warning: Scoping phase not complete")

    # Validate CDK configuration
    valid, error = validate_cdk_configuration(args.adw_id, logger)
    if not valid:
        logger.error(f"❌ {error}")
        sys.exit(1)

    # Setup Parameter Store
    if not args.skip_parameter_setup:
        param_success = setup_parameter_store(args.adw_id, args.environment, logger)
        if not param_success:
            logger.error("❌ Parameter Store setup failed")
            sys.exit(1)
    else:
        logger.info("⏭️ Skipping Parameter Store setup")

    # Deploy infrastructure
    deploy_success, stacks = deploy_infrastructure(
        adw_id=args.adw_id,
        environment=args.environment,
        logger=logger,
        require_approval=args.require_approval,
    )

    if not deploy_success:
        logger.error("❌ Deployment failed")

        # Rollback if enabled
        if not args.no_rollback and stacks:
            rollback_success = rollback_deployment(args.adw_id, stacks, logger)
            if rollback_success:
                logger.info("✅ Rollback completed")
            else:
                logger.error("❌ Rollback failed - manual cleanup required")

        # Update state
        update_deployment_state(
            state=state,
            stacks=stacks,
            environment=args.environment,
            success=False,
            logger=logger,
        )

        # Post to GitHub
        post_deployment_summary(
            issue_number=args.issue_number,
            adw_id=args.adw_id,
            environment=args.environment,
            stacks=stacks,
            success=False,
            health_check_results="Deployment failed",
            logger=logger,
        )

        sys.exit(1)

    # Run post-deployment health checks
    health_success, health_results = run_post_deployment_checks(
        adw_id=args.adw_id,
        stacks=stacks,
        logger=logger,
    )

    if not health_success:
        logger.error("❌ Health checks failed")

        # Rollback if enabled
        if not args.no_rollback:
            rollback_success = rollback_deployment(args.adw_id, stacks, logger)
            if rollback_success:
                logger.info("✅ Rollback completed")
            else:
                logger.error("❌ Rollback failed - manual cleanup required")

        # Update state
        update_deployment_state(
            state=state,
            stacks=stacks,
            environment=args.environment,
            success=False,
            logger=logger,
        )

        # Post to GitHub
        post_deployment_summary(
            issue_number=args.issue_number,
            adw_id=args.adw_id,
            environment=args.environment,
            stacks=stacks,
            success=False,
            health_check_results=health_results,
            logger=logger,
        )

        sys.exit(1)

    # Update state with successful deployment
    update_deployment_state(
        state=state,
        stacks=stacks,
        environment=args.environment,
        success=True,
        logger=logger,
    )

    # Post summary to GitHub
    post_deployment_summary(
        issue_number=args.issue_number,
        adw_id=args.adw_id,
        environment=args.environment,
        stacks=stacks,
        success=True,
        health_check_results=health_results,
        logger=logger,
    )

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ Deployment Complete!")
    logger.info("=" * 60)
    logger.info(f"Environment: {args.environment}")
    logger.info(f"Stacks deployed: {len(stacks)}")
    logger.info("")
    logger.info("🎯 Next steps:")
    logger.info(f"   uv run adws/adw_test_infra.py --adw-id {args.adw_id}")
    if args.issue_number:
        logger.info(f"   # View deployment details in issue #{args.issue_number}")
    logger.info("")


if __name__ == "__main__":
    main()
