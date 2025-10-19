#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml"]
# ///

"""Modular Scoping Agent - Individual file generation with parallel execution.

This script provides granular control over scoping file generation:
- Generate individual files with /scope_file_N commands
- Automatic dependency resolution
- Parallel execution for independent files
- Context summarization to prevent window overflow
- Resume capability after failures

Usage:
    # Generate individual file
    uv run adw_scoping_modular.py --adw-id abc123 --file-num 2 [--force]

    # Generate all missing files with optimal ordering
    uv run adw_scoping_modular.py --adw-id abc123 --all [--parallel]

    # Generate specific files in parallel
    uv run adw_scoping_modular.py --adw-id abc123 --file-nums 6,11 --parallel
"""

import argparse
import sys
import yaml
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState
from adws.adw_modules.agent import AgentPromptRequest, prompt_claude_code_with_retry
from adws.adw_modules.cdk_generator import (
    generate_cdk_config_yaml,
    generate_cdk_construct_template,
    generate_parameter_store_script
)
from adws.adw_modules.data_types import InfrastructureConfig


# File dependency graph - which files must be completed before others
FILE_DEPENDENCIES = {
    2: [1],           # Requirements needs discovery brief
    3: [2],           # User flows needs requirements
    4: [3],           # Data models needs user flows
    5: [4],           # ERD needs data models
    6: [5],           # ML research needs ERD
    11: [5],          # Security needs ERD (can run parallel with 6!)
    7: [6, 11],       # AWS analysis needs ML research + Security
    8: [7],           # AWS services needs AWS analysis
    9: [8],           # Architecture needs services
    10: [9],          # CDK needs architecture (can run parallel with 12,13,14!)
    12: [9],          # Cost needs architecture
    13: [9],          # Validation needs architecture
    14: [9],          # LLM prompts needs architecture
}

# Parallel execution groups (files that can run simultaneously)
PARALLEL_GROUPS = [
    [6, 11],          # ML research + Security (after file 5)
    [10, 12, 13, 14], # CDK, Cost, Validation, LLM prompts (after file 9)
]


def load_scoping_instructions():
    """Load scoping file instructions from YAML config."""
    instructions_path = Path(__file__).parent / "scoping_instructions.yaml"
    with open(instructions_path, 'r') as f:
        return yaml.safe_load(f)


def read_file_safe(file_path):
    """Read file content safely, return empty string if doesn't exist."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def get_file_config(file_num: int) -> Optional[Dict]:
    """Get configuration for a specific file number.

    Args:
        file_num: File number (2-14)

    Returns:
        File configuration dict or None if not found
    """
    config = load_scoping_instructions()
    for file_config in config['files']:
        if file_config['number'] == file_num:
            return file_config
    return None


def summarize_context(context: str, max_length: int = 8000) -> str:
    """Summarize context if it exceeds max length.

    Args:
        context: Full context string
        max_length: Maximum context length before summarization

    Returns:
        Original or summarized context
    """
    if len(context) <= max_length:
        return context

    # Simple summarization: take first and last portions
    half = max_length // 2
    return (
        context[:half] +
        "\n\n[... CONTEXT SUMMARIZED FOR LENGTH ...]\n\n" +
        context[-half:]
    )


def build_context_for_file(
    adw_id: str,
    file_num: int,
    specs_dir: Path,
    context_mode: str = "smart"
) -> str:
    """Build accumulated context from all prerequisite files.

    Args:
        adw_id: Workflow ID
        file_num: Target file number
        specs_dir: Specifications directory
        context_mode: 'full' | 'summarized' | 'smart'

    Returns:
        Accumulated context string
    """
    # Start with discovery brief (file 1)
    discovery_brief_path = specs_dir / "1_discovery_brief.md"
    discovery_brief = read_file_safe(discovery_brief_path)

    # Check for project file
    project_file = Path(f"projects/{adw_id}.md")
    project_context = ""
    if project_file.exists():
        project_context = read_file_safe(project_file)

    # Initialize context
    context = f"""# Project Context

{project_context if project_context else "No project file provided."}

# Discovery Brief (File 1)

