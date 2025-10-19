#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml"]
# ///

"""Scoping Agent - AI-powered sequential reasoning for technical architecture.

This script generates comprehensive scoping documentation using Claude Code
to reason through each aspect sequentially, building context as it progresses.

Usage:
    uv run adw_scoping.py --adw-id abc123 [--context "additional info"]
"""

import argparse
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
import logging

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


def generate_scoping_file(
    file_config,
    adw_id,
    specs_dir,
    accumulated_context,
    agent_output_dir
):
    """
    Generate a single scoping file using Claude Code agent.

    Args:
        file_config: File configuration from scoping_instructions.yaml
        adw_id: Workflow ID
        specs_dir: Path to specs directory
        accumulated_context: Context from all previous files
        agent_output_dir: Directory for agent output logs

    Returns:
        tuple: (success: bool, file_content: str)
    """
    file_num = file_config['number']
    filename = file_config['filename']
    title = file_config['title']
    instructions = file_config['instructions']

    print(f"\n>>> Generating File {file_num}: {filename}")
    print(f"    {title}")

    # Build prompt for Claude Code agent
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
        agent_name="scoping",
        model="sonnet",
        dangerously_skip_permissions=True,
        output_file=str(output_file),
        working_dir=str(Path.cwd())
    )

    # Call Claude Code agent with retry logic
    print(f"    Calling Claude Code agent...")
    response = prompt_claude_code_with_retry(request, max_retries=2)

    if not response.success:
        print(f"    [ERROR] Failed to generate {filename}")
        print(f"    Error: {response.output}")
        return False, ""

    print(f"    [OK] Generated {filename}")

    # Extract file content from response
    file_content = response.output.strip()

    # Write file to specs directory
    file_path = specs_dir / f"{file_num}_{filename}"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    return True, file_content


