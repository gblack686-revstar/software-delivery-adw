# Software Delivery ADW

> Complete AI Development Workflow - from client discovery through deployment and infrastructure management

---

## 🎯 What is This?

An enterprise-grade AI-powered workflow system that automates the entire software delivery lifecycle with AWS CDK integration:

**Discovery** → **Scoping** → **Planning** → **Development** → **Testing** → **Code Review** → **Deployment** → **Infrastructure Testing**

Each phase leverages specialized AI agents with automatic retry/resolution capabilities and isolated execution environments.

---

## ✨ Key Features

- **🔄 Worktree Isolation** - Parallel development with deterministic port allocation (15 concurrent workflows)
- **🤖 Automatic Retry Logic** - Intelligent test failure resolution (4 attempts unit, 2 attempts E2E)
- **📝 Code Review Automation** - Severity-based classification with auto-blocker resolution (3 attempts)
- **☁️ AWS CDK Integration** - Auto-generated infrastructure as code with config-driven approach
- **🔐 Configuration Management** - Unified config across local development and AWS Parameter Store
- **🚀 GitHub Integration** - Automatic PR creation, issue tracking, and progress updates
- **📦 State Management** - Comprehensive tracking with dual-storage pattern for backward compatibility

---

## 📋 Complete Workflow

```
1. Discovery Phase
   └─ Qualify leads, gather requirements
   └─ Output: Discovery Brief

2. Scoping Phase (AI-Powered Sequential Reasoning)
   └─ AI generates 13 files sequentially, each building on previous context
   └─ ML research (Exa API) before AWS service selection
   └─ Generate CDK configurations and construct templates
   └─ Output: Requirements, user flows, data models, ML research, AWS architecture, CDK config, cost estimate
   └─ Uses Claude Code CLI subprocess (5-10 min, ~$0.60-1.20/project)

3. Planning Phase
   └─ Create isolated worktree with unique ports
   └─ Generate PRD and agile stories
   └─ Set up development environment
   └─ Output: Worktree, PRD, sprint breakdown, stories

4. Development Phase
   └─ Implement features in isolated worktree
   └─ Auto-generate implementation plans from stories
   └─ Full git operations with branch management
   └─ Output: Code commits, feature implementations

5. Testing Phase
   └─ Unit tests with automatic failure resolution (4 retry attempts)
   └─ E2E tests with Playwright (2 retry attempts)
   └─ Test output analysis and fix generation
   └─ Output: Test reports, coverage metrics

6. Code Review Phase
   └─ Automated code review with severity classification
   └─ Automatic blocker resolution (3 retry attempts)
   └─ Tech debt and improvement tracking
   └─ Output: Review report, blocker fixes

7. Deployment Phase
   └─ Deploy CDK stacks to AWS
   └─ Parameter Store configuration setup
   └─ Automatic health checks and rollback
   └─ Output: Deployed infrastructure, stack outputs

8. Infrastructure Testing Phase
   └─ Validate CDK stack deployments
   └─ Resource-level health checks
   └─ Infrastructure validation
   └─ Output: Infrastructure test report
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** with [uv](https://github.com/astral-sh/uv)
- **Claude Code CLI** (required for scoping phase - [Install Guide](https://docs.claude.com/claude-code#installation))
  - Used for AI-powered sequential reasoning in scoping
  - Required for both local and cloud container deployments
  - Verify installation: `claude --version`
- **Node.js 18+** (for MCP servers)
- **Git** (for worktree management)
- **AWS CDK** (optional, for deployment)
- **API Keys:**
  - Anthropic API key (required)
  - Exa API key (required for ML research in scoping)
  - Brave Search API key (optional)
  - GitHub PAT (optional)
  - AWS credentials (optional, for deployment)

### 2. Setup

```bash
# Clone/navigate to this directory
cd software-delivery-adw

# Install Python dependencies
uv sync

# Copy environment template
cp .env.sample .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor

# Required environment variables:
# - ANTHROPIC_API_KEY: Your Claude API key
# - EXA_API_KEY: For ML research in scoping phase
# - CLAUDE_CODE_PATH: Path to Claude Code CLI (defaults to "claude")
#   - If Claude Code CLI is not in PATH, set full path here
#   - Example: CLAUDE_CODE_PATH=/usr/local/bin/claude

# Install AWS CDK (optional, for deployment)
npm install -g aws-cdk