{discovery_brief}
"""

    # Get all prerequisite files based on dependency graph
    prerequisites = get_all_prerequisites(file_num)

    # Load scoping instructions to get filenames
    config = load_scoping_instructions()
    file_configs_map = {fc['number']: fc for fc in config['files']}

    # Add each prerequisite file to context
    for prereq_num in sorted(prerequisites):
        if prereq_num == 1:  # Skip discovery brief (already included)
            continue

        file_config = file_configs_map.get(prereq_num)
        if not file_config:
            continue

        filename = file_config['filename']
        title = file_config['title']
        file_path = specs_dir / f"{prereq_num}_{filename}"

        if file_path.exists():
            content = read_file_safe(file_path)

            # Smart mode: summarize older files, keep recent files full
            if context_mode == "smart":
                # Files more than 5 positions back get summarized
                if file_num - prereq_num > 5:
                    content = summarize_context(content, max_length=2000)
            elif context_mode == "summarized":
                content = summarize_context(content, max_length=3000)
            # 'full' mode uses content as-is

            context += f"\n\n# {title} (File {prereq_num})\n\n{content}"

    return context


def get_all_prerequisites(file_num: int) -> Set[int]:
    """Get all prerequisite file numbers (transitive closure).

    Args:
        file_num: Target file number

    Returns:
        Set of all prerequisite file numbers
    """
    prerequisites = set()
    to_process = [file_num]

    while to_process:
        current = to_process.pop()
        deps = FILE_DEPENDENCIES.get(current, [])
        for dep in deps:
            if dep not in prerequisites:
                prerequisites.add(dep)
                to_process.append(dep)

    return prerequisites


def check_file_exists(adw_id: str, file_num: int) -> bool:
    """Check if a scoping file already exists.

    Args:
        adw_id: Workflow ID
        file_num: File number

    Returns:
        True if file exists
    """
    specs_dir = Path(f"specs/{adw_id}")

    # Special case for file 1 (discovery brief - created during discovery phase)
    if file_num == 1:
        file_path = specs_dir / "1_discovery_brief.md"
        return file_path.exists()

    file_config = get_file_config(file_num)
    if not file_config:
        return False

    filename = file_config['filename']
    file_path = specs_dir / f"{file_num}_{filename}"

    return file_path.exists()


def generate_single_file(
    adw_id: str,
    file_num: int,
    force: bool = False,
    context_mode: str = "smart",
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, str]:
    """Generate a single scoping file.

    Args:
        adw_id: Workflow ID
        file_num: File number (2-14)
        force: Regenerate even if file exists
        context_mode: Context management mode
        logger: Optional logger instance

    Returns:
        Tuple of (success: bool, message: str)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Check if file already exists
    if not force and check_file_exists(adw_id, file_num):
        msg = f"File {file_num} already exists (use --force to regenerate)"
        logger.info(msg)
        return True, msg

    # Validate file number
    file_config = get_file_config(file_num)
    if not file_config:
        msg = f"Invalid file number: {file_num}"
        logger.error(msg)
        return False, msg

    # Check prerequisites
    prerequisites = FILE_DEPENDENCIES.get(file_num, [])
    for prereq in prerequisites:
        if not check_file_exists(adw_id, prereq):
            msg = f"Prerequisite file {prereq} not found. Generate it first."
            logger.error(msg)
            return False, msg

    # Create directories
    specs_dir = Path(f"specs/{adw_id}")
    specs_dir.mkdir(parents=True, exist_ok=True)

    agent_output_dir = Path(f"agents/{adw_id}/scoping")
    agent_output_dir.mkdir(parents=True, exist_ok=True)

    # Build context
    logger.info(f"Building context for file {file_num} (mode: {context_mode})")
    accumulated_context = build_context_for_file(
        adw_id, file_num, specs_dir, context_mode
    )

    # Extract file details
    filename = file_config['filename']
    title = file_config['title']
    instructions = file_config['instructions']

    logger.info(f"Generating File {file_num}: {filename}")
    logger.info(f"  {title}")

    # Build prompt
    prompt = f"""You are a technical architect conducting detailed scoping for a software project.

# Context from Previous Analysis

{accumulated_context}

---

# Your Task

Generate the next scoping document: **{file_num}_{filename}**

{instructions}

# Output Requirements

- Provide ONLY the file content (no explanations, no markdown code blocks)
- Be specific and detailed, not generic templates
- Use information from the discovery brief and previous scoping files
- Reference specific technologies, services, and requirements
- Include realistic estimates and recommendations
- Format exactly as specified in the instructions above

Generate the complete {filename} file now:
"""

    # Create output file path for agent logs
    output_file = agent_output_dir / f"file_{file_num}_{filename.replace('.', '_')}.jsonl"

    # Create agent request
    request = AgentPromptRequest(
        prompt=prompt,
        adw_id=adw_id,
        agent_name="scoping_modular",
        model="sonnet",
        dangerously_skip_permissions=True,
        output_file=str(output_file),
        working_dir=str(Path.cwd())
    )

    # Call Claude Code agent
    logger.info("  Calling Claude Code agent...")
    response = prompt_claude_code_with_retry(request, max_retries=2)

    if not response.success:
        msg = f"Failed to generate file {file_num}: {response.output}"
        logger.error(msg)
        return False, msg

    logger.info(f"  [OK] Generated {filename}")

    # Extract and write file content
    file_content = response.output.strip()
    file_path = specs_dir / f"{file_num}_{filename}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    msg = f"Successfully generated file {file_num}: {filename}"
    return True, msg


