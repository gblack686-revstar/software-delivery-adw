"""State management for ADW workflows.

Provides persistent state across all phases of the workflow with AWS infrastructure tracking.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from .data_types import (
    ADWStateData,
    InfrastructureConfig,
    CDKStackInfo,
    InfrastructureTestResult
)


class ADWState:
    """Manages persistent state for an ADW workflow run.

    Enhanced with AWS infrastructure tracking capabilities.
    """

    def __init__(self, adw_id: str, logger: Optional[logging.Logger] = None):
        """Initialize state for a specific ADW ID.

        Args:
            adw_id: Unique workflow identifier (8-char hex string)
            logger: Optional logger instance
        """
        self.adw_id = adw_id
        self.logger = logger

        # Get project root (parent of adws directory)
        # __file__ is in adws/adw_modules/, go up 3 levels
        project_root = Path(__file__).parent.parent.parent
        self.state_dir = project_root / "agents" / adw_id
        self.state_file = self.state_dir / "adw_state.json"

        # Create directory if it doesn't exist
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Core data using Pydantic model
        self._core_data: Optional[ADWStateData] = None

        # Extended phase-specific data (for software-delivery-adw phases)
        self._extended_data: Dict[str, Any] = {}

        # Load existing state if available
        if self.state_file.exists():
            self._load_from_disk()
        else:
            # Initialize new state
            self._core_data = ADWStateData(adw_id=adw_id)
            self._extended_data = {
                "created_at": datetime.now().isoformat(),
                "current_phase": None,
                "discovery": {},
                "scoping": {},
                "planning": {},
                "development": {},
                "ui_review": {},
                "test": {},
                "review": {}
            }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state.

        Checks both core data and extended data.

        Args:
            key: Key to retrieve (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Value from state or default
        """
        # Try to get from core data first (Pydantic model)
        if hasattr(self._core_data, key):
            return getattr(self._core_data, key)

        # Try extended data for dot-notation and phase data
        keys = key.split('.')
        value = self._extended_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    def update(self, **kwargs) -> None:
        """Update state with new values.

        Updates both core data and extended data as appropriate.

        Args:
            **kwargs: Key-value pairs to update
        """
        # Update core data fields if they exist in ADWStateData
        core_fields = ADWStateData.model_fields.keys()

        for key, value in kwargs.items():
            if key in core_fields:
                # Update core data
                setattr(self._core_data, key, value)
            else:
                # Update extended data
                self._extended_data[key] = value

        self._extended_data["updated_at"] = datetime.now().isoformat()

    def update_phase(self, phase: str, **kwargs) -> None:
        """Update a specific phase's data.

        Args:
            phase: Phase name (discovery, scoping, planning, etc.)
            **kwargs: Key-value pairs to update in that phase
        """
        if phase not in self._extended_data:
            self._extended_data[phase] = {}

        self._extended_data[phase].update(kwargs)
        self._extended_data["current_phase"] = phase
        self._extended_data["updated_at"] = datetime.now().isoformat()

    def save(self, source: str = "unknown") -> None:
        """Save state to disk.

        Args:
            source: Source of the save operation for logging
        """
        # Combine core and extended data for saving
        save_data = {
            **self._core_data.model_dump(mode="json", exclude_none=True),
            **self._extended_data
        }

        with open(self.state_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)

        if self.logger:
            self.logger.debug(f"State saved by {source}")

    def _load_from_disk(self) -> None:
        """Load state from disk."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            # Extract core fields
            core_fields = ADWStateData.model_fields.keys()
            core_data_dict = {k: v for k, v in data.items() if k in core_fields}

            # Create core data model
            self._core_data = ADWStateData(**core_data_dict)

            # Store remaining data as extended
            self._extended_data = {k: v for k, v in data.items() if k not in core_fields}

    @classmethod
    def load(cls, adw_id: str, logger: Optional[logging.Logger] = None) -> Optional["ADWState"]:
        """Load an existing state by ADW ID.

        Args:
            adw_id: Workflow ID to load
            logger: Optional logger instance

        Returns:
            ADWState instance if found, None otherwise
        """
        # Try to find state file
        project_root = Path(__file__).parent.parent.parent
        state_file = project_root / "agents" / adw_id / "adw_state.json"

        if not state_file.exists():
            return None

        instance = cls(adw_id, logger)
        return instance

    @classmethod
    def load_from_id(cls, adw_id: str) -> Optional["ADWState"]:
        """Load an existing state by ADW ID (legacy method).

        Args:
            adw_id: Workflow ID to load

        Returns:
            ADWState instance if found, None otherwise
        """
        return cls.load(adw_id, None)

    # AWS Infrastructure Methods

    def update_infrastructure_config(self, config: InfrastructureConfig) -> None:
        """Update infrastructure configuration.

        Args:
            config: Infrastructure configuration
        """
        self._core_data.infrastructure_config = config
        self._extended_data["updated_at"] = datetime.now().isoformat()

    def add_cdk_stack(self, stack_info: CDKStackInfo) -> None:
        """Add or update a CDK stack.

        Args:
            stack_info: CDK stack information
        """
        if not self._core_data.infrastructure_config:
            # Create default config if none exists
            self._core_data.infrastructure_config = InfrastructureConfig(
                resource_prefix=f"{self.adw_id}-dev"
            )

        # Find and update existing stack or append new one
        stacks = self._core_data.infrastructure_config.stacks
        for i, stack in enumerate(stacks):
            if stack.stack_name == stack_info.stack_name:
                stacks[i] = stack_info
                return

        stacks.append(stack_info)

    def mark_infrastructure_deployed(self, deployed: bool = True) -> None:
        """Mark infrastructure as deployed.

        Args:
            deployed: Deployment status
        """
        self._core_data.infrastructure_deployed = deployed
        self._extended_data["updated_at"] = datetime.now().isoformat()

    def add_infrastructure_test_result(self, result: InfrastructureTestResult) -> None:
        """Add an infrastructure test result.

        Args:
            result: Test result to add
        """
        self._core_data.infrastructure_test_results.append(result)

    def mark_infrastructure_tested(self, tested: bool = True) -> None:
        """Mark infrastructure as tested.

        Args:
            tested: Test status
        """
        self._core_data.infrastructure_tested = tested
        self._extended_data["updated_at"] = datetime.now().isoformat()

    def get_infrastructure_config(self) -> Optional[InfrastructureConfig]:
        """Get infrastructure configuration.

        Returns:
            Infrastructure configuration or None
        """
        return self._core_data.infrastructure_config

    def get_cdk_stacks(self) -> List[CDKStackInfo]:
        """Get all CDK stacks.

        Returns:
            List of CDK stack information
        """
        if not self._core_data.infrastructure_config:
            return []
        return self._core_data.infrastructure_config.stacks

    def to_dict(self) -> Dict[str, Any]:
        """Get complete state as dictionary.

        Returns:
            Complete state dictionary
        """
        return {
            **self._core_data.model_dump(mode="json", exclude_none=True),
            **self._extended_data
        }

    def __repr__(self) -> str:
        """String representation of state."""
        phase = self._extended_data.get("current_phase", "uninitialized")
        return f"ADWState(adw_id='{self.adw_id}', phase='{phase}')"


def make_adw_id() -> str:
    """Generate a unique ADW ID.

    Returns:
        8-character hexadecimal string
    """
    import uuid
    return str(uuid.uuid4())[:8]