# Configure AWS credentials (optional)
aws configure
```

### 3. Run Complete Workflow

**Phase 1: Discovery**

```bash
uv run adws/adw_discovery.py
# Generates unique workflow ID (e.g., abc12345)
```

**Phase 2: AI-Powered Scoping with Sequential Reasoning**

```bash
uv run adws/adw_scoping.py --adw-id abc12345
# Generates 13 AI-powered scoping files + CDK configurations
# Time: 5-10 minutes | Cost: ~$0.60-1.20 per project
```

**How It Works:**
- Uses Claude Code CLI as subprocess (works in local and cloud containers)
- Sequential AI reasoning: Each file builds on all previous context
- Files generated (2-14):
  1. Requirements Analysis → 2. User Flows → 3. Data Models → 4. Data Schema (ERD)
  5. **ML Research (uses Exa API)** → 6. AWS Native Analysis → 7. AWS Services
  8. Architecture Diagram → 9. CDK Constructs → 10. Security & RBAC
  11. Cost Estimate → 12. Validation Gates → 13. LLM Prompts
- **Key Innovation:** ML research happens BEFORE infrastructure selection (model requirements drive AWS service choices)
- See [docs/SCOPING_AI_MIGRATION.md](docs/SCOPING_AI_MIGRATION.md) for technical details

**Prerequisites:**
- Claude Code CLI installed and in PATH (verify: `claude --version`)
- ANTHROPIC_API_KEY in .env
- EXA_API_KEY in .env (for ML research)
- Discovery phase completed

**Troubleshooting:**
- Error "Claude Code CLI is not installed"? Check CLAUDE_CODE_PATH in .env
- Files missing Exa research? Verify EXA_API_KEY is set
- Generation fails? Check agent logs: `agents/{adw_id}/scoping/`

**Phase 3: Planning with Worktree Isolation**

```bash
uv run adws/adw_planning.py --adw-id abc12345 --sprints 4
# Creates isolated worktree at trees/abc12345/
# Allocates ports: Backend 9103, Frontend 9203 (example)
```

**Phase 4: Development in Worktree**

```bash
uv run adws/adw_develop.py --story-id STORY-001 --adw-id abc12345
# Implements feature in isolated worktree
# Auto-generates implementation plan
```

**Phase 5: Automated Testing**

```bash
uv run adws/adw_test.py --adw-id abc12345
# Runs unit tests (4 retry attempts with auto-resolution)
# Runs E2E tests (2 retry attempts with auto-resolution)
```

**Phase 6: Code Review**

```bash
uv run adws/adw_review.py --adw-id abc12345
# Automated code review
# Auto-resolves blockers (3 retry attempts)
```

**Phase 7: AWS Deployment**

```bash
# First, configure environment
uv run adws/adw_config.py --adw-id abc12345 --action sync --direction local_to_cloud

# Then deploy infrastructure
uv run adws/adw_deploy.py --adw-id abc12345 --environment dev
# Deploys CDK stacks to AWS
# Sets up Parameter Store
# Runs health checks
```

**Phase 8: Infrastructure Testing**

```bash
uv run adws/adw_test_infra.py --adw-id abc12345
# Validates deployed infrastructure
# Checks resource health
```

---

## 🎓 Simple Example: Complete 3-Story Project

### Example Project: Task Manager API

Let's build a simple Task Manager API with 3 user stories from discovery to deployment.

#### Discovery Prompt

Start the discovery phase with this simple prompt:

```
I need a simple Task Manager API that allows users to:
1. Create and manage tasks
2. Mark tasks as complete
3. List all tasks