def main():
    """Main entry point for AI-powered scoping agent."""
    load_dotenv()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="AI-Powered Scoping Agent")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--context", help="Additional context (transcripts, Miro boards, etc.)")
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"AI-POWERED SCOPING PHASE")
    print(f"{'='*80}\n")
    print(f"ADW ID: {args.adw_id}")
    print(f"Approach: Sequential Claude reasoning (14 files)")

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

    # Update state
    state.update_phase("scoping", started=True)
    if args.context:
        state.update_phase("scoping", additional_context=args.context)
    state.save()

    # Create output directories
    specs_dir = Path(f"specs/{args.adw_id}")
    specs_dir.mkdir(parents=True, exist_ok=True)

    agent_output_dir = Path(f"agents/{args.adw_id}/scoping")
    agent_output_dir.mkdir(parents=True, exist_ok=True)

    # Load scoping instructions
    print(f"Loading scoping instructions...")
    config = load_scoping_instructions()
    files_config = config['files']
    print(f"[OK] Loaded instructions for {len(files_config)} files\n")

    # Read discovery brief to start context accumulation
    discovery_brief = read_file_safe(discovery_brief_path)

    # Check if project file exists (e.g., projects/theragraph.md)
    project_file = Path(f"projects/{args.adw_id}.md")
    project_context = ""
    if project_file.exists():
        project_context = read_file_safe(project_file)
        print(f"[INFO] Found project file: {project_file}")
        print(f"[INFO] Including project context in scoping\n")

    # Initialize accumulated context with discovery brief and project file
    accumulated_context = f"""# Project Context

{project_context if project_context else "No project file provided."}

# Discovery Brief (File 1)

{discovery_brief}
"""

    # Track generated files
    generated_files = {}
    successful_files = 0
    failed_files = 0

    print(f"{'='*80}")
    print(f"SEQUENTIAL FILE GENERATION")
    print(f"{'='*80}")

    # Generate each scoping file sequentially
    for file_config in files_config:
        file_num = file_config['number']
        filename = file_config['filename']

        success, file_content = generate_scoping_file(
            file_config=file_config,
            adw_id=args.adw_id,
            specs_dir=specs_dir,
            accumulated_context=accumulated_context,
            agent_output_dir=agent_output_dir
        )

        if success:
            successful_files += 1
            generated_files[filename] = str(specs_dir / f"{file_num}_{filename}")

            # Add this file's content to accumulated context for next file
            accumulated_context += f"\n\n# {file_config['title']} (File {file_num})\n\n{file_content}"
        else:
            failed_files += 1
            print(f"    [WARNING] Skipping {filename} due to generation error")

    print(f"\n{'='*80}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"Successful: {successful_files}/{len(files_config)}")
    if failed_files > 0:
        print(f"Failed: {failed_files}/{len(files_config)}")

    # Update state with generated files
    state.update_phase(
        "scoping",
        completed=(failed_files == 0),
        **{k.replace('.', '_'): v for k, v in generated_files.items()}
    )
    state.save()

    # Generate CDK configurations (from existing adw_scoping.py logic)
    print(f"\n{'='*80}")
    print(f"CDK CONFIGURATION GENERATION")
    print(f"{'='*80}\n")

    try:
        aws_services_path = specs_dir / "8_aws_services.yaml"
        if not aws_services_path.exists():
            raise FileNotFoundError(f"AWS services file not found: {aws_services_path}")

        cdk_config_dir = specs_dir / "cdk_config"
        cdk_config_dir.mkdir(exist_ok=True)

        # Generate CDK config YAML
        cdk_config_path = cdk_config_dir / "cdk_config.yaml"
        generated_constructs = generate_cdk_config_yaml(
            aws_services_yaml_path=str(aws_services_path),
            output_path=str(cdk_config_path),
            logger=logger
        )
        print(f"   [OK] Generated CDK config: {Path(cdk_config_path).name}")

        # Generate construct template
        construct_template_path = cdk_config_dir / "construct_template.ts"
        generate_cdk_construct_template(
            cdk_config_path=str(cdk_config_path),
            output_path=str(construct_template_path),
            logger=logger
        )
        print(f"   [OK] Generated construct template: {Path(construct_template_path).name}")

        # Generate parameter store script
        param_script_path = cdk_config_dir / "setup_parameters.sh"
        generate_parameter_store_script(
            cdk_config_path=str(cdk_config_path),
            prefix=f"/sdaw/{args.adw_id}/dev",
            output_dir=str(cdk_config_dir),
            logger=logger
        )
        print(f"   [OK] Generated Parameter Store script: {Path(param_script_path).name}")

        # Create infrastructure config
        infra_config = InfrastructureConfig(
            environment="dev",
            region="us-east-1",
            resource_prefix=f"{args.adw_id}-dev",
            parameter_store_prefix=f"/sdaw/{args.adw_id}/dev",
            secrets_manager_prefix=f"sdaw/{args.adw_id}/dev",
            cdk_config_path=str(cdk_config_path),
            cdk_output_dir=str(cdk_config_dir)
        )

        state.update_infrastructure_config(infra_config)
        state.update_phase(
            "scoping",
            cdk_config_dir=str(cdk_config_dir),
            cdk_constructs=generated_constructs,
            param_script=str(param_script_path)
        )
        state.save()

        print(f"\n[SUCCESS] CDK configurations generated!")
        print(f"CDK config directory: {cdk_config_dir}")

    except Exception as e:
        print(f"\n[WARNING] Could not generate CDK config: {e}")
        print("CDK config can be generated manually later.")

    # Final summary
    print(f"\n{'='*80}")
    print(f"SCOPING COMPLETE")
    print(f"{'='*80}\n")
    print(f"Files generated: {successful_files}")
    print(f"Output directory: {specs_dir}")
    print(f"Agent logs: {agent_output_dir}")
    print(f"\nGenerated files:")
    for filename, path in sorted(generated_files.items()):
        print(f"  - {Path(path).name}")

    if failed_files == 0:
        print(f"\n[SUCCESS] All scoping files generated successfully!")
        print(f"\nNext: uv run adws/adw_planning.py --adw-id {args.adw_id}")
    else:
        print(f"\n[WARNING] {failed_files} file(s) failed to generate")
        print(f"Review agent logs in: {agent_output_dir}")


if __name__ == "__main__":
    main()
