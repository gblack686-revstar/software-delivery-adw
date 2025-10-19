"""AWS CDK helper functions for infrastructure management.

Provides utilities for deploying, destroying, and managing CDK stacks.
"""

import subprocess
import json
import logging
from typing import Dict, Optional, Tuple, List, Any
from .data_types import CDKStackInfo, AWSResource, AWSResourceType


def run_cdk_command(
    command: List[str],
    cwd: str,
    logger: logging.Logger
) -> Tuple[bool, str]:
    """Run a CDK command and return success status and output.

    Args:
        command: List of command parts (e.g., ["cdk", "deploy", "--all"])
        cwd: Working directory for the command
        logger: Logger instance

    Returns:
        Tuple of (success, output/error_message)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd
        )

        if result.returncode == 0:
            logger.info(f"CDK command succeeded: {' '.join(command)}")
            return True, result.stdout
        else:
            logger.error(f"CDK command failed: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        logger.error(f"Error running CDK command: {e}")
        return False, str(e)


def deploy_cdk_stack(
    stack_name: str,
    cdk_app_dir: str,
    logger: logging.Logger,
    require_approval: bool = False,
    parameters: Optional[Dict[str, str]] = None
) -> Tuple[bool, Optional[CDKStackInfo]]:
    """Deploy a CDK stack.

    Args:
        stack_name: Name of the stack to deploy
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance
        require_approval: Whether to require manual approval
        parameters: Stack parameters as key-value pairs

    Returns:
        Tuple of (success, CDKStackInfo or None)
    """
    logger.info(f"Deploying CDK stack: {stack_name}")

    # Build command
    cmd = ["cdk", "deploy", stack_name, "--json"]

    if not require_approval:
        cmd.append("--require-approval=never")

    # Add parameters if provided
    if parameters:
        for key, value in parameters.items():
            cmd.extend(["--parameters", f"{stack_name}:{key}={value}"])

    success, output = run_cdk_command(cmd, cdk_app_dir, logger)

    if not success:
        return False, None

    # Parse the JSON output to get stack info
    try:
        stack_data = json.loads(output)

        # Extract stack outputs and resources
        outputs = stack_data.get("outputs", {})

        stack_info = CDKStackInfo(
            stack_name=stack_name,
            status="deployed",
            outputs=outputs,
            parameters=parameters or {}
        )

        return True, stack_info

    except json.JSONDecodeError:
        logger.warning("Could not parse CDK deploy output as JSON")
        # Return basic info even if we can't parse the output
        stack_info = CDKStackInfo(
            stack_name=stack_name,
            status="deployed",
            parameters=parameters or {}
        )
        return True, stack_info


def destroy_cdk_stack(
    stack_name: str,
    cdk_app_dir: str,
    logger: logging.Logger,
    force: bool = True
) -> bool:
    """Destroy a CDK stack.

    Args:
        stack_name: Name of the stack to destroy
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance
        force: Whether to force destruction without confirmation

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Destroying CDK stack: {stack_name}")

    cmd = ["cdk", "destroy", stack_name]

    if force:
        cmd.append("--force")

    success, output = run_cdk_command(cmd, cdk_app_dir, logger)

    return success


def get_stack_outputs(
    stack_name: str,
    cdk_app_dir: str,
    logger: logging.Logger
) -> Tuple[bool, Dict[str, str]]:
    """Get outputs from a deployed CDK stack.

    Args:
        stack_name: Name of the stack
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance

    Returns:
        Tuple of (success, outputs_dict)
    """
    logger.info(f"Getting outputs for stack: {stack_name}")

    # List stacks and find our stack
    cmd = ["cdk", "list", "--json"]
    success, output = run_cdk_command(cmd, cdk_app_dir, logger)

    if not success:
        return False, {}

    try:
        stacks = json.loads(output)

        # Find matching stack
        for stack in stacks:
            if stack.get("name") == stack_name:
                return True, stack.get("outputs", {})

        logger.warning(f"Stack {stack_name} not found in CDK app")
        return False, {}

    except json.JSONDecodeError:
        logger.error("Could not parse CDK list output")
        return False, {}


def synth_cdk_stack(
    stack_name: Optional[str],
    cdk_app_dir: str,
    logger: logging.Logger,
    output_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """Synthesize CDK stack to CloudFormation template.

    Args:
        stack_name: Name of the stack to synth (None for all stacks)
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance
        output_dir: Optional output directory for templates

    Returns:
        Tuple of (success, output_path or error_message)
    """
    logger.info(f"Synthesizing CDK stack: {stack_name or 'all stacks'}")

    cmd = ["cdk", "synth"]

    if stack_name:
        cmd.append(stack_name)

    if output_dir:
        cmd.extend(["--output", output_dir])

    success, output = run_cdk_command(cmd, cdk_app_dir, logger)

    if success:
        if output_dir:
            return True, output_dir
        else:
            return True, output
    else:
        return False, output


def validate_cdk_app(
    cdk_app_dir: str,
    logger: logging.Logger
) -> Tuple[bool, str]:
    """Validate a CDK app by attempting to synthesize it.

    Args:
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance

    Returns:
        Tuple of (is_valid, error_message)
    """
    logger.info("Validating CDK app")

    # Try to synth without actually deploying
    success, output = synth_cdk_stack(None, cdk_app_dir, logger)

    if success:
        return True, "CDK app is valid"
    else:
        return False, output


def get_stack_status(
    stack_name: str,
    cdk_app_dir: str,
    logger: logging.Logger
) -> Optional[str]:
    """Get the current status of a CDK stack.

    Args:
        stack_name: Name of the stack
        cdk_app_dir: Directory containing the CDK app
        logger: Logger instance

    Returns:
        Stack status string or None if not found
    """
    cmd = ["cdk", "list", "--json"]
    success, output = run_cdk_command(cmd, cdk_app_dir, logger)

    if not success:
        return None

    try:
        stacks = json.loads(output)

        for stack in stacks:
            if stack.get("name") == stack_name:
                return stack.get("status", "unknown")

        return None

    except json.JSONDecodeError:
        return None


def bootstrap_cdk_environment(
    account_id: str,
    region: str,
    logger: logging.Logger,
    qualifier: Optional[str] = None
) -> bool:
    """Bootstrap CDK environment for a given account and region.

    Args:
        account_id: AWS account ID
        region: AWS region
        logger: Logger instance
        qualifier: Optional qualifier for the bootstrap stack

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Bootstrapping CDK environment for {account_id} in {region}")

    cmd = [
        "cdk", "bootstrap",
        f"aws://{account_id}/{region}"
    ]

    if qualifier:
        cmd.extend(["--qualifier", qualifier])

    # Run without cwd since this is account-level
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("CDK bootstrap successful")
            return True
        else:
            logger.error(f"CDK bootstrap failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error bootstrapping CDK: {e}")
        return False