def generate_files_parallel(
    adw_id: str,
    file_nums: List[int],
    force: bool = False,
    context_mode: str = "smart",
    logger: Optional[logging.Logger] = None
) -> Dict[int, Tuple[bool, str]]:
    """Generate multiple files in parallel.

    Args:
        adw_id: Workflow ID
        file_nums: List of file numbers to generate
        force: Regenerate even if files exist
        context_mode: Context management mode
        logger: Optional logger instance

    Returns:
        Dict mapping file_num to (success, message) tuples
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    results = {}

    with ThreadPoolExecutor(max_workers=len(file_nums)) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                generate_single_file,
                adw_id,
                file_num,
                force,
                context_mode,
                logger
            ): file_num
            for file_num in file_nums
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_num = future_to_file[future]
            try:
                success, message = future.result()
                results[file_num] = (success, message)
            except Exception as e:
                results[file_num] = (False, f"Exception: {str(e)}")

    return results


def get_missing_files(adw_id: str) -> List[int]:
    """Get list of files that don't exist yet.

    Args:
        adw_id: Workflow ID

    Returns:
        List of missing file numbers (2-14)
    """
    missing = []
    for file_num in range(2, 15):  # Files 2-14
        if not check_file_exists(adw_id, file_num):
            missing.append(file_num)
    return missing


def generate_all_files(
    adw_id: str,
    parallel: bool = True,
    force: bool = False,
    context_mode: str = "smart",
    logger: Optional[logging.Logger] = None
) -> bool:
    """Generate all missing scoping files in optimal order.

    Args:
        adw_id: Workflow ID
        parallel: Enable parallel execution for independent files
        force: Regenerate even if files exist
        context_mode: Context management mode
        logger: Optional logger instance

    Returns:
        True if all files generated successfully
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Determine which files need generation
    if force:
        files_to_generate = list(range(2, 15))
    else:
        files_to_generate = get_missing_files(adw_id)

    if not files_to_generate:
        logger.info("All scoping files already exist!")
        return True

    logger.info(f"Files to generate: {files_to_generate}")

    all_success = True
    generated_count = 0

    if parallel:
        # Use parallel execution groups
        logger.info("Using parallel execution where possible")

        # Process files in dependency order with parallelization
        remaining = set(files_to_generate)

        while remaining:
            # Find files that can run now (all dependencies met)
            ready = []
            for file_num in remaining:
                deps = FILE_DEPENDENCIES.get(file_num, [])
                deps_met = all(
                    check_file_exists(adw_id, dep) or dep not in files_to_generate
                    for dep in deps
                )
                if deps_met:
                    ready.append(file_num)

            if not ready:
                logger.error("Circular dependency or missing prerequisites!")
                return False

            # Check if ready files can run in parallel
            can_parallelize = False
            for group in PARALLEL_GROUPS:
                if set(ready).issubset(set(group)):
                    can_parallelize = True
                    break

            if can_parallelize and len(ready) > 1:
                # Run in parallel
                logger.info(f"Generating files {ready} in parallel...")
                results = generate_files_parallel(
                    adw_id, ready, force, context_mode, logger
                )

                for file_num, (success, message) in results.items():
                    logger.info(f"  File {file_num}: {message}")
                    if success:
                        generated_count += 1
                        remaining.remove(file_num)
                    else:
                        all_success = False
            else:
                # Run sequentially
                for file_num in ready:
                    success, message = generate_single_file(
                        adw_id, file_num, force, context_mode, logger
                    )
                    logger.info(f"  {message}")

                    if success:
                        generated_count += 1
                        remaining.remove(file_num)
                    else:
                        all_success = False

    else:
        # Sequential execution
        logger.info("Using sequential execution")

        for file_num in files_to_generate:
            success, message = generate_single_file(
                adw_id, file_num, force, context_mode, logger
            )
            logger.info(f"  {message}")

            if success:
                generated_count += 1
            else:
                all_success = False
                # Continue with next file even if one fails

    logger.info(f"\n{'='*80}")
    logger.info(f"GENERATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Successfully generated: {generated_count}/{len(files_to_generate)}")

    return all_success