Tech stack: Python FastAPI backend, PostgreSQL database, React frontend
Deploy to AWS
```

#### Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Task Manager API Workflow                     │
└─────────────────────────────────────────────────────────────────┘

Step 1: DISCOVERY
   Input: Project description above
   Command: uv run adws/adw_discovery.py
   Output: → ADW ID: abc12345
           → specs/abc12345/1_discovery_brief.md

Step 2: SCOPING (AI-Powered Sequential Reasoning)
   Command: uv run adws/adw_scoping.py --adw-id abc12345
   Output: → 13 AI-generated files (requirements → ML research → AWS → architecture)
           → ML research via Exa API (finds optimal models BEFORE infrastructure)
           → CDK configuration (RDS, ECS, S3, CloudFront)
           → Cost estimate and validation gates
   Time: ~5-10 minutes | Cost: ~$0.60-1.20

Step 3: PLANNING (3 stories, 1 sprint)
   Command: uv run adws/adw_planning.py --adw-id abc12345 --sprints 1
   Output: → Isolated worktree: trees/abc12345/
           → Ports: Backend 9103, Frontend 9203
           → PRD and sprint plan created

Step 4: DEVELOP STORY 1 - Create Tasks API
   Command: uv run adws/adw_develop.py --adw-id abc12345 --story-id STORY-001
   Output: → POST /api/tasks endpoint created
           → Database model implemented
           → Unit tests written
           → Committed to feature branch

Step 5: DEVELOP STORY 2 - Complete Tasks API
   Command: uv run adws/adw_develop.py --adw-id abc12345 --story-id STORY-002
   Output: → PATCH /api/tasks/:id endpoint created
           → Update logic implemented
           → Unit tests written
           → Committed to feature branch

Step 6: DEVELOP STORY 3 - List Tasks API
   Command: uv run adws/adw_develop.py --adw-id abc12345 --story-id STORY-003
   Output: → GET /api/tasks endpoint created
           → Filtering and pagination added
           → Unit tests written
           → Committed to feature branch

Step 7: TESTING (Automatic retry on failures)
   Command: uv run adws/adw_test.py --adw-id abc12345
   Output: → Unit tests: 15/15 passed ✓
           → E2E tests: 5/5 passed ✓
           → Coverage: 85%

Step 8: CODE REVIEW (Automatic blocker resolution)
   Command: uv run adws/adw_review.py --adw-id abc12345
   Output: → 0 blockers, 2 tech debt items
           → Review approved ✓

Step 9: CONFIGURATION
   Command: uv run adws/adw_config.py --adw-id abc12345 --action sync --direction local_to_cloud
   Output: → Config synced to AWS Parameter Store
           → Environment variables set

Step 10: DEPLOY TO AWS DEV
   Command: uv run adws/adw_deploy.py --adw-id abc12345 --environment dev
   Output: → VPC and networking deployed ✓
           → RDS PostgreSQL deployed ✓
           → ECS Fargate backend deployed ✓
           → S3 + CloudFront frontend deployed ✓
           → All health checks passed ✓

Step 11: INFRASTRUCTURE TESTING
   Command: uv run adws/adw_test_infra.py --adw-id abc12345
   Output: → All 4 stacks validated ✓
           → Security scan passed ✓
           → Infrastructure ready for staging ✓

┌─────────────────────────────────────────────────────────────────┐
│                         🎉 PROJECT COMPLETE                      │
│                                                                   │
│  Backend:  https://abc12345-dev-backend.aws-region.elb.com      │
│  Frontend: https://abc12345-dev.cloudfront.net                  │
│  Database: abc12345-dev.region.rds.amazonaws.com                │
│                                                                   │
│  Total Time: ~2-3 hours (mostly AI automation)                  │
│  Lines of Code: ~500 backend, ~300 frontend, ~200 tests        │
│  AWS Resources: VPC, RDS, ECS, S3, CloudFront, ALB             │
└─────────────────────────────────────────────────────────────────┘
```

#### Actual Commands to Run

```bash
# Step 1: Discovery
echo "I need a simple Task Manager API that allows users to:
1. Create and manage tasks
2. Mark tasks as complete
3. List all tasks

Tech stack: Python FastAPI backend, PostgreSQL database, React frontend
Deploy to AWS" | uv run adws/adw_discovery.py

# Save the ADW ID from output (e.g., abc12345)
export ADW_ID=abc12345

# Step 2: Scoping (generates 3 stories automatically)
uv run adws/adw_scoping.py --adw-id $ADW_ID

# Step 3: Planning (1 sprint for 3 stories)
uv run adws/adw_planning.py --adw-id $ADW_ID --sprints 1

# Step 4-6: Develop all 3 stories
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-001  # Create tasks
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-002  # Complete tasks
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-003  # List tasks

# Step 7: Testing (with auto-retry)
uv run adws/adw_test.py --adw-id $ADW_ID

# Step 8: Code Review (with auto-blocker resolution)
uv run adws/adw_review.py --adw-id $ADW_ID

# Step 9: Configuration
uv run adws/adw_config.py --adw-id $ADW_ID --action generate
uv run adws/adw_config.py --adw-id $ADW_ID --action sync --direction local_to_cloud

# Step 10: Deploy to AWS
uv run adws/adw_deploy.py --adw-id $ADW_ID --environment dev

# Step 11: Infrastructure Testing
uv run adws/adw_test_infra.py --adw-id $ADW_ID

# 🎉 Done! Your Task Manager API is live on AWS
```

#### What Gets Created

