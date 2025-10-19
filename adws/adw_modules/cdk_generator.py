"""CDK configuration generator for AI-driven software delivery.

Generates CDK configurations, constructs, and deployment scripts based on
project scoping output.
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


def generate_cdk_config_yaml(
    client_name: str,
    environment: str,
    project_requirements: Dict[str, Any],
    output_dir: str,
    logger: logging.Logger
) -> str:
    """Generate CDK configuration YAML file.

    Args:
        client_name: Client identifier (e.g., "clientA")
        environment: Environment name (dev, staging, production)
        project_requirements: Project requirements from scoping
        output_dir: Directory to write config file
        logger: Logger instance

    Returns:
        Path to generated config file
    """
    logger.info(f"Generating CDK config for {client_name} ({environment})")

    # Build resource prefix
    resource_prefix = f"{client_name}-{environment}"

    # Extract infrastructure needs from requirements
    infra_needs = project_requirements.get("infrastructure", {})

    config = {
        "project": {
            "name": client_name,
            "environment": environment,
            "resourcePrefix": resource_prefix,
            "region": infra_needs.get("region", "us-east-1")
        },
        "infrastructure": {
            "compute": _generate_compute_config(infra_needs.get("compute", {})),
            "storage": _generate_storage_config(infra_needs.get("storage", {})),
            "database": _generate_database_config(infra_needs.get("database", {})),
            "auth": _generate_auth_config(infra_needs.get("auth", {})),
            "networking": _generate_networking_config(infra_needs.get("networking", {}))
        },
        "parameters": {
            "storePrefix": f"/sdaw/{client_name}/{environment}",
            "secretsPrefix": f"sdaw/{client_name}/{environment}"
        },
        "monitoring": {
            "enableCloudWatch": True,
            "enableXRay": infra_needs.get("monitoring", {}).get("xray", False),
            "logRetentionDays": 30
        },
        "tags": {
            "Client": client_name,
            "Environment": environment,
            "ManagedBy": "SDAW",
            "CreatedAt": datetime.utcnow().isoformat()
        }
    }

    # Write config file
    os.makedirs(output_dir, exist_ok=True)
    config_path = os.path.join(output_dir, "cdk_config.yaml")

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"CDK config written to {config_path}")
    return config_path


def _generate_compute_config(compute_needs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate compute configuration section."""
    return {
        "lambda": {
            "enabled": compute_needs.get("serverless", True),
            "runtime": compute_needs.get("runtime", "python3.11"),
            "timeout": compute_needs.get("timeout", 30),
            "memorySize": compute_needs.get("memory", 512)
        },
        "ecs": {
            "enabled": compute_needs.get("containers", False),
            "fargate": True
        }
    }


