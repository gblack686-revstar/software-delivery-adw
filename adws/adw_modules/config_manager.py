"""
Configuration Manager - Unified Configuration Management

Manages configuration across local development (worktrees) and AWS (Parameter Store).
Provides validation, templating, and syncing capabilities.

Key Features:
    - Local .env file management
    - AWS Parameter Store integration
    - Configuration validation with schemas
    - Environment templates generation
    - Config syncing between local and cloud
    - Worktree-specific configuration
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import yaml


class ConfigManager:
    """
    Manages configuration for ADW workflows across local and cloud environments.

    Handles three configuration layers:
    1. Worktree configuration (.ports.env, .env.local)
    2. Project configuration (specs/<adw-id>/config/)
    3. Cloud configuration (AWS Parameter Store)
    """

    def __init__(
        self,
        adw_id: str,
        environment: str = "dev",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize configuration manager.

        Args:
            adw_id: Workflow ID
            environment: Environment name (dev, staging, production)
            logger: Logger instance
        """
        self.adw_id = adw_id
        self.environment = environment
        self.logger = logger or logging.getLogger(__name__)

        # Paths
        self.specs_dir = Path("specs") / adw_id
        self.config_dir = self.specs_dir / "config"
        self.worktree_dir = Path("trees") / adw_id

        # Configuration storage
        self._config: Dict[str, Any] = {}
        self._schema: Optional[Dict[str, Any]] = None

    def load_worktree_config(self) -> Dict[str, str]:
        """
        Load configuration from worktree .ports.env and .env.local files.

        Returns:
            Dictionary of configuration values
        """
        self.logger.info("Loading worktree configuration...")

        config = {}

        # Load .ports.env
        ports_env_file = self.worktree_dir / ".ports.env"
        if ports_env_file.exists():
            config.update(self._load_env_file(ports_env_file))
            self.logger.debug(f"Loaded .ports.env: {ports_env_file}")

        # Load .env.local
        env_local_file = self.worktree_dir / ".env.local"
        if env_local_file.exists():
            config.update(self._load_env_file(env_local_file))
            self.logger.debug(f"Loaded .env.local: {env_local_file}")

        self._config.update(config)
        return config

    def load_project_config(self) -> Dict[str, Any]:
        """
        Load project configuration from specs/<adw-id>/config/.

        Returns:
            Dictionary of configuration values
        """
        self.logger.info("Loading project configuration...")

        config = {}

        # Load config.yaml if exists
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, "r") as f:
                project_config = yaml.safe_load(f)
                if project_config:
                    config.update(project_config)
                    self.logger.debug(f"Loaded config.yaml: {config_file}")

        # Load environment-specific config
        env_config_file = self.config_dir / f"config.{self.environment}.yaml"
        if env_config_file.exists():
            with open(env_config_file, "r") as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    config.update(env_config)
                    self.logger.debug(f"Loaded {self.environment} config: {env_config_file}")

        self._config.update(config)
        return config

    def load_aws_config(self, parameter_prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Load configuration from AWS Parameter Store.

        Args:
            parameter_prefix: Parameter Store prefix (default: /sdaw/{adw_id}/{environment})

        Returns:
            Dictionary of parameter values
        """
        self.logger.info("Loading AWS Parameter Store configuration...")

        if parameter_prefix is None:
            parameter_prefix = f"/sdaw/{self.adw_id}/{self.environment}"

        try:
            import boto3

            ssm = boto3.client("ssm")

            # Get all parameters with prefix
            response = ssm.get_parameters_by_path(
                Path=parameter_prefix,
                Recursive=True,
                WithDecryption=True,
            )

            config = {}
            for param in response.get("Parameters", []):
                # Extract key from parameter name (remove prefix)
                key = param["Name"].replace(f"{parameter_prefix}/", "").replace("/", "_")
                config[key] = param["Value"]

            self.logger.info(f"Loaded {len(config)} parameters from Parameter Store")
            self._config.update(config)
            return config

        except Exception as e:
            self.logger.warning(f"Failed to load AWS config: {e}")
            return {}

    def save_to_parameter_store(
        self,
        config: Dict[str, str],
        parameter_prefix: Optional[str] = None,
        overwrite: bool = True,
    ) -> Tuple[bool, List[str]]:
        """
        Save configuration to AWS Parameter Store.

        Args:
            config: Configuration dictionary to save
            parameter_prefix: Parameter Store prefix
            overwrite: Whether to overwrite existing parameters

        Returns:
            Tuple of (success, list of saved parameter names)
        """
        self.logger.info("Saving configuration to Parameter Store...")

        if parameter_prefix is None:
            parameter_prefix = f"/sdaw/{self.adw_id}/{self.environment}"

        try:
            import boto3

            ssm = boto3.client("ssm")

            saved_params = []

            for key, value in config.items():
                # Convert key to parameter path (replace _ with /)
                param_name = f"{parameter_prefix}/{key.replace('_', '/')}"

                # Determine parameter type based on key
                param_type = "SecureString" if "secret" in key.lower() or "password" in key.lower() or "key" in key.lower() else "String"

                try:
                    ssm.put_parameter(
                        Name=param_name,
                        Value=str(value),
                        Type=param_type,
                        Overwrite=overwrite,
                    )
                    saved_params.append(param_name)
                    self.logger.debug(f"Saved parameter: {param_name}")

                except Exception as e:
                    self.logger.error(f"Failed to save parameter {param_name}: {e}")

            self.logger.info(f"Saved {len(saved_params)} parameters to Parameter Store")
            return True, saved_params

        except Exception as e:
            self.logger.error(f"Failed to save to Parameter Store: {e}")
            return False, []

    def generate_env_template(
        self,
        output_file: Optional[Path] = None,
        include_secrets: bool = False,
    ) -> str:
        """
        Generate .env.example template file.

        Args:
            output_file: Output file path (default: specs/{adw_id}/config/.env.example)
            include_secrets: Whether to include secret values (not recommended)

        Returns:
            Path to generated template file
        """
        self.logger.info("Generating .env template...")

        if output_file is None:
            output_file = self.config_dir / ".env.example"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load schema if available
        schema = self._load_schema()

        template_lines = [
            "# Auto-generated environment configuration template",
            f"# ADW ID: {self.adw_id}",
            f"# Environment: {self.environment}",
            "",
        ]

        # Group variables by category
        categories = self._categorize_config_keys(schema)

        for category, keys in categories.items():
            if not keys:
                continue

            template_lines.append(f"# {category}")
            template_lines.append("")

            for key in keys:
                # Get value from config or schema
                value = self._config.get(key, "")

                # Get description from schema
                description = ""
                if schema and key in schema.get("properties", {}):
                    description = schema["properties"][key].get("description", "")

                # Mask secrets
                if not include_secrets and self._is_secret_key(key):
                    value = "your-secret-value-here"

                # Add description as comment
                if description:
                    template_lines.append(f"# {description}")

                # Add variable
                template_lines.append(f"{key}={value}")
                template_lines.append("")

        # Write template file
        template_content = "\n".join(template_lines)
        with open(output_file, "w") as f:
            f.write(template_content)

        self.logger.info(f"✅ Generated template: {output_file}")
        return str(output_file)

    def generate_config_schema(
        self,
        output_file: Optional[Path] = None,
    ) -> str:
        """
        Generate JSON schema for configuration validation.

        Args:
            output_file: Output file path (default: specs/{adw_id}/config/config.schema.json)

        Returns:
            Path to generated schema file
        """
        self.logger.info("Generating configuration schema...")

        if output_file is None:
            output_file = self.config_dir / "config.schema.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Build schema from current configuration
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"ADW Configuration - {self.adw_id}",
            "description": f"Configuration schema for ADW workflow {self.adw_id}",
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Infer types from current config
        for key, value in self._config.items():
            prop_schema = self._infer_schema_type(key, value)
            schema["properties"][key] = prop_schema

            # Mark non-secret required fields
            if not self._is_secret_key(key) and value:
                schema["required"].append(key)

        # Write schema file
        with open(output_file, "w") as f:
            json.dump(schema, f, indent=2)

        self._schema = schema
        self.logger.info(f"✅ Generated schema: {output_file}")
        return str(output_file)

    def validate_config(
        self,
        config: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration to validate (default: current config)
            schema: Schema to validate against (default: load from file)

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        self.logger.info("Validating configuration...")

        if config is None:
            config = self._config

        if schema is None:
            schema = self._load_schema()

        if not schema:
            self.logger.warning("No schema available for validation")
            return True, []

        errors = []

        # Check required fields
        for required_key in schema.get("required", []):
            if required_key not in config or not config[required_key]:
                errors.append(f"Missing required field: {required_key}")

        # Validate types and constraints
        for key, value in config.items():
            if key not in schema.get("properties", {}):
                continue

            prop_schema = schema["properties"][key]
            prop_type = prop_schema.get("type")

            # Type validation
            if prop_type == "string" and not isinstance(value, str):
                errors.append(f"{key}: Expected string, got {type(value).__name__}")
            elif prop_type == "integer" and not isinstance(value, int):
                errors.append(f"{key}: Expected integer, got {type(value).__name__}")
            elif prop_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{key}: Expected number, got {type(value).__name__}")
            elif prop_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{key}: Expected boolean, got {type(value).__name__}")

            # Pattern validation
            if "pattern" in prop_schema and isinstance(value, str):
                import re
                if not re.match(prop_schema["pattern"], value):
                    errors.append(f"{key}: Does not match pattern {prop_schema['pattern']}")

        is_valid = len(errors) == 0

        if is_valid:
            self.logger.info("✅ Configuration is valid")
        else:
            self.logger.error(f"❌ Configuration validation failed: {len(errors)} errors")
            for error in errors:
                self.logger.error(f"  - {error}")

        return is_valid, errors

    def sync_config(
        self,
        direction: str = "local_to_cloud",
        keys: Optional[List[str]] = None,
    ) -> Tuple[bool, int]:
        """
        Sync configuration between local and cloud.

        Args:
            direction: Sync direction ("local_to_cloud" or "cloud_to_local")
            keys: Specific keys to sync (default: all)

        Returns:
            Tuple of (success, number of synced keys)
        """
        self.logger.info(f"Syncing configuration: {direction}")

        if direction == "local_to_cloud":
            # Load local config
            local_config = {}
            local_config.update(self.load_worktree_config())
            local_config.update(self.load_project_config())

            # Filter keys if specified
            if keys:
                local_config = {k: v for k, v in local_config.items() if k in keys}

            # Save to Parameter Store
            success, saved_params = self.save_to_parameter_store(local_config)
            return success, len(saved_params)

        elif direction == "cloud_to_local":
            # Load from Parameter Store
            cloud_config = self.load_aws_config()

            # Filter keys if specified
            if keys:
                cloud_config = {k: v for k, v in cloud_config.items() if k in keys}

            # Save to local files
            synced_count = 0

            # Update worktree .env.local
            if self.worktree_dir.exists():
                env_local_file = self.worktree_dir / ".env.local"
                self._save_env_file(env_local_file, cloud_config)
                synced_count += len(cloud_config)

            return True, synced_count

        else:
            self.logger.error(f"Invalid sync direction: {direction}")
            return False, 0

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    # Private helper methods

    def _load_env_file(self, file_path: Path) -> Dict[str, str]:
        """Load key=value pairs from .env file."""
        config = {}

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

        return config

    def _save_env_file(self, file_path: Path, config: Dict[str, str]) -> None:
        """Save configuration to .env file."""
        lines = []

        for key, value in config.items():
            lines.append(f"{key}={value}")

        with open(file_path, "w") as f:
            f.write("\n".join(lines))

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load configuration schema from file."""
        if self._schema:
            return self._schema

        schema_file = self.config_dir / "config.schema.json"
        if not schema_file.exists():
            return None

        with open(schema_file, "r") as f:
            self._schema = json.load(f)

        return self._schema

    def _is_secret_key(self, key: str) -> bool:
        """Check if key contains secret/sensitive data."""
        secret_keywords = ["secret", "password", "key", "token", "credential"]
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in secret_keywords)

    def _infer_schema_type(self, key: str, value: Any) -> Dict[str, Any]:
        """Infer JSON schema type from value."""
        schema = {}

        if isinstance(value, bool):
            schema["type"] = "boolean"
        elif isinstance(value, int):
            schema["type"] = "integer"
        elif isinstance(value, float):
            schema["type"] = "number"
        elif isinstance(value, str):
            schema["type"] = "string"

            # Add pattern for specific types
            if "port" in key.lower():
                schema["pattern"] = "^[0-9]+$"
            elif "url" in key.lower():
                schema["pattern"] = "^https?://"
            elif "email" in key.lower():
                schema["pattern"] = "^[^@]+@[^@]+\\.[^@]+$"

        else:
            schema["type"] = "string"

        # Add description
        schema["description"] = f"Configuration value for {key}"

        return schema

    def _categorize_config_keys(self, schema: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """Categorize configuration keys by prefix or type."""
        categories = {
            "Database Configuration": [],
            "API Configuration": [],
            "AWS Configuration": [],
            "Development Configuration": [],
            "Other Configuration": [],
        }

        for key in self._config.keys():
            key_lower = key.lower()

            if any(db in key_lower for db in ["database", "db", "postgres", "mysql", "mongo"]):
                categories["Database Configuration"].append(key)
            elif any(api in key_lower for api in ["api", "endpoint", "url", "host"]):
                categories["API Configuration"].append(key)
            elif any(aws in key_lower for aws in ["aws", "bucket", "lambda", "dynamodb", "s3"]):
                categories["AWS Configuration"].append(key)
            elif any(dev in key_lower for dev in ["port", "debug", "log"]):
                categories["Development Configuration"].append(key)
            else:
                categories["Other Configuration"].append(key)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


# Convenience functions

def load_config(
    adw_id: str,
    environment: str = "dev",
    include_aws: bool = False,
    logger: Optional[logging.Logger] = None,
) -> ConfigManager:
    """
    Load configuration from all sources.

    Args:
        adw_id: Workflow ID
        environment: Environment name
        include_aws: Whether to load from AWS Parameter Store
        logger: Logger instance

    Returns:
        ConfigManager instance with loaded configuration
    """
    manager = ConfigManager(adw_id, environment, logger)

    # Load local configurations
    manager.load_worktree_config()
    manager.load_project_config()

    # Load AWS config if requested
    if include_aws:
        manager.load_aws_config()

    return manager


def generate_templates(
    adw_id: str,
    environment: str = "dev",
    logger: Optional[logging.Logger] = None,
) -> Tuple[str, str]:
    """
    Generate both .env template and JSON schema.

    Args:
        adw_id: Workflow ID
        environment: Environment name
        logger: Logger instance

    Returns:
        Tuple of (template_path, schema_path)
    """
    manager = ConfigManager(adw_id, environment, logger)

    # Load existing config
    manager.load_worktree_config()
    manager.load_project_config()

    # Generate files
    template_path = manager.generate_env_template()
    schema_path = manager.generate_config_schema()

    return template_path, schema_path