**Generated Files:**
```
specs/abc12345/
├── 1_discovery_brief.md          # Project requirements (from discovery)
├── 2_requirements_analysis.md    # AI-extracted technical requirements
├── 3_user_flows.yaml              # AI-generated user flows
├── 4_data_models.yaml             # AI-generated data entities
├── 5_data_schema.mmd              # ERD diagram (Mermaid)
├── 6_ml_research.md               # ML model research via Exa API
├── 7_aws_native_analysis.md       # AWS service analysis
├── 8_aws_services.yaml            # AWS resource specifications
├── 9_architecture.mmd             # System architecture diagram
├── 10_cdk_constructs.md           # CDK implementation guidance
├── 11_security_rbac.md            # Security and auth design
├── 12_cost_estimate.md            # AWS cost projections
├── 13_validation_gates.yaml       # Success criteria
├── 14_llm_prompts.yaml            # Agent configurations
└── cdk_config/
    ├── cdk_config.yaml            # Infrastructure config
    ├── construct_template.ts      # CDK TypeScript template
    └── setup_parameters.sh        # Parameter Store script

trees/abc12345/                    # Isolated worktree
├── backend/
│   ├── api/
│   │   └── tasks.py               # Task endpoints
│   ├── models/
│   │   └── task.py                # Task model
│   └── tests/
│       └── test_tasks.py          # Unit tests
└── frontend/
    └── src/
        └── components/
            └── TaskList.tsx       # Task list component

agents/abc12345/
└── adw_state.json                 # Workflow state tracking
```

**AWS Resources Created:**
- VPC with public/private subnets
- RDS PostgreSQL database (db.t3.micro)
- ECS Fargate cluster with backend container
- Application Load Balancer
- S3 bucket for frontend
- CloudFront distribution
- Parameter Store for configuration

#### Expected Timeline

- **Discovery:** 5 minutes (AI analysis)
- **Scoping:** 5-10 minutes (13 AI-generated files + CDK config via sequential reasoning)
- **Planning:** 5 minutes (worktree + PRD)
- **Development:** 30-45 minutes (3 stories)
- **Testing:** 10 minutes (with auto-retry)
- **Review:** 5 minutes (with auto-fixes)
- **Deployment:** 15-20 minutes (AWS resources)
- **Infrastructure Testing:** 5 minutes

**Total: ~90-120 minutes for complete working API on AWS**

#### Manual vs Automated Steps

Understanding what requires human input vs AI automation:

| Step | Type | Human Role | AI Agent Role |
|------|------|-----------|---------------|
| **1. Discovery** | 🟡 **Manual Input** | Provide project requirements via prompt | Analyzes requirements, qualifies lead, generates discovery brief |
| **2. Scoping** | 🟡 **Semi-Automated** | Review architecture, AWS services, cost estimates - approve before proceeding | Designs architecture, data models, user flows, generates CDK config, creates cost estimates |
| **3. Planning** | 🟢 **Fully Automated** | None (starts after scoping approval) | Creates isolated worktree, allocates ports, generates PRD and agile stories, sets up GitHub issue tracking |
| **4-6. Development** | 🟢 **Fully Automated** | None | Implements each story, writes code, creates tests, commits to feature branch |
| **7. Testing** | 🟢 **Fully Automated** | None | Runs unit tests, runs E2E tests, analyzes failures, auto-fixes up to 4 attempts (unit) and 2 attempts (E2E) |
| **8. Code Review** | 🟢 **Fully Automated** | None | Reviews code, classifies issues by severity, auto-resolves blockers (up to 3 attempts), posts review to GitHub |
| **9. Configuration** | 🟡 **Semi-Automated** | Review generated configs, edit secrets if needed | Generates config templates, validates schema, syncs to AWS Parameter Store |
| **10. Deployment** | 🔴 **Manual Approval** | Approve deployment to production (dev/staging can be auto) | Deploys CDK stacks, configures resources, runs health checks, handles rollback |
| **11. Infra Testing** | 🟢 **Fully Automated** | None | Validates infrastructure, checks resource health, runs security scans |

**Legend:**
- 🟢 **Fully Automated** - AI handles everything, zero human intervention required
- 🟡 **Semi-Automated** - AI does the work, human reviews/approves
- 🔴 **Manual Approval** - Human decision required (especially for production)

**Key Points:**
- **Step 1 (Discovery)** - You provide the initial project description
- **Step 2 (Scoping)** - AI generates architecture and AWS config, **you review and approve** before planning begins
- **Steps 3-8 are 100% automated** - AI handles planning, coding, testing, and review without human intervention
- **Step 9 (Configuration)** - AI generates everything, but you should review secrets/credentials before deploying
- **Step 10 (Deployment)** - AI can auto-deploy to dev/staging, but **production deployments should have manual approval** (use `--require-approval` flag)
- **Step 11 runs automatically** - Validates the deployed infrastructure

**Real-World Usage Pattern:**