def _generate_storage_config(storage_needs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate storage configuration section."""
    return {
        "s3": {
            "enabled": storage_needs.get("objectStorage", True),
            "versioning": storage_needs.get("versioning", True),
            "encryption": "AES256",
            "publicAccess": False
        },
        "cloudFront": {
            "enabled": storage_needs.get("cdn", False)
        }
    }


def _generate_database_config(db_needs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate database configuration section."""
    return {
        "dynamoDB": {
            "enabled": db_needs.get("nosql", False),
            "billingMode": "PAY_PER_REQUEST"
        },
        "rds": {
            "enabled": db_needs.get("relational", False),
            "engine": db_needs.get("engine", "postgres"),
            "instanceClass": db_needs.get("instanceClass", "db.t3.micro")
        },
        "opensearch": {
            "enabled": db_needs.get("search", False)
        }
    }


def _generate_auth_config(auth_needs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate authentication configuration section."""
    return {
        "cognito": {
            "enabled": auth_needs.get("userPool", False),
            "mfa": auth_needs.get("mfa", False),
            "passwordPolicy": {
                "minLength": 8,
                "requireUppercase": True,
                "requireNumbers": True,
                "requireSymbols": True
            }
        }
    }


def _generate_networking_config(network_needs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate networking configuration section."""
    return {
        "vpc": {
            "enabled": network_needs.get("isolatedNetwork", False),
            "cidr": network_needs.get("cidr", "10.0.0.0/16"),
            "maxAzs": network_needs.get("availabilityZones", 2)
        },
        "apiGateway": {
            "enabled": network_needs.get("api", True),
            "type": network_needs.get("apiType", "REST")
        }
    }


def generate_cdk_construct_template(
    construct_name: str,
    construct_type: str,
    output_dir: str,
    logger: logging.Logger
) -> str:
    """Generate a reusable CDK construct template.

    Args:
        construct_name: Name for the construct (e.g., "RAGSystem")
        construct_type: Type of construct (lambda, dynamodb, s3, etc.)
        output_dir: Directory to write construct file
        logger: Logger instance

    Returns:
        Path to generated construct file
    """
    logger.info(f"Generating CDK construct template: {construct_name} ({construct_type})")

    # Construct templates by type
    templates = {
        "lambda": _lambda_construct_template(construct_name),
        "dynamodb": _dynamodb_construct_template(construct_name),
        "s3": _s3_construct_template(construct_name),
        "apigateway": _apigateway_construct_template(construct_name)
    }

    template = templates.get(construct_type, _generic_construct_template(construct_name))

    # Write construct file
    os.makedirs(output_dir, exist_ok=True)
    construct_path = os.path.join(output_dir, f"{construct_name.lower()}_construct.py")

    with open(construct_path, "w") as f:
        f.write(template)

    logger.info(f"CDK construct written to {construct_path}")
    return construct_path


def _lambda_construct_template(name: str) -> str:
    """Generate Lambda construct template."""
    return f'''"""CDK construct for {name} Lambda function."""

from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    Duration,
    RemovalPolicy
)
from constructs import Construct


class {name}Construct(Construct):
    """Reusable construct for {name} Lambda function."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda function
        self.function = lambda_.Function(
            self,
            "{name}Function",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/{name.lower()}"),
            environment=environment,
            timeout=Duration.seconds(30),
            memory_size=512,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add necessary permissions
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter", "ssm:GetParameters"],
                resources=["*"]  # Scope down in production
            )
        )
'''


def _dynamodb_construct_template(name: str) -> str:
    """Generate DynamoDB construct template."""
    return f'''"""CDK construct for {name} DynamoDB table."""

from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct


class {name}Construct(Construct):
    """Reusable construct for {name} DynamoDB table."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB table
        self.table = dynamodb.Table(
            self,
            "{name}Table",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )
'''


def _s3_construct_template(name: str) -> str:
    """Generate S3 construct template."""
    return f'''"""CDK construct for {name} S3 bucket."""

from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy
)
from constructs import Construct


class {name}Construct(Construct):
    """Reusable construct for {name} S3 bucket."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket
        self.bucket = s3.Bucket(
            self,
            "{name}Bucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
'''


def _apigateway_construct_template(name: str) -> str:
    """Generate API Gateway construct template."""
    return f'''"""CDK construct for {name} API Gateway."""

from aws_cdk import (
    aws_apigateway as apigw,
    aws_lambda as lambda_
)
from constructs import Construct


class {name}Construct(Construct):
    """Reusable construct for {name} API Gateway."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        backend_function: lambda_.Function,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create API Gateway
        self.api = apigw.RestApi(
            self,
            "{name}Api",
            rest_api_name="{name} API",
            description="API for {name}",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            )
        )

        # Add Lambda integration
        integration = apigw.LambdaIntegration(backend_function)

        # Add routes
        self.api.root.add_method("ANY", integration)
'''


def _generic_construct_template(name: str) -> str:
    """Generate generic construct template."""
    return f'''"""CDK construct for {name}."""

from constructs import Construct


class {name}Construct(Construct):
    """Reusable construct for {name}."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Implement {name} construct
        pass
'''


def generate_parameter_store_script(
    parameters: Dict[str, str],
    prefix: str,
    output_dir: str,
    logger: logging.Logger
) -> str:
    """Generate script to populate Parameter Store.

    Args:
        parameters: Key-value pairs to store
        prefix: Parameter Store prefix
        output_dir: Directory to write script
        logger: Logger instance

    Returns:
        Path to generated script
    """
    logger.info(f"Generating Parameter Store setup script with prefix {prefix}")

    script = '''#!/bin/bash
# Auto-generated Parameter Store setup script

set -e

REGION="${AWS_REGION:-us-east-1}"

echo "Setting up Parameter Store parameters in $REGION..."

'''

    for key, value in parameters.items():
        param_name = f"{prefix}/{key}"
        script += f'''
aws ssm put-parameter \\
    --name "{param_name}" \\
    --value "{value}" \\
    --type String \\
    --region "$REGION" \\
    --overwrite || echo "Parameter {param_name} already exists"
'''

    script += '\necho "Parameter Store setup complete!"'

    # Write script
    os.makedirs(output_dir, exist_ok=True)
    script_path = os.path.join(output_dir, "setup_parameters.sh")

    with open(script_path, "w") as f:
        f.write(script)

    # Make executable
    os.chmod(script_path, 0o755)

    logger.info(f"Parameter Store script written to {script_path}")
    return script_path