def main():
    """Main entry point for modular scoping."""
    load_dotenv()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Modular Scoping Agent")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--file-num", type=int, help="Generate specific file number (2-14)")
    parser.add_argument("--file-nums", help="Generate specific files (comma-separated, e.g., '6,11')")
    parser.add_argument("--all", action="store_true", help="Generate all missing files")
    parser.add_argument("--force", action="store_true", help="Regenerate even if file exists")
    parser.add_argument("--parallel", action="store_true", default=True, help="Enable parallel execution (default: true)")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("--context-mode", choices=["full", "summarized", "smart"], default="smart", help="Context management mode")

    args = parser.parse_args()

    # Determine parallel setting
    parallel = args.parallel and not args.no_parallel

    print(f"\n{'='*80}")
    print(f"MODULAR SCOPING PHASE")
    print(f"{'='*80}\n")
    print(f"ADW ID: {args.adw_id}")
    print(f"Context mode: {args.context_mode}")
    print(f"Parallel execution: {parallel}")

    # Load state
    state = ADWState.load_from_id(args.adw_id)
    if not state:
        print(f"\n[ERROR] No state found for ADW ID: {args.adw_id}")
        print("Run adw_discovery.py first!")
        sys.exit(1)

    # Check if discovery is complete
    discovery_brief_path = state.get("discovery.discovery_brief")
    if not discovery_brief_path:
        print("\n[ERROR] Discovery phase not complete")
        sys.exit(1)

    print(f"Discovery brief: {discovery_brief_path}\n")

    # Determine operation mode
    if args.file_num:
        # Generate single file
        success, message = generate_single_file(
            args.adw_id,
            args.file_num,
            args.force,
            args.context_mode,
            logger
        )
        print(f"\n{message}")
        sys.exit(0 if success else 1)

    elif args.file_nums:
        # Generate specific files
        file_nums = [int(n.strip()) for n in args.file_nums.split(',')]
        print(f"Generating files: {file_nums}\n")

        if parallel and len(file_nums) > 1:
            results = generate_files_parallel(
                args.adw_id, file_nums, args.force, args.context_mode, logger
            )
            all_success = all(success for success, _ in results.values())
        else:
            all_success = True
            for file_num in file_nums:
                success, message = generate_single_file(
                    args.adw_id, file_num, args.force, args.context_mode, logger
                )
                print(f"{message}")
                all_success = all_success and success

        sys.exit(0 if all_success else 1)

    elif args.all:
        # Generate all missing files
        success = generate_all_files(
            args.adw_id,
            parallel,
            args.force,
            args.context_mode,
            logger
        )
        sys.exit(0 if success else 1)

    else:
        print("[ERROR] Must specify --file-num, --file-nums, or --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