```bash
# Morning: Provide requirements (1 minute)
echo "Your project description" | uv run adws/adw_discovery.py

# AI generates scoping (10 minutes)
export ADW_ID=abc12345  # From discovery output
uv run adws/adw_scoping.py --adw-id $ADW_ID

# Review scoping output (5-10 minutes)
# Check: specs/$ADW_ID/6_architecture.mmd
# Check: specs/$ADW_ID/5_aws_services.yaml
# Check: specs/$ADW_ID/cdk_config/cdk_config.yaml
# Approve cost estimates and architecture

# After approval, let AI work (60-90 minutes unattended)
# Steps 3-8 run automatically via script or cron
uv run adws/adw_planning.py --adw-id $ADW_ID --sprints 1
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-001
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-002
uv run adws/adw_develop.py --adw-id $ADW_ID --story-id STORY-003
uv run adws/adw_test.py --adw-id $ADW_ID
uv run adws/adw_review.py --adw-id $ADW_ID

# Afternoon: Review config and deploy (15 minutes)
# Review configuration
uv run adws/adw_config.py --adw-id $ADW_ID --action generate
nano specs/$ADW_ID/config/.env.example

# Deploy to dev (automatic)
uv run adws/adw_config.py --adw-id $ADW_ID --action sync --direction local_to_cloud
uv run adws/adw_deploy.py --adw-id $ADW_ID --environment dev
uv run adws/adw_test_infra.py --adw-id $ADW_ID

# Review dev deployment, then deploy to production (manual approval)
uv run adws/adw_deploy.py --adw-id $ADW_ID --environment production --require-approval
```

**What This Means:**
- **3 human touchpoints per project:**
  1. Initial requirements (1 min)
  2. Review scoping/architecture (5-10 min)
  3. Review and deploy (15 min)
- Between touchpoints, AI works unattended (no human intervention needed)
- Parallel workflows work independently - no conflicts, no manual coordination
- **Human time: ~25-30 minutes per project** (spread across the day)
- **AI time: ~90-120 minutes per project** (all automation)

---

## 📁 Directory Structure

```
software-delivery-adw/
├── .env                        # Your API keys (not committed)
├── .mcp.json                   # Active MCP config (auto-managed)
├── subagent_configs/           # Specialized MCP configs per agent
│   ├── mcp.discovery.json
│   ├── mcp.scoping.json
│   ├── mcp.planning.json
│   ├── mcp.developer.json
│   ├── mcp.test.json
│   ├── mcp.reviewer.json
│   └── mcp.deployer.json
├── claude_commands/commands/   # Claude Code slash commands (renamed from .claude to avoid OneDrive deletion)
│   ├── discover.md
│   ├── scope.md
│   ├── planning.md
│   ├── develop.md
│   ├── test.md
│   ├── review.md
│   ├── deploy.md
│   ├── test_infra.md
│   ├── config.md
│   ├── install_worktree.md
│   ├── resolve_failed_test.md
│   └── resolve_failed_e2e_test.md
├── adws/                       # Workflow scripts
│   ├── adw_modules/            # Shared utilities
│   │   ├── state.py            # State management with dual-storage
│   │   ├── git_ops.py          # Git automation
│   │   ├── worktree_ops.py     # Worktree and port management
│   │   ├── workflow_ops.py     # Workflow orchestration
│   │   ├── aws_cdk_helper.py   # CDK deployment utilities
│   │   ├── cdk_generator.py    # CDK config generation
│   │   ├── config_manager.py   # Configuration management
│   │   ├── data_types.py       # Pydantic models
│   │   ├── utils.py            # Helper functions
│   │   ├── github.py           # GitHub integration
│   │   └── agent.py            # Agent execution
│   ├── adw_discovery.py        # Phase 1: Discovery
│   ├── adw_scoping.py          # Phase 2: Scoping + CDK
│   ├── adw_planning.py         # Phase 3: Planning + Worktree
│   ├── adw_develop.py          # Phase 4: Development
│   ├── adw_test.py             # Phase 5: Testing
│   ├── adw_review.py           # Phase 6: Code Review
│   ├── adw_deploy.py           # Phase 7: AWS Deployment
│   ├── adw_test_infra.py       # Phase 8: Infrastructure Testing
│   └── adw_config.py           # Configuration Management
├── specs/                      # Generated specifications (per workflow)
│   └── {adw_id}/
│       ├── 1_discovery_brief.md          # Discovery phase output
│       ├── 2_requirements_analysis.md    # AI-generated (scoping)
│       ├── 3_user_flows.yaml              # AI-generated (scoping)
│       ├── 4_data_models.yaml             # AI-generated (scoping)
│       ├── 5_data_schema.mmd              # AI-generated (scoping)
│       ├── 6_ml_research.md               # AI-generated via Exa (scoping)
│       ├── 7_aws_native_analysis.md       # AI-generated (scoping)
│       ├── 8_aws_services.yaml            # AI-generated (scoping)
│       ├── 9_architecture.mmd             # AI-generated (scoping)
│       ├── 10_cdk_constructs.md           # AI-generated (scoping)
│       ├── 11_security_rbac.md            # AI-generated (scoping)
│       ├── 12_cost_estimate.md            # AI-generated (scoping)
│       ├── 13_validation_gates.yaml       # AI-generated (scoping)
│       ├── 14_llm_prompts.yaml            # AI-generated (scoping)
│       ├── config/             # Configuration management
│       │   ├── config.yaml
│       │   ├── config.dev.yaml
│       │   ├── config.staging.yaml
│       │   ├── config.production.yaml
│       │   ├── .env.example
│       │   └── config.schema.json
│       └── cdk_config/         # CDK configurations (auto-generated)
│           ├── cdk_config.yaml
│           ├── construct_template.ts
│           └── setup_parameters.sh
├── agents/                     # Agent execution state and outputs
│   └── {adw_id}/
│       ├── adw_state.json      # Persistent workflow state
│       └── logs/               # Execution logs
├── trees/                      # Isolated worktrees (git worktrees)
│   └── {adw_id}/
│       ├── .ports.env          # Port configuration
│       ├── .env.local          # Local environment variables
│       ├── backend/            # Backend code
│       ├── frontend/           # Frontend code
│       └── plans/              # Implementation plans
└── projects/                   # Generated code (optional)
    └── {project_name}/
```

