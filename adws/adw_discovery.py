#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml"]
# ///

"""Discovery Agent - Client requirements discovery and qualification.

Usage:
    uv run adw_discovery.py --deal-info "..." --adw-id abc123

    Or interactive:
    uv run adw_discovery.py
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState, make_adw_id


def main():
    """Main entry point for discovery agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Discovery Agent")
    parser.add_argument("--deal-info", help="Client/deal information")
    parser.add_argument("--adw-id", help="Workflow ID (auto-generated if not provided)")
    args = parser.parse_args()

    # Get or create ADW ID
    adw_id = args.adw_id or make_adw_id()
    print(f"\n>>> Starting Discovery Phase")
    print(f"ADW ID: {adw_id}")

    # Initialize state
    state = ADWState(adw_id)
    state.update_phase("discovery", started=True)
    state.save()

    # Get deal info
    if args.deal_info:
        deal_info = args.deal_info
    else:
        print("\n" + "="*60)
        print("DISCOVERY AGENT - CLIENT INFORMATION")
        print("="*60)
        print("\nPlease provide information about the client/deal:")
        print("(Paste all available info, then press Ctrl+D or Ctrl+Z)")
        print()
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        deal_info = "\n".join(lines)

    # Save deal info to state
    state.update_phase("discovery", deal_info=deal_info)
    state.save()

    # Create specs directory
    specs_dir = Path(f"specs/{adw_id}")
    specs_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Call Claude Code with /discover command
    # For now, create a template brief
    brief_path = specs_dir / "1_discovery_brief.md"
    print(f"\nCreating discovery brief at: {brief_path}")

    with open(brief_path, 'w', encoding='utf-8') as f:
        f.write(f"""# Discovery Brief

**ADW ID:** {adw_id}
**Phase:** Discovery

## Executive Summary

[To be completed after client discovery call - provide 1-2 paragraph summary of the project]

## Client Information

{deal_info}

## Discovery Questionnaire

### Objectives & Outcomes

* What are the precise success metrics for the project (quantitative and qualitative)?
* What defines "done" for MVP vs. full production launch?
* What is the expected business impact and ROI?
* What level of explainability or auditability is required?
* How will stakeholders evaluate project success?

### Users & Workflows

* Who are the primary users and their roles?
* What is the current workflow and what are the pain points?
* What existing tools need to integrate with this solution?
* How frequently will the system be used (requests/day, users/week)?
* What are the user training and adoption requirements?

### Data & Integrations

* What is the typical data volume (per day/week/month)?
* Where is data currently stored and in what formats?
* Is data labeled/annotated? What is the quality level?
* What input/output formats are required?
* Which existing systems need API or file-based integration?
* Are there data migration needs from legacy systems?

### Architecture & Scalability

* What is the expected throughput during POC vs. production?
* Should this use single or multi-account AWS structure?
* Are there data residency or regional requirements?
* Is processing real-time or batch-based?
* What are scalability projections (6 months, 1 year, 2 years)?

### Technical Requirements

* What is the preferred tech stack or are there constraints?
* What are the performance requirements (latency, throughput)?
* Are GPUs or specialized hardware (Inferentia, Trainium) required?
* What are containerization preferences (ECS, EKS, Lambda)?
* What database types are needed (RDS, DynamoDB, Aurora, DocumentDB)?
* Are there caching or CDN needs?

### Security, Compliance & Governance

* What type of data sensitivity applies (PII, PHI, financial, proprietary)?
* Which compliance frameworks are required (HIPAA, SOC2, GDPR, ISO)?
* What authentication/authorization is needed (SSO, MFA, Okta, Cognito)?
* What encryption requirements exist (at-rest, in-transit, KMS CMKs)?
* What audit logging and monitoring is required?
* Are there cross-account or third-party access needs?

### QA & Validation

* What testing strategy is required (unit, integration, E2E)?
* What are the acceptance criteria and quality gates?
* What performance benchmarks must be met?
* How will results be validated against ground truth?
* Is QA manual review, automated, or hybrid?

### Operations & DevOps

* What CI/CD pipeline capabilities are needed?
* What IaC preference exists (CDK, Terraform, CloudFormation)?
* What monitoring and observability tools are required?
* What alerting and incident response processes are needed?
* What are backup and disaster recovery requirements (RPO, RTO)?
* What is the version control and deployment strategy?

### Cost & Budget

* What is the budget ceiling and project duration?
* What is the acceptable cost per transaction/user/request?
* What cost optimization strategies should be considered?
* How should costs be allocated and tracked?
* What is the acceptable cost variance?

### Risks & Dependencies

* What external dependencies and integrations are critical?
* What data availability or quality risks exist?
* What technical complexity or unknowns are present?
* What are timeline constraints and critical dates?
* What resource constraints exist (team, budget, infrastructure)?
* What compliance or security blockers might arise?

## Call Agenda (60-75 min)

1. **Introductions & Objectives (5 min)** – Confirm goals and success criteria
2. **Current State Review (10 min)** – Understand existing workflow and pain points
3. **Data & Technical Landscape (15 min)** – Discuss data, integrations, and tech stack
4. **Requirements Deep Dive (15 min)** – Define functional and non-functional requirements
5. **Architecture & Compliance (15 min)** – Review AWS environment and security needs
6. **Next Steps & Timeline (10 min)** – Align on milestones, ownership, and follow-ups

## Assumptions & Risks to Validate

[To be completed during discovery - list key assumptions, technical risks, compliance concerns, and resource/timeline risks]

## Recommendation

**Qualification Score:** [TBD]/100
**Proceed to Scoping:** [Yes/No - to be determined after questionnaire completion]

**Reasoning:**
[To be completed after analyzing questionnaire responses]

## Next Steps

1. **Complete this questionnaire** with client responses during discovery call
2. **Conduct client research** on industry, competitors, and market position
3. **Validate assumptions and risks** identified above
4. **Update recommendation** based on findings
5. **When qualified**, proceed to scoping:
   ```bash
   uv run adws/adw_scoping.py --adw-id {adw_id}
   ```

---

*This questionnaire is ready for your discovery call. To use Claude Code for AI-powered discovery:*

1. Install Claude Code CLI
2. Set ANTHROPIC_API_KEY in .env
3. Run: `claude --prompt "$(cat .claude/commands/discover.md)" --args "{adw_id}"`

Or integrate with the SubagentExecutor to automatically use Brave Search MCP for research.
""")

    # Update state
    state.update_phase(
        "discovery",
        completed=False,
        discovery_brief=str(brief_path)
    )
    state.save()

    print(f"\n[SUCCESS] Discovery brief template created!")
    print(f"\nReview: {brief_path}")
    print(f"\nNext: uv run adws/adw_scoping.py --adw-id {adw_id}")


if __name__ == "__main__":
    main()
