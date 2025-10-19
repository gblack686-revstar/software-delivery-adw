"""Subagent execution with MCP configuration management.

Provides utilities to run specialized subagents with specific MCP configurations,
preserving context in the main orchestrator.
"""

import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional


@contextmanager
def temporary_mcp_config(mcp_config: Dict[str, Any], project_root: Path):
    """Context manager to temporarily use a specific MCP config.

    Args:
        mcp_config: MCP server configuration dict
        project_root: Path to project root directory

    Yields:
        Path to temporary .mcp.json file
    """
    mcp_file = project_root / ".mcp.json"
    backup_file = project_root / ".mcp.json.backup"

    # Backup existing config if it exists
    has_backup = False
    if mcp_file.exists():
        shutil.copy(mcp_file, backup_file)
        has_backup = True

    try:
        # Write temporary config
        with open(mcp_file, 'w') as f:
            json.dump(mcp_config, f, indent=2)

        yield mcp_file

    finally:
        # Restore original config
        if has_backup:
            shutil.move(backup_file, mcp_file)
        elif mcp_file.exists():
            mcp_file.unlink()


class SubagentExecutor:
    """Manages subagent execution with MCP configuration."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize subagent executor.

        Args:
            project_root: Path to project root (defaults to current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.configs_dir = project_root / "subagent_configs"

    def load_mcp_config(self, config_name: str) -> Dict[str, Any]:
        """Load an MCP configuration file.

        Args:
            config_name: Name of config file (without .json extension)

        Returns:
            MCP configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_file = self.configs_dir / f"{config_name}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"MCP config not found: {config_file}")

        with open(config_file) as f:
            return json.load(f)

    def execute_with_mcp(
        self,
        mcp_config_name: str,
        command: list,
        description: str = "Executing subagent"
    ) -> subprocess.CompletedProcess:
        """Execute a command with a specific MCP configuration.

        Args:
            mcp_config_name: Name of MCP config to use (e.g., "mcp.discovery")
            command: Command to execute as a list
            description: Human-readable description of what's being executed

        Returns:
            CompletedProcess with stdout/stderr
        """
        print(f"[SubAgent] {description}")
        print(f"[SubAgent] Loading MCP config: {mcp_config_name}")

        # Load the MCP config
        mcp_config = self.load_mcp_config(mcp_config_name)

        # Execute with temporary MCP config
        with temporary_mcp_config(mcp_config, self.project_root):
            print(f"[SubAgent] Executing: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

        return result

    def run_discovery_agent(
        self,
        deal_info: str,
        adw_id: str
    ) -> subprocess.CompletedProcess:
        """Run discovery subagent with discovery MCP config.

        Args:
            deal_info: Client/deal information
            adw_id: Workflow ID

        Returns:
            CompletedProcess result
        """
        command = [
            "uv", "run",
            "adws/adw_discovery.py",
            "--deal-info", deal_info,
            "--adw-id", adw_id
        ]

        return self.execute_with_mcp(
            mcp_config_name="mcp.discovery",
            command=command,
            description=f"Running Discovery Agent (ADW: {adw_id})"
        )

    def run_scoping_agent(
        self,
        adw_id: str,
        additional_context: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run scoping subagent with scoping MCP config.

        Args:
            adw_id: Workflow ID
            additional_context: Optional additional context (transcripts, etc.)

        Returns:
            CompletedProcess result
        """
        command = [
            "uv", "run",
            "adws/adw_scoping.py",
            "--adw-id", adw_id
        ]

        if additional_context:
            command.extend(["--context", additional_context])

        return self.execute_with_mcp(
            mcp_config_name="mcp.scoping",
            command=command,
            description=f"Running Scoping Agent (ADW: {adw_id})"
        )

    def run_planning_agent(
        self,
        adw_id: str,
        sprints: int = 4
    ) -> subprocess.CompletedProcess:
        """Run planning subagent with planning MCP config.

        Args:
            adw_id: Workflow ID
            sprints: Number of sprints

        Returns:
            CompletedProcess result
        """
        command = [
            "uv", "run",
            "adws/adw_planning.py",
            "--adw-id", adw_id,
            "--sprints", str(sprints)
        ]

        return self.execute_with_mcp(
            mcp_config_name="mcp.planning",
            command=command,
            description=f"Running Planning Agent (ADW: {adw_id})"
        )

    def run_developer_agent(
        self,
        story_id: str,
        adw_id: str
    ) -> subprocess.CompletedProcess:
        """Run developer subagent with developer MCP config.

        Args:
            story_id: Story ID to implement
            adw_id: Workflow ID

        Returns:
            CompletedProcess result
        """
        command = [
            "uv", "run",
            "adws/adw_develop.py",
            "--story-id", story_id,
            "--adw-id", adw_id
        ]

        return self.execute_with_mcp(
            mcp_config_name="mcp.developer",
            command=command,
            description=f"Running Developer Agent for {story_id} (ADW: {adw_id})"
        )

    def run_ui_reviewer_agent(
        self,
        adw_id: str,
        app_url: str = "http://localhost:3000"
    ) -> subprocess.CompletedProcess:
        """Run UI reviewer subagent with UI reviewer MCP config.

        Args:
            adw_id: Workflow ID
            app_url: Application URL to test

        Returns:
            CompletedProcess result
        """
        command = [
            "uv", "run",
            "adws/adw_ui_review.py",
            "--adw-id", adw_id,
            "--app-url", app_url
        ]

        return self.execute_with_mcp(
            mcp_config_name="mcp.ui_reviewer",
            command=command,
            description=f"Running UI Reviewer Agent (ADW: {adw_id})"
        )