---

## 🔧 Advanced Features

### Worktree Isolation

Each workflow gets an isolated git worktree with deterministic port allocation:

- **Backend Ports:** 9100-9114 (15 concurrent workflows)
- **Frontend Ports:** 9200-9214
- **Port Calculation:** `hash(adw_id) % 15 + 9100`

Example:
```bash
# ADW ID: abc12345 → Backend: 9103, Frontend: 9203
# ADW ID: def67890 → Backend: 9107, Frontend: 9207
```

**Benefits:**
- ✅ No port conflicts between workflows
- ✅ Parallel development on same codebase
- ✅ Clean isolation of feature branches
- ✅ Easy environment management

### Automatic Retry Logic

Intelligent failure resolution with configurable retry attempts:

**Unit Tests:** 4 retry attempts
```python
# Automatic test failure analysis
# Fix generation based on error messages
# Code modification and re-test
# Max 4 iterations before reporting failure
```

**E2E Tests:** 2 retry attempts
```python
# Screenshot analysis for visual debugging
# Browser log examination
# Selector and timing fixes
# Max 2 iterations (higher cost)
```

**Code Review Blockers:** 3 retry attempts
```python
# Severity classification (blocker, tech_debt, skippable)
# Automatic blocker resolution
# Re-review after fixes
# Max 3 iterations
```

### Configuration Management

Unified configuration across local development and AWS:

**Three Layers:**
1. **Worktree Config** - `.ports.env`, `.env.local`
2. **Project Config** - `config.yaml`, `config.{env}.yaml`
3. **Cloud Config** - AWS Parameter Store

**Features:**
- ✅ JSON schema validation
- ✅ Environment templates (`.env.example`)
- ✅ Local ↔ Cloud synchronization
- ✅ Secret detection and masking
- ✅ Type inference and validation

**Usage:**
```bash
# Generate templates
uv run adws/adw_config.py --adw-id abc123 --action generate

# Validate configuration
uv run adws/adw_config.py --adw-id abc123 --action validate

# Sync to AWS
uv run adws/adw_config.py --adw-id abc123 --action sync --direction local_to_cloud
```

### AWS CDK Integration

Auto-generated infrastructure as code:

**During Scoping:**
- Analyzes AWS service requirements
- Generates `cdk_config.yaml`
- Creates CDK construct templates
- Generates Parameter Store setup script

**During Deployment:**
- Deploys stacks to AWS
- Configures Parameter Store
- Runs health checks
- Automatic rollback on failure

**Multi-Environment Support:**
- Dev environment (cost-optimized)
- Staging environment (production-like)
- Production environment (full redundancy)

### State Management

Comprehensive tracking with dual-storage pattern:

**Core Data (Pydantic):**
- ADW ID, worktree path, branch name
- Port allocations
- Infrastructure configuration
- CDK stack information

**Extended Data (Phases):**
- Discovery, scoping, planning phase data
- Development, testing, review phase data
- Deployment and infrastructure testing data

