#!/usr/bin/env python3
"""
ADW Config - Configuration Management CLI

Manage configuration across local development and AWS deployments.

Usage:
    uv run adws/adw_config.py --adw-id <adw-id> --action <action> [options]

Actions:
    generate    - Generate .env template and JSON schema
    validate    - Validate configuration against schema
    sync        - Sync configuration between local and cloud
    load        - Load and display current configuration
    set         - Set a configuration value
    get         - Get a configuration value

Features:
    - Unified configuration management
    - Local and cloud synchronization
    - Schema validation
    - Template generation
    - Environment-specific configuration
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.config_manager import ConfigManager, load_config, generate_templates
from adws.adw_modules.utils import setup_logger


def action_generate(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Generate configuration templates."""
    logger.info(f"Generating templates for {args.adw_id}...")

    try:
        template_path, schema_path = generate_templates(
            adw_id=args.adw_id,
            environment=args.environment,
            logger=logger,
        )

        logger.info("✅ Templates generated successfully!")
        logger.info(f"   Template: {template_path}")
        logger.info(f"   Schema: {schema_path}")

        return 0

    except Exception as e:
        logger.error(f"❌ Failed to generate templates: {e}")
        return 1


def action_validate(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Validate configuration."""
    logger.info(f"Validating configuration for {args.adw_id}...")

    try:
        # Load configuration
        manager = load_config(
            adw_id=args.adw_id,
            environment=args.environment,
            include_aws=args.include_aws,
            logger=logger,
        )

        # Validate
        is_valid, errors = manager.validate_config()

        if is_valid:
            logger.info("✅ Configuration is valid!")
            return 0
        else:
            logger.error(f"❌ Configuration validation failed ({len(errors)} errors):")
            for error in errors:
                logger.error(f"   - {error}")
            return 1

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return 1


def action_sync(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Sync configuration between local and cloud."""
    logger.info(f"Syncing configuration: {args.direction}")

    try:
        manager = ConfigManager(
            adw_id=args.adw_id,
            environment=args.environment,
            logger=logger,
        )

        # Parse keys if provided
        keys = args.keys.split(",") if args.keys else None

        # Sync
        success, synced_count = manager.sync_config(
            direction=args.direction,
            keys=keys,
        )

        if success:
            logger.info(f"✅ Synced {synced_count} configuration values!")
            return 0
        else:
            logger.error("❌ Sync failed")
            return 1

    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        return 1


def action_load(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Load and display configuration."""
    logger.info(f"Loading configuration for {args.adw_id}...")

    try:
        manager = load_config(
            adw_id=args.adw_id,
            environment=args.environment,
            include_aws=args.include_aws,
            logger=logger,
        )

        config = manager.get_all()

        if not config:
            logger.warning("No configuration found")
            return 0

        logger.info("\n" + "=" * 60)
        logger.info("Configuration Values")
        logger.info("=" * 60)

        # Group by category
        for key, value in sorted(config.items()):
            # Mask secrets
            if any(secret in key.lower() for secret in ["secret", "password", "key", "token"]):
                display_value = "***HIDDEN***"
            else:
                display_value = value

            logger.info(f"{key:30} = {display_value}")

        logger.info("=" * 60)
        logger.info(f"Total: {len(config)} configuration values")

        return 0

    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        return 1


def action_set(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Set a configuration value."""
    if not args.key or not args.value:
        logger.error("❌ --key and --value are required for set action")
        return 1

    logger.info(f"Setting {args.key} = {args.value}")

    try:
        manager = ConfigManager(
            adw_id=args.adw_id,
            environment=args.environment,
            logger=logger,
        )

        # Load existing config
        manager.load_worktree_config()
        manager.load_project_config()

        # Set new value
        manager.set(args.key, args.value)

        # Save to worktree .env.local if exists
        worktree_dir = Path("trees") / args.adw_id
        if worktree_dir.exists():
            env_local_file = worktree_dir / ".env.local"

            # Load existing .env.local
            env_config = {}
            if env_local_file.exists():
                env_config = manager._load_env_file(env_local_file)

            # Update value
            env_config[args.key] = args.value

            # Save
            manager._save_env_file(env_local_file, env_config)
            logger.info(f"✅ Updated {env_local_file}")

        # Optionally sync to cloud
        if args.sync_to_cloud:
            success, saved_params = manager.save_to_parameter_store({args.key: args.value})
            if success:
                logger.info(f"✅ Synced to Parameter Store")
            else:
                logger.warning("⚠️ Failed to sync to Parameter Store")

        logger.info("✅ Configuration value set!")
        return 0

    except Exception as e:
        logger.error(f"❌ Failed to set configuration: {e}")
        return 1


def action_get(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Get a configuration value."""
    if not args.key:
        logger.error("❌ --key is required for get action")
        return 1

    try:
        manager = load_config(
            adw_id=args.adw_id,
            environment=args.environment,
            include_aws=args.include_aws,
            logger=logger,
        )

        value = manager.get(args.key)

        if value is None:
            logger.warning(f"⚠️ Configuration key not found: {args.key}")
            return 1

        # Mask secrets in output
        if any(secret in args.key.lower() for secret in ["secret", "password", "key", "token"]):
            display_value = "***HIDDEN*** (use --show-secrets to display)"
            if args.show_secrets:
                display_value = value
        else:
            display_value = value

        logger.info(f"{args.key} = {display_value}")
        return 0

    except Exception as e:
        logger.error(f"❌ Failed to get configuration: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADW Configuration Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate templates
  uv run adws/adw_config.py --adw-id abc123 --action generate

  # Validate configuration
  uv run adws/adw_config.py --adw-id abc123 --action validate

  # Sync local to cloud
  uv run adws/adw_config.py --adw-id abc123 --action sync --direction local_to_cloud

  # Load and display configuration
  uv run adws/adw_config.py --adw-id abc123 --action load

  # Set a value
  uv run adws/adw_config.py --adw-id abc123 --action set --key API_KEY --value secret123

  # Get a value
  uv run adws/adw_config.py --adw-id abc123 --action get --key API_KEY
        """
    )

    parser.add_argument("--adw-id", required=True, help="ADW workflow ID")
    parser.add_argument(
        "--action",
        required=True,
        choices=["generate", "validate", "sync", "load", "set", "get"],
        help="Action to perform",
    )
    parser.add_argument(
        "--environment",
        default="dev",
        choices=["dev", "staging", "production"],
        help="Environment (default: dev)",
    )

    # Sync options
    parser.add_argument(
        "--direction",
        choices=["local_to_cloud", "cloud_to_local"],
        default="local_to_cloud",
        help="Sync direction (for sync action)",
    )
    parser.add_argument(
        "--keys",
        help="Comma-separated list of keys to sync (for sync action)",
    )

    # Set/get options
    parser.add_argument("--key", help="Configuration key (for set/get actions)")
    parser.add_argument("--value", help="Configuration value (for set action)")
    parser.add_argument(
        "--sync-to-cloud",
        action="store_true",
        help="Also sync to Parameter Store (for set action)",
    )
    parser.add_argument(
        "--show-secrets",
        action="store_true",
        help="Show secret values (for get action)",
    )

    # Load options
    parser.add_argument(
        "--include-aws",
        action="store_true",
        help="Include AWS Parameter Store values (for load/validate/get actions)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("adw_config", level=logging.INFO)

    logger.info("=" * 60)
    logger.info("⚙️ ADW Configuration Management")
    logger.info("=" * 60)
    logger.info(f"📋 ADW ID: {args.adw_id}")
    logger.info(f"🎬 Action: {args.action}")
    logger.info(f"🌍 Environment: {args.environment}")
    logger.info("")

    # Execute action
    action_map = {
        "generate": action_generate,
        "validate": action_validate,
        "sync": action_sync,
        "load": action_load,
        "set": action_set,
        "get": action_get,
    }

    action_func = action_map[args.action]
    exit_code = action_func(args, logger)

    logger.info("")
    if exit_code == 0:
        logger.info("✅ Action completed successfully!")
    else:
        logger.info("❌ Action failed!")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