**State File:** `agents/{adw_id}/adw_state.json`

---

## 🎨 GitHub Integration

Automatic GitHub integration throughout the workflow:

**Planning Phase:**
- Creates feature branch
- Opens pull request
- Posts planning summary

**Development Phase:**
- Commits feature implementations
- Pushes to remote
- Updates PR with progress

**Testing Phase:**
- Posts test results to PR
- Reports failures with details
- Updates on retry attempts

**Code Review Phase:**
- Posts review findings to PR
- Reports blocker resolution
- Updates review status

**Deployment Phase:**
- Posts deployment status
- Links to deployed infrastructure
- Reports health check results

**Usage with GitHub Issue:**
```bash
# All commands support --issue-number
uv run adws/adw_planning.py --adw-id abc123 --issue-number 42
uv run adws/adw_develop.py --adw-id abc123 --story-id STORY-001 --issue-number 42
uv run adws/adw_test.py --adw-id abc123 --issue-number 42
```

---

## 📚 Documentation

### Slash Commands
All workflows have detailed Claude Code documentation in `claude_commands/commands/` (renamed from `.claude` to prevent OneDrive/antivirus deletion):

- **discover.md** - Discovery workflow
- **scope.md** - Scoping with CDK generation
- **planning.md** - Planning with worktree isolation
- **develop.md** - Story implementation
- **test.md** - Automated testing with retry logic
- **review.md** - Code review automation
- **deploy.md** - AWS deployment
- **test_infra.md** - Infrastructure testing
- **config.md** - Configuration management
- **install_worktree.md** - Worktree environment setup
- **resolve_failed_test.md** - Test failure resolution
- **resolve_failed_e2e_test.md** - E2E test resolution

### Module Documentation
Core modules in `adws/adw_modules/`:

- **state.py** - Workflow state management
- **git_ops.py** - Git automation functions
- **worktree_ops.py** - Worktree and port management
- **workflow_ops.py** - Workflow orchestration
- **aws_cdk_helper.py** - CDK deployment utilities
- **cdk_generator.py** - CDK config generation
- **config_manager.py** - Configuration management
- **data_types.py** - Pydantic models for type safety
- **utils.py** - Helper functions
- **github.py** - GitHub API integration
- **agent.py** - Agent execution framework

### Testing

See [TESTING.md](./TESTING.md) for comprehensive testing documentation.

**Quick Start:**
```bash
# Run all integration tests (23 tests)
pytest tests/integration/ -v

# Run module tests only (12 tests)
pytest tests/integration/test_workflow.py -v

# Run E2E workflow tests only (11 tests)
pytest tests/integration/test_e2e_workflow.py -v
```

**Test Coverage:**
- ✅ State management and persistence
- ✅ Port allocation (deterministic + uniqueness)
- ✅ Configuration management
- ✅ Git operations
- ✅ Pydantic data types
- ✅ Complete workflow execution (discovery → deployment)

**What's Tested:**
- 12 module integration tests (state, ports, config, git, data types)
- 11 end-to-end workflow tests (complete workflow from discovery to deployment readiness)
- Automatic cleanup (no test artifacts left behind)
- Stub-based testing (no external dependencies required)

---

## 🎯 Use Cases

### Parallel Development

Multiple developers can work on the same codebase simultaneously:

```bash
# Developer A: Infrastructure work
uv run adws/adw_planning.py --adw-id infra-work --sprints 2
uv run adws/adw_develop.py --adw-id infra-work --story-id STORY-001

# Developer B: Auth feature (different worktree, different ports)
uv run adws/adw_planning.py --adw-id auth-feature --sprints 2
uv run adws/adw_develop.py --adw-id auth-feature --story-id STORY-001

# No conflicts! Each workflow has:
# - Isolated worktree (trees/infra-work vs trees/auth-feature)
# - Unique ports (9100/9200 vs 9101/9201)
# - Separate branch (plan-2sprint-infra-work vs plan-2sprint-auth-feature)
```

### Multi-Environment Deployment

Deploy to dev, staging, and production:

```bash
# Dev deployment
uv run adws/adw_deploy.py --adw-id abc123 --environment dev
uv run adws/adw_test_infra.py --adw-id abc123

# Staging deployment (after dev validates)
uv run adws/adw_deploy.py --adw-id abc123 --environment staging
uv run adws/adw_test_infra.py --adw-id abc123

# Production deployment (after staging validates)
uv run adws/adw_deploy.py --adw-id abc123 --environment production --require-approval
uv run adws/adw_test_infra.py --adw-id abc123
```

### Configuration Synchronization

Sync configuration across environments:

```bash
# Generate templates from scoping
uv run adws/adw_config.py --adw-id abc123 --action generate

# Edit local configuration
nano trees/abc123/.env.local

# Validate before deployment
uv run adws/adw_config.py --adw-id abc123 --action validate

# Sync to AWS for production
uv run adws/adw_config.py --adw-id abc123 --action sync --direction local_to_cloud --environment production
```

---

## 🤝 Contributing

This system is designed to be extensible:

- **Add New Workflows** - Create new phase scripts in `adws/`
- **Custom Agents** - Define new agent types in `claude_commands/commands/`
- **MCP Servers** - Add new MCP configurations in `subagent_configs/`
- **CDK Constructs** - Extend CDK templates in scoping phase
- **Configuration Schemas** - Define custom validation rules

---

## 🔍 Troubleshooting

### Claude Code CLI Issues

**Error:** `Claude Code CLI is not installed. Expected at: claude`

This means the scoping phase cannot find the Claude Code CLI executable.

**Solution 1: Verify Installation**
```bash
# Check if Claude Code is installed
claude --version

# If not found, install from:
# https://docs.claude.com/claude-code#installation
```

**Solution 2: Set CLAUDE_CODE_PATH**
```bash
# If Claude Code is installed but not in PATH
# Find the installation location:
which claude  # Linux/Mac
where claude  # Windows

# Add to .env:
CLAUDE_CODE_PATH=/full/path/to/claude
```

**Solution 3: Check PATH (for cloud containers)**
```dockerfile
# Ensure Claude Code CLI is in PATH in your Dockerfile
ENV PATH="/usr/local/bin:${PATH}"
RUN npm install -g @anthropic-ai/claude-code
```

**Common Locations:**
- **macOS/Linux:** `/usr/local/bin/claude` or `~/.local/bin/claude`
- **Windows:** `C:\Users\{user}\AppData\Roaming\npm\claude.cmd`
- **Docker:** `/usr/local/bin/claude`

**Check Agent Logs:**
If scoping fails, check detailed logs:
```bash
# View agent execution logs
cat agents/{adw_id}/scoping/file_*_*.jsonl

# Convert to readable JSON
python -m json.tool agents/{adw_id}/scoping/file_2_requirements_analysis.jsonl
```

### Worktree Issues

**Error:** `Worktree already exists`
```bash
# Remove existing worktree
git worktree remove trees/abc12345
```

**Error:** `Port already in use`
```bash
# System automatically finds alternative ports
# Check .ports.env in worktree for actual allocated ports
```

### Testing Issues

**Error:** `Tests failing after 4 attempts`
```bash
# Check test output in logs
# Review fix attempts in commit history
# May require manual intervention for complex issues
```

### Deployment Issues

**Error:** `CDK configuration not found`
```bash
# Ensure scoping phase completed
uv run adws/adw_scoping.py --adw-id abc123
```

**Error:** `AWS credentials not configured`
```bash
# Configure AWS CLI
aws configure
```

### Configuration Issues

**Error:** `Validation failed`
```bash
# Check validation errors
uv run adws/adw_config.py --adw-id abc123 --action validate

# Fix missing required fields
uv run adws/adw_config.py --adw-id abc123 --action set --key MISSING_KEY --value value
```

---

## 📈 Performance

### Context Management

Specialized subagent architecture for optimal performance:

- **Main orchestrator:** Minimal context, fast reasoning
- **Specialized agents:** Load only required MCP tools
- **Context cleanup:** Subagent context discarded after execution
- **Result aggregation:** Efficient data flow between agents

### Retry Optimization

Smart retry strategies to balance success rate and cost:

- **Unit tests:** 4 attempts (low cost, high success rate)
- **E2E tests:** 2 attempts (high cost, focused resolution)
- **Code review:** 3 attempts (balanced approach)

### Port Allocation

Deterministic port allocation for 15 concurrent workflows:

- **No port scanning:** Direct calculation from ADW ID
- **Fallback mechanism:** Automatic alternative if port in use
- **No conflicts:** Guaranteed unique ports per workflow

---

## 📄 License

MIT - Use freely for your projects!

---

## 🚀 Getting Help

**Resources:**
- [Claude Code Docs](https://docs.claude.com/claude-code)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [uv Documentation](https://github.com/astral-sh/uv)

**Common Issues:**
- Phase script errors? Check `agents/{adw_id}/adw_state.json`
- MCP server issues? Verify API keys in `.env`
- AWS deployment issues? Check CloudFormation console
- Git worktree issues? Use `git worktree list` and `git worktree remove`

---

**Built with ❤️ for efficient software delivery**
