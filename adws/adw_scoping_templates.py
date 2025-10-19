#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pyyaml"]
# ///

"""Scoping Agent - Technical requirements and architecture design.

Usage:
    uv run adw_scoping.py --adw-id abc123 [--context "additional info"]
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.state import ADWState
from adws.adw_modules.cdk_generator import (
    generate_cdk_config_yaml,
    generate_cdk_construct_template,
    generate_parameter_store_script
)
from adws.adw_modules.data_types import InfrastructureConfig
import logging


def main():
    """Main entry point for scoping agent."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Scoping Agent")
    parser.add_argument("--adw-id", required=True, help="Workflow ID")
    parser.add_argument("--context", help="Additional context (transcripts, Miro boards, etc.)")
    args = parser.parse_args()

    print(f"\n>>> Starting Scoping Phase")
    print(f"ADW ID: {args.adw_id}")

    # Load state
    state = ADWState.load_from_id(args.adw_id)
    if not state:
        print(f"❌ Error: No state found for ADW ID: {args.adw_id}")
        print("Run adw_discovery.py first!")
        sys.exit(1)

    # Check if discovery is complete
    discovery_brief = state.get("discovery.discovery_brief")
    if not discovery_brief:
        print("❌ Error: Discovery phase not complete")
        sys.exit(1)

    print(f"Discovery brief: {discovery_brief}")

    # Update state
    state.update_phase("scoping", started=True)
    if args.context:
        state.update_phase("scoping", additional_context=args.context)
    state.save()

    # Create output files
    specs_dir = Path(f"specs/{args.adw_id}")

    # Create template files
    files_to_create = [
        ("2_ml_research.md", f"""# ML/AI Research Summary

**ADW ID:** {args.adw_id}

## Use Case Classification

- Problem type: [To be determined - Classification / Regression / Segmentation / Generation / etc.]
- Domain: [To be determined - Computer Vision / NLP / Time Series / Recommendation / etc.]

## Recommended Models

### Primary Model Recommendation
- **Model:** [To be researched using Exa]
- **Justification:** [Why this model fits the use case]
- **Pre-trained options:** [HuggingFace link / AWS Marketplace / etc.]
- **Performance benchmarks:** [Accuracy/F1/mAP on similar datasets]
- **Resource requirements:** [GPU type, memory, training time estimates]

### Alternative Models
1. **Model 2:** [To be researched]
2. **Model 3:** [To be researched]

## Data Science Techniques

### Data Preprocessing
- [Technique 1]: Purpose and implementation
- [Technique 2]: Purpose and implementation

### Feature Engineering
- [Approach 1]
- [Approach 2]

### Data Augmentation
- [Strategy 1]
- [Strategy 2]

## Training Infrastructure

### Recommended Setup
- **Training:** [SageMaker / Self-managed on EC2]
- **Instance type:** [ml.g5.xlarge / p4d.24xlarge / etc.]
- **Distributed training:** [Yes/No, strategy if yes]

### Inference Setup
- **Endpoint type:** [Real-time / Serverless / Batch]
- **Instance type:** [ml.g5.xlarge / Lambda / etc.]
- **Optimization:** [Quantization / Pruning / etc.]

## MLOps Strategy

### Experiment Tracking
- Tool: [SageMaker Experiments / MLflow / Weights & Biases]

### Model Registry
- Strategy: [SageMaker Model Registry / Custom]

### Monitoring
- Metrics to track: [Data drift / Model performance / Latency]
- Tools: [SageMaker Model Monitor / Custom CloudWatch]

### Retraining Pipeline
- Trigger: [Schedule / Performance degradation / Data drift]
- Frequency: [Weekly / Monthly / On-demand]

## Key Findings from Research

### Academic Papers
1. [Use Exa to find relevant papers]

### Industry Implementations
1. [Use Exa to find case studies]

### Open Source Models
1. [Research on HuggingFace, GitHub, AWS Marketplace]

## Risks & Considerations
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

## Next Steps
1. Use Exa to research state-of-the-art models for this use case
2. Validate model selection with stakeholders
3. Set up proof-of-concept with recommended model
4. Evaluate on sample dataset

---

*To populate this with AI research, use Claude Code with Exa MCP:*
```bash
claude --mcp-config subagent_configs/mcp.scoping.json --prompt "Research ML/AI models for [use case]"
```
"""),
        ("3_user_flows.yaml", """# User Flows

user_flows:
  - flow_id: UF-001
    name: "Example User Flow"
    persona: "End User"
    description: "Description of the flow"
    steps:
      - step: 1
        action: "User action"
        expected: "Expected result"
    error_cases:
      - case: "Error scenario"
        handling: "How to handle"
"""),
        ("4_data_models.yaml", """# Data Models

entities:
  - name: User
    table: users
    description: "User entity"
    fields:
      - name: id
        type: uuid
        primary_key: true
        required: true
      - name: email
        type: string
        max_length: 255
        unique: true
        required: true
    sample_data:
      - id: "550e8400-e29b-41d4-a716-446655440000"
        email: "user@example.com"
"""),
        ("5a_aws_native_analysis.md", f"""# AWS-Native Service Analysis

**ADW ID:** {args.adw_id}
**Preference:** AWS-native services to minimize integration complexity

## Service Selection Summary

| Capability | AWS-Native Service | Status | Integration Complexity |
|------------|-------------------|--------|----------------------|
| Compute | Lambda | NATIVE | None - Fully integrated |
| Database | RDS PostgreSQL | NATIVE | None - Fully integrated |
| Authentication | Cognito | NATIVE | None - Fully integrated |
| Storage | S3 | NATIVE | None - Fully integrated |
| Caching | ElastiCache | NATIVE | None - Fully integrated |
| Message Queue | SQS | NATIVE | None - Fully integrated |
| ML/AI | SageMaker | NATIVE | None - Fully integrated |
| Monitoring | CloudWatch | NATIVE | None - Fully integrated |

## Native AWS Services (SELECTED)

### 1. Compute - AWS Lambda
- **Purpose:** Serverless API backend
- **Why selected:** No server management, auto-scaling, pay-per-use
- **Integration benefits:**
  - IAM role-based permissions
  - CloudWatch Logs integration
  - VPC connectivity
  - X-Ray tracing
- **Managed aspects:** Patching, scaling, high availability

### 2. Database - Amazon RDS (PostgreSQL)
- **Purpose:** Relational database for application data
- **Why selected:** Managed PostgreSQL, automated backups, point-in-time recovery
- **Integration benefits:**
  - IAM database authentication
  - CloudWatch monitoring
  - Secrets Manager for credentials
  - VPC security groups
- **Managed aspects:** Patching, backups, failover

### 3. Authentication - Amazon Cognito
- **Purpose:** User authentication and authorization
- **Why selected:** Managed user pools, OAuth2/OIDC, MFA support
- **Integration benefits:**
  - Native integration with API Gateway
  - IAM role assumption for AWS resource access
  - CloudWatch monitoring
- **Managed aspects:** User management, token issuance, security compliance

### 4. Storage - Amazon S3
- **Purpose:** Object storage for files, media, backups
- **Why selected:** Highly durable, scalable, integrated with all AWS services
- **Integration benefits:**
  - IAM permissions
  - CloudWatch metrics
  - S3 Event Notifications (Lambda triggers)
  - Versioning and lifecycle policies
- **Managed aspects:** Durability (11 9's), availability, encryption

### 5. ML/AI - Amazon SageMaker
- **Purpose:** Model training and inference (if applicable)
- **Why selected:** End-to-end ML platform, managed training, scalable endpoints
- **Integration benefits:**
  - IAM permissions
  - S3 integration for data
  - CloudWatch metrics
  - Model Registry
- **Managed aspects:** Infrastructure provisioning, model hosting, auto-scaling

### 6. Monitoring - Amazon CloudWatch
- **Purpose:** Centralized monitoring, logging, and alerting
- **Why selected:** Native integration with all AWS services
- **Integration benefits:**
  - Automatic metrics from AWS services
  - Unified log aggregation
  - Alarms with SNS integration
  - Dashboards for visualization
- **Managed aspects:** Data retention, scaling, alerting infrastructure

## Non-Native Services (IF REQUIRED)

> **Note:** Only use non-native services if AWS doesn't have an equivalent or if specific requirements cannot be met.

### [Example: If using third-party service]
- **Purpose:** [What it does]
- **Why AWS doesn't have equivalent:** [Explanation]
- **Alternative AWS service considered:** [AWS service evaluated but not selected, with reason]
- **Integration complexity:**
  - **Authentication:** API keys (not IAM) - store in Secrets Manager
  - **Networking:** Requires internet gateway or VPC endpoint
  - **Monitoring:** Custom CloudWatch metrics via Lambda
  - **Logging:** Forward logs to CloudWatch via Lambda or agent
  - **Cost tracking:** Not visible in AWS Cost Explorer - manual tracking needed
  - **Disaster recovery:** Custom backup/restore scripts required
- **Maintenance overhead:**
  - Manual security patches
  - Version upgrades coordination
  - Separate monitoring setup
- **Estimated integration time:** [X hours/days for initial setup]
- **Recommendation:** [Use / Reconsider AWS alternative]

## Integration Complexity Matrix

| Aspect | Native Services | Non-Native Services |
|--------|----------------|---------------------|
| Authentication | IAM roles | API keys in Secrets Manager |
| Monitoring | CloudWatch native | Custom metrics/agents |
| Logging | CloudWatch Logs | Forward or separate system |
| Networking | VPC native | VPC endpoints or internet gateway |
| Cost tracking | Cost Explorer | Manual tracking |
| Backups | Automated | Custom scripts |
| Security patches | AWS managed | Manual updates required |
| Scaling | Auto-scaling built-in | Manual configuration |
| Compliance | AWS certifications | Self-managed compliance |

## Decision Rationale

**Why we prefer AWS-native:**

1. **Reduced operational overhead:** AWS manages patches, updates, scaling automatically
2. **Unified IAM security:** Single permission model across all services
3. **Integrated monitoring:** CloudWatch provides single pane of glass
4. **Cost visibility:** All costs visible in AWS Cost Explorer
5. **Compliance:** AWS handles compliance certifications (SOC2, HIPAA, etc.)
6. **Disaster recovery:** Built-in backup and restore capabilities
7. **Support:** AWS Support can troubleshoot issues across all services
8. **Performance:** Native integration reduces latency and improves reliability

**When to consider non-native:**

- AWS service doesn't exist for the specific capability
- Specific advanced features not available in AWS equivalent
- Existing team has deep expertise in third-party tool
- Cost significantly lower (after accounting for integration/maintenance time)
- Contractual obligations with existing vendor

## Service Selection Process

For each capability needed:

```
1. Identify capability requirement
   └─> Check AWS native service catalog

2. Does AWS have native service?
   ├─> YES: Use AWS native (PREFERRED)
   │   └─> Document service, config, cost
   └─> NO: Evaluate alternatives
       ├─> AWS Marketplace managed service?
       │   └─> Evaluate integration complexity
       └─> Self-managed on ECS/EC2?
           └─> Document why needed, integration plan
```

## Recommendations

1. **Always evaluate AWS-native first:** Check AWS service catalog before considering alternatives
2. **Minimize non-native services:** Each non-native service adds integration complexity
3. **Document integration overhead:** For any non-native service, document all integration requirements upfront
4. **Plan for ongoing maintenance:** Budget time for security patches, updates, monitoring setup
5. **Consider AWS Marketplace:** For third-party tools, prefer AWS Marketplace versions for easier billing/integration
6. **Use Secrets Manager:** Store all third-party API keys in AWS Secrets Manager
7. **Forward logs to CloudWatch:** Centralize logging even for non-native services
8. **Custom CloudWatch metrics:** Publish metrics from non-native services to CloudWatch for unified monitoring

## Risk Assessment

**AWS-native services:**

- **Risk: Service deprecation** (Low) - AWS rarely deprecates services
- **Risk: Service limits** (Medium) - May hit quotas, but can request increases
- **Risk: Regional availability** (Low) - Most services available in major regions
- **Mitigation:** Monitor service limits, request quota increases proactively

**Non-native services:**

- **Risk: Integration complexity** (High) - Each service requires custom integration work
- **Risk: Maintenance overhead** (Medium) - Ongoing updates, patches, monitoring
- **Risk: Security vulnerabilities** (Medium) - Need to monitor CVEs and patch promptly
- **Risk: Cost overruns** (Medium) - Hidden costs in integration time and maintenance
- **Risk: Vendor lock-in** (Medium) - Switching costs if service doesn't work out
- **Mitigation:** Minimize non-native services, automate updates where possible, document all integration points

## Architecture Impact

**Using native services simplifies:**

- Infrastructure as Code (all in CDK/CloudFormation)
- Security auditing (unified IAM policies)
- Cost allocation (Cost Explorer tags)
- Disaster recovery (AWS Backup service)
- Compliance reporting (AWS Config)

**Using non-native services requires:**

- Multiple IaC tools (Terraform for third-party, CDK for AWS)
- API key management and rotation
- Custom monitoring and alerting setup
- Separate backup/restore procedures
- Additional compliance documentation

---

*To refine this analysis, use Claude Code with discovery brief context to evaluate specific requirements against AWS service catalog.*
"""),
        ("5_aws_services.yaml", f"""# AWS Services Configuration

## Naming Convention
# Pattern: {{project_name}}_{{environment}}_{{function}}
# Example: {args.adw_id}_dev_api_handler

project_name: {args.adw_id}
environment: dev

services:
  # Compute Services
  - service: Lambda
    purpose: "API Backend Functions"
    naming_pattern: "{args.adw_id}_{{environment}}_{{function_name}}"
    functions:
      - name: api_handler
        full_name: "{args.adw_id}_dev_api_handler"
        runtime: python3.11
        memory: 512
        timeout: 30
        handler: "index.handler"
        code_path: "lambda/api_handler"
        environment_vars:
          - DB_CONNECTION_STRING
          - API_KEY_SECRET_ARN
          - LOG_LEVEL
        iam_policies:
          - "ssm:GetParameter"
          - "secretsmanager:GetSecretValue"
          - "dynamodb:Query"
          - "dynamodb:PutItem"
        layers:
          - common_libs
          - auth_layer
      - name: event_processor
        full_name: "{args.adw_id}_dev_event_processor"
        runtime: python3.11
        memory: 256
        timeout: 60
        handler: "process.handler"
        code_path: "lambda/event_processor"
        trigger: EventBridge
    estimated_cost: "$10-20/month"

  # Storage Services
  - service: S3
    purpose: "Application Storage"
    naming_pattern: "{args.adw_id}-{{environment}}-{{bucket_type}}"
    buckets:
      - name: data
        full_name: "{args.adw_id}-dev-data"
        versioning: true
        encryption: "AES256"
        lifecycle_policies:
          - transition_to_ia: 90 days
          - expire: 365 days
        directories:
          - uploads/
          - processed/
          - exports/
          - temp/
        cors_enabled: true
        public_access: false
      - name: assets
        full_name: "{args.adw_id}-dev-assets"
        versioning: false
        encryption: "AES256"
        directories:
          - static/css/
          - static/js/
          - static/images/
          - templates/
        cloudfront_enabled: true
        public_access: read-only
    estimated_cost: "$5-10/month"

  # Database Services
  - service: DynamoDB
    purpose: "NoSQL Data Storage"
    naming_pattern: "{args.adw_id}_{{environment}}_{{table_name}}"
    tables:
      - name: users
        full_name: "{args.adw_id}_dev_users"
        partition_key: user_id (String)
        sort_key: created_at (Number)
        gsi:
          - name: email_index
            partition_key: email
        billing_mode: PAY_PER_REQUEST
        point_in_time_recovery: true
      - name: sessions
        full_name: "{args.adw_id}_dev_sessions"
        partition_key: session_id (String)
        ttl_attribute: expires_at
        billing_mode: PAY_PER_REQUEST
    estimated_cost: "$5-15/month"

  - service: RDS
    purpose: "Relational Database (PostgreSQL)"
    naming_pattern: "{args.adw_id}-{{environment}}-{{db_name}}"
    instances:
      - name: primary
        full_name: "{args.adw_id}-dev-primary"
        engine: postgres
        version: "15.4"
        instance_class: db.t3.micro
        allocated_storage: 20
        multi_az: false
        backup_retention: 7
        databases:
          - {args.adw_id}_app
        schemas:
          - public
          - audit
        encryption: true
    estimated_cost: "$15-25/month"

  # API & Networking
  - service: API Gateway
    purpose: "REST API Management"
    naming_pattern: "{args.adw_id}-{{environment}}-api"
    apis:
      - name: main_api
        full_name: "{args.adw_id}-dev-api"
        type: REST
        stage: dev
        throttling:
          rate_limit: 1000
          burst_limit: 2000
        endpoints:
          - /api/v1/tasks
          - /api/v1/users
          - /api/v1/auth
        cors_enabled: true
        custom_domain: false
    estimated_cost: "$3/month"

  # Authentication & Authorization
  - service: Cognito
    purpose: "User Authentication & Management"
    naming_pattern: "{args.adw_id}_{{environment}}_{{pool_type}}"
    user_pools:
      - name: user_pool
        full_name: "{args.adw_id}_dev_user_pool"
        password_policy:
          min_length: 8
          require_uppercase: true
          require_numbers: true
          require_symbols: true
        mfa: OPTIONAL
        attributes:
          - email (required)
          - name
          - phone_number
        auto_verify: email
        app_clients:
          - name: web_client
            full_name: "{args.adw_id}_dev_web_client"
    estimated_cost: "$0 (free tier up to 50k MAU)"

  # ML/AI Services (if applicable)
  - service: SageMaker
    purpose: "ML Model Training and Inference"
    naming_pattern: "{args.adw_id}_{{environment}}_{{model_name}}"
    endpoints:
      - name: inference
        full_name: "{args.adw_id}_dev_inference"
        instance_type: ml.t3.medium
        initial_instance_count: 1
        auto_scaling:
          min_capacity: 1
          max_capacity: 3
          target_value: 70
        model_s3_path: "s3://{args.adw_id}-dev-models/inference/"
      - name: batch_transform
        full_name: "{args.adw_id}_dev_batch"
        instance_type: ml.m5.large
        batch_strategy: MultiRecord
        output_s3_path: "s3://{args.adw_id}-dev-data/predictions/"
    training_jobs:
      - name: model_training
        full_name: "{args.adw_id}_dev_training"
        instance_type: ml.g5.xlarge
        instance_count: 1
        training_data_path: "s3://{args.adw_id}-dev-data/training/"
        output_path: "s3://{args.adw_id}-dev-models/"
    estimated_cost: "$200-300/month (if enabled)"

  # Monitoring & Observability
  - service: CloudWatch
    purpose: "Logging and Monitoring"
    naming_pattern: "/aws/{{service}}/{args.adw_id}/{{environment}}/{{resource}}"
    log_groups:
      - /aws/lambda/{args.adw_id}/dev/api_handler
      - /aws/lambda/{args.adw_id}/dev/event_processor
      - /aws/apigateway/{args.adw_id}/dev/main_api
      - /aws/sagemaker/{args.adw_id}/dev/inference
    retention_days: 30
    dashboards:
      - name: "{args.adw_id}_dev_overview"
        widgets:
          - Lambda invocations
          - API Gateway latency
          - DynamoDB throttles
          - SageMaker endpoint metrics
    alarms:
      - Lambda errors > 5% in 5 minutes
      - API Gateway 5xx > 1% in 5 minutes
      - DynamoDB consumed capacity > 80%
    estimated_cost: "$5-10/month"

  # Secrets Management
  - service: Secrets Manager
    purpose: "Secure Credential Storage"
    naming_pattern: "{args.adw_id}/{{environment}}/{{secret_type}}"
    secrets:
      - name: "{args.adw_id}/dev/db_credentials"
        rotation: 30 days
      - name: "{args.adw_id}/dev/api_keys"
        rotation: 90 days
      - name: "{args.adw_id}/dev/jwt_secret"
        rotation: false
    estimated_cost: "$1-2/month"

## Directory Structure Planning

infrastructure/
  cdk/
    lib/
      stacks/
        compute-stack.ts          # Lambda functions
        storage-stack.ts          # S3 buckets
        database-stack.ts         # DynamoDB/RDS
        api-stack.ts              # API Gateway
        auth-stack.ts             # Cognito
        ml-stack.ts               # SageMaker (if applicable)
        monitoring-stack.ts       # CloudWatch
    constructs/
      lambda-function.ts          # Reusable Lambda construct
      s3-bucket.ts                # Reusable S3 construct
      api-endpoint.ts             # Reusable API construct

application/
  lambda/
    api_handler/
      index.py
      requirements.txt
    event_processor/
      process.py
      requirements.txt
    layers/
      common_libs/
        python/
          lib/
      auth_layer/
        python/
          lib/

## Estimated Total Monthly Cost
- Without ML: $40-80/month
- With ML: $240-380/month
"""),
        ("6_architecture.mmd", """graph TB
    User[User] --> CloudFront[CloudFront CDN]
    CloudFront --> APIGateway[API Gateway]
    APIGateway --> Lambda[Lambda Functions]
    Lambda --> RDS[(RDS Database)]
    Lambda --> S3[S3 Storage]
    Lambda --> SageMaker[SageMaker Endpoint]
"""),
        ("7_cost_estimate.md", """# AWS Cost Estimate

## Assumptions
- Monthly active users: 1,000
- API requests/month: 100,000
- Storage: 50 GB
- ML inference requests/month: 10,000 (if applicable)

## Monthly Cost Estimate

### Compute
- **Lambda**: $10

### Storage
- **RDS**: $15
- **S3**: $5

### ML/AI (if applicable)
- **SageMaker Endpoint**: $200 (ml.g5.xlarge real-time)
- **SageMaker Training**: $50 (monthly retraining)

### Networking
- **CloudFront**: $5
- **Data Transfer**: $3

**Total (without ML)**: ~$35/month
**Total (with ML)**: ~$285/month
"""),
        ("8_data_schema.mmd", """---
title: Data Schema - Entity Relationship Diagram
---
erDiagram
    %% Example entities - customize based on 4_data_models.yaml

    User ||--o{ Task : creates
    User ||--o{ Session : has
    User {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }

    Task ||--o{ TaskComment : has
    Task {
        uuid id PK
        uuid user_id FK
        string title
        text description
        string status
        string priority
        date due_date
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
    }

    TaskComment {
        uuid id PK
        uuid task_id FK
        uuid user_id FK
        text content
        timestamp created_at
        timestamp updated_at
    }

    Session {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        timestamp created_at
    }

    %% Add more entities based on your data models
    %% Entity relationships:
    %%   ||--|| : one to one
    %%   ||--o{ : one to many
    %%   }o--o{ : many to many

%% Notes:
%% - This diagram should match the entities defined in 4_data_models.yaml
%% - Update entity names, fields, and relationships based on your project
%% - Use this to visualize database schema and review with stakeholders
%% - PK = Primary Key, FK = Foreign Key, UK = Unique Key
"""),
        ("9_user_auth_rbac.md", f"""# User Authentication & RBAC Security

**ADW ID:** {args.adw_id}
**Last Updated:** {{current_date}}

## Overview

This document defines the authentication flow, role-based access control (RBAC), and security restrictions for the application.

---

## 1. Authentication Strategy

### Primary Authentication: AWS Cognito

**Cognito User Pool:** `{args.adw_id}_dev_user_pool`

**Authentication Flow:**
```
1. User registers → Cognito User Pool
2. Email verification → Cognito sends verification code
3. User logs in → Cognito returns JWT tokens
   - ID Token (user claims)
   - Access Token (API access)
   - Refresh Token (token renewal)
4. Client includes Access Token in API requests
5. API Gateway validates token with Cognito
6. Lambda receives validated user context
```

**Password Policy:**
- Minimum length: 8 characters
- Require uppercase: Yes
- Require numbers: Yes
- Require special characters: Yes
- Password expiry: 90 days (configurable)
- Password history: Prevent reuse of last 5 passwords

**Multi-Factor Authentication (MFA):**
- Type: OPTIONAL (can be enforced per user group)
- Methods: SMS, TOTP (Authenticator app)
- Admin users: MFA REQUIRED
- Regular users: MFA OPTIONAL

---

## 2. User Roles & Permissions

### Role Hierarchy

```
├─ admin           (Full system access)
├─ manager         (Team/resource management)
├─ user            (Standard access)
└─ readonly        (View-only access)
```

### Role Definitions

#### 1. Admin Role
**Cognito Group:** `{args.adw_id}_dev_admins`

**Permissions:**
- ✅ Full CRUD on all resources
- ✅ User management (create, delete, modify roles)
- ✅ System configuration
- ✅ View audit logs
- ✅ Manage API keys
- ✅ Deploy infrastructure changes
- ✅ Access sensitive data

**IAM Policy ARN:** `arn:aws:iam::ACCOUNT_ID:policy/{args.adw_id}-dev-admin-policy`

**DynamoDB Permissions:**
- `dynamodb:*` on all tables

**S3 Permissions:**
- `s3:*` on all buckets

**Lambda Permissions:**
- `lambda:InvokeFunction` on all functions

**Secrets Manager:**
- `secretsmanager:GetSecretValue` on all secrets
- `secretsmanager:PutSecretValue` on all secrets

---

#### 2. Manager Role
**Cognito Group:** `{args.adw_id}_dev_managers`

**Permissions:**
- ✅ Create, read, update resources within their team
- ✅ View team member data
- ✅ Assign tasks to team members
- ✅ Generate reports for their team
- ❌ Delete system-wide resources
- ❌ Modify user roles
- ❌ Access admin panel

**IAM Policy ARN:** `arn:aws:iam::ACCOUNT_ID:policy/{args.adw_id}-dev-manager-policy`

**DynamoDB Permissions:**
- `dynamodb:GetItem`, `PutItem`, `Query`, `Scan` on user tables
- `dynamodb:GetItem`, `PutItem`, `UpdateItem` on resource tables
- ❌ `DeleteItem` on critical tables

**S3 Permissions:**
- `s3:GetObject`, `s3:PutObject` on `{args.adw_id}-dev-data/team/*`
- ❌ Delete permissions on shared resources

---

#### 3. User Role (Standard)
**Cognito Group:** `{args.adw_id}_dev_users`

**Permissions:**
- ✅ Create, read, update own resources
- ✅ View shared/public resources
- ✅ Upload files to personal directory
- ❌ Access other users' private data
- ❌ Delete shared resources
- ❌ Modify system settings

**IAM Policy ARN:** `arn:aws:iam::ACCOUNT_ID:policy/{args.adw_id}-dev-user-policy`

**DynamoDB Permissions:**
- `dynamodb:GetItem`, `PutItem`, `UpdateItem` where `user_id = ${{context.authorizer.claims.sub}}`
- Condition: `StringEquals: dynamodb:LeadingKeys: [${{context.authorizer.claims.sub}}]`

**S3 Permissions:**
- `s3:GetObject`, `s3:PutObject` on `{args.adw_id}-dev-data/users/${{cognito:username}}/*`
- `s3:GetObject` on `{args.adw_id}-dev-assets/*` (public read)

---

#### 4. ReadOnly Role
**Cognito Group:** `{args.adw_id}_dev_readonly`

**Permissions:**
- ✅ View public resources
- ✅ Generate read-only reports
- ❌ Create, update, or delete any resources
- ❌ Access sensitive data

**IAM Policy ARN:** `arn:aws:iam::ACCOUNT_ID:policy/{args.adw_id}-dev-readonly-policy`

**DynamoDB Permissions:**
- `dynamodb:GetItem`, `Query`, `Scan` on non-sensitive tables only

**S3 Permissions:**
- `s3:GetObject` on `{args.adw_id}-dev-assets/*` only

---

## 3. API Gateway Authorization

### Cognito Authorizer Configuration

```yaml
API Gateway: {args.adw_id}-dev-api
Authorizer:
  Name: {args.adw_id}_cognito_authorizer
  Type: COGNITO_USER_POOLS
  Provider ARN: arn:aws:cognito-idp:REGION:ACCOUNT_ID:userpool/USER_POOL_ID
  Token Source: method.request.header.Authorization
  Token Validation: JWKS (automatic)
  Identity Source: method.request.header.Authorization
  Authorization Scopes:
    - openid
    - email
    - profile
```

### Endpoint-Level Permissions

| Endpoint | Method | Required Role | Additional Checks |
|----------|--------|---------------|-------------------|
| `/api/v1/tasks` | GET | user | Returns only user's own tasks |
| `/api/v1/tasks` | POST | user | user_id set to authenticated user |
| `/api/v1/tasks/{{id}}` | PUT | user | Ownership check: task.user_id == auth.user_id |
| `/api/v1/tasks/{{id}}` | DELETE | user | Ownership check: task.user_id == auth.user_id |
| `/api/v1/users` | GET | manager | Returns team members only |
| `/api/v1/users` | POST | admin | Only admins can create users |
| `/api/v1/users/{{id}}` | DELETE | admin | Only admins can delete users |
| `/api/v1/admin/*` | ALL | admin | All admin endpoints require admin role |

---

## 4. Lambda-Level Authorization

### Authorization Logic in Lambda Functions

**File:** `lambda/api_handler/index.py`

```python
def check_authorization(event, required_role, resource_id=None):
    \"\"\"
    Verify user has required role and optional resource ownership.

    Args:
        event: API Gateway event with authorizer context
        required_role: Role required (admin, manager, user, readonly)
        resource_id: Optional - check if user owns this resource

    Returns:
        dict: {{"authorized": bool, "reason": str}}
    \"\"\"
    # Extract claims from Cognito authorizer
    claims = event['requestContext']['authorizer']['claims']
    user_id = claims['sub']
    user_email = claims['email']
    user_groups = claims.get('cognito:groups', '').split(',')

    # Check role membership
    role_map = {{
        'admin': '{args.adw_id}_dev_admins',
        'manager': '{args.adw_id}_dev_managers',
        'user': '{args.adw_id}_dev_users',
        'readonly': '{args.adw_id}_dev_readonly'
    }}

    required_group = role_map.get(required_role)
    if required_group not in user_groups:
        return {{
            'authorized': False,
            'reason': f'User lacks required role: {{required_role}}'
        }}

    # If resource ownership check required
    if resource_id:
        # Query DynamoDB to get resource owner
        table = boto3.resource('dynamodb').Table('{args.adw_id}_dev_resources')
        response = table.get_item(Key={{'resource_id': resource_id}})

        if 'Item' not in response:
            return {{'authorized': False, 'reason': 'Resource not found'}}

        resource_owner = response['Item'].get('user_id')

        # Admins can access any resource
        if '{args.adw_id}_dev_admins' in user_groups:
            return {{'authorized': True, 'reason': 'Admin override'}}

        # Check ownership
        if resource_owner != user_id:
            return {{
                'authorized': False,
                'reason': 'User does not own this resource'
            }}

    return {{'authorized': True, 'reason': 'Authorized'}}
```

---

## 5. Data-Level Security

### Row-Level Security (RLS)

**DynamoDB:**
- User-owned tables must include `user_id` partition/sort key
- Queries automatically filtered by authenticated user ID
- Admins can override with special query parameter

**Example Query with RLS:**
```python
# Standard user query (automatic filtering)
response = table.query(
    KeyConditionExpression=Key('user_id').eq(authenticated_user_id)
)

# Admin query (can access all)
if is_admin(user_groups):
    response = table.scan()  # Full scan allowed for admins only
```

**RDS/PostgreSQL:**
- Use PostgreSQL Row Level Security (RLS) policies
- Policies enforced at database level

```sql
-- Enable RLS on tasks table
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Policy: Users see only their own tasks
CREATE POLICY user_tasks_policy ON tasks
    FOR SELECT
    TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- Policy: Admins see all tasks
CREATE POLICY admin_tasks_policy ON tasks
    FOR ALL
    TO admin_user
    USING (true);
```

### Column-Level Security

**Sensitive Fields:**
- `password_hash` - Never returned in API responses
- `email` - Returned only to owner or admin
- `phone_number` - Returned only to owner or admin
- `ssn` / `payment_info` - Encrypted at rest, access logged

**Lambda Response Filtering:**
```python
def filter_sensitive_fields(user_object, requester_role, requester_id):
    \"\"\"Remove sensitive fields based on requester permissions.\"\"\"
    filtered = user_object.copy()

    # Always remove password hash
    filtered.pop('password_hash', None)

    # Remove PII unless owner or admin
    if requester_role not in ['admin'] and requester_id != user_object['user_id']:
        filtered.pop('email', None)
        filtered.pop('phone_number', None)
        filtered.pop('ssn', None)
        filtered.pop('payment_info', None)

    return filtered
```

---

## 6. Security Restrictions & Best Practices

### Rate Limiting

**API Gateway Throttling:**
```yaml
Default Limits:
  Rate Limit: 1,000 requests/second
  Burst Limit: 2,000 requests

Per-User Quotas:
  Free Tier: 100 requests/day
  Standard: 10,000 requests/day
  Admin: Unlimited
```

**Implementation:**
```python
# Usage plan in CDK
const usagePlan = api.addUsagePlan('UsagePlan', {{
  throttle: {{
    rateLimit: 1000,
    burstLimit: 2000
  }},
  quota: {{
    limit: 10000,
    period: apigateway.Period.DAY
  }}
}});
```

### IP Whitelisting (Optional)

**Admin Endpoints:**
```yaml
Allowed IPs for /api/v1/admin/*:
  - Corporate VPN: 203.0.113.0/24
  - Office Network: 198.51.100.0/24
```

**Implementation in API Gateway Resource Policy:**
```json
{{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "execute-api:Invoke",
  "Resource": "arn:aws:execute-api:*:*:*/*/POST/admin/*",
  "Condition": {{
    "NotIpAddress": {{
      "aws:SourceIp": ["203.0.113.0/24", "198.51.100.0/24"]
    }}
  }}
}}
```

### Encryption

**Data at Rest:**
- DynamoDB: Encrypted with AWS-managed keys (default)
- S3: AES-256 encryption enabled on all buckets
- RDS: Encryption enabled at database instance level
- Secrets Manager: Encrypted with KMS CMK

**Data in Transit:**
- All API endpoints: HTTPS only (TLS 1.2+)
- Certificate: AWS Certificate Manager (ACM)
- Strict Transport Security (HSTS) enabled

### Audit Logging

**CloudWatch Logs:**
```
Log Group: /aws/security/{args.adw_id}/dev/audit
Retention: 90 days
```

**Logged Events:**
- User login/logout
- Failed authentication attempts
- Role changes
- Access to sensitive resources
- API errors (4xx, 5xx)
- Admin actions

**Log Format:**
```json
{{
  "timestamp": "2025-10-17T10:30:00Z",
  "event_type": "API_ACCESS",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_email": "user@example.com",
  "user_role": "user",
  "action": "GET /api/v1/tasks",
  "resource_id": "task-12345",
  "result": "SUCCESS",
  "ip_address": "203.0.113.45",
  "user_agent": "Mozilla/5.0..."
}}
```

---

## 7. Security Compliance

### OWASP Top 10 Mitigation

| Vulnerability | Mitigation |
|---------------|------------|
| **A01: Broken Access Control** | Cognito + API Gateway authorizer + Lambda ownership checks |
| **A02: Cryptographic Failures** | TLS 1.2+ in transit, AES-256 at rest, KMS for secrets |
| **A03: Injection** | Parameterized queries, input validation, DynamoDB (NoSQL) |
| **A04: Insecure Design** | Security by design, principle of least privilege, RBAC |
| **A05: Security Misconfiguration** | Infrastructure as Code (CDK), automated security scanning |
| **A06: Vulnerable Components** | Dependabot, automated vulnerability scanning |
| **A07: Auth & Session Mgmt** | Cognito JWT tokens, secure session handling |
| **A08: Software & Data Integrity** | Signed deployments, CloudFormation drift detection |
| **A09: Logging Failures** | CloudWatch comprehensive logging, 90-day retention |
| **A10: SSRF** | VPC isolation, restrictive security groups |

### Compliance Frameworks

**SOC 2 Type II:**
- Access controls: Cognito + RBAC
- Logging: CloudWatch audit trail
- Encryption: At-rest and in-transit

**GDPR:**
- Data minimization: Collect only required fields
- Right to be forgotten: User deletion API
- Data portability: Export user data API
- Consent management: Opt-in for data processing

**HIPAA (if applicable):**
- Business Associate Agreement (BAA) with AWS
- Encryption of PHI at rest and in transit
- Access logs for PHI
- Automatic session timeout

---

## 8. Incident Response

### Security Event Response Plan

**Severity Levels:**
1. **Critical** - Active breach, data exfiltration
2. **High** - Privilege escalation, unauthorized admin access
3. **Medium** - Failed login attempts, suspicious API usage
4. **Low** - Policy violations, audit log anomalies

**Response Procedures:**

**1. Detection:**
- CloudWatch Alarms trigger on anomalies
- SNS notification to security team
- Lambda auto-remediation (e.g., disable compromised user)

**2. Containment:**
- Disable compromised user accounts immediately
- Rotate API keys and secrets
- Enable MFA for all users (if not already required)

**3. Investigation:**
- Review CloudWatch audit logs
- Identify affected resources
- Determine attack vector

**4. Recovery:**
- Restore from backups if needed
- Re-enable users after password reset
- Apply security patches

**5. Post-Incident:**
- Document lessons learned
- Update security policies
- Implement additional controls

---

## 9. Recommended Security Enhancements

### Short-Term (MVP)
- ✅ Cognito user authentication
- ✅ API Gateway authorizer
- ✅ RBAC with 4 roles
- ✅ HTTPS only
- ✅ Secrets in Secrets Manager

### Medium-Term (Post-Launch)
- 🔄 Enable MFA for all users
- 🔄 Implement rate limiting per user
- 🔄 Add IP whitelisting for admin endpoints
- 🔄 Automated security scanning (Prowler, ScoutSuite)

### Long-Term (Scale)
- 📅 Web Application Firewall (AWS WAF)
- 📅 DDoS protection (AWS Shield)
- 📅 Real-time threat detection (GuardDuty)
- 📅 Automated compliance reporting (AWS Config)

---

## 10. References

- [AWS Cognito Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/security-best-practices.html)
- [API Gateway Security](https://docs.aws.amazon.com/apigateway/latest/developerguide/security.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

**Security Review:** Requires stakeholder approval before production deployment
**Last Reviewed:** {{current_date}}
**Next Review:** {{next_review_date}}
"""),
        ("10_cdk_constructs.md", f"""# CDK Constructs Research & Recommendations

**ADW ID:** {args.adw_id}
**Last Updated:** {{current_date}}

## Overview

This document provides research on available CDK constructs and recommendations for implementation, with special focus on ML/SageMaker projects.

---

## 1. Official AWS CDK Construct Libraries

### 🎯 Generative AI & Bedrock Constructs

#### AWS Generative AI CDK Constructs (Primary Recommendation)
**Repository:** [github.com/awslabs/generative-ai-cdk-constructs](https://github.com/awslabs/generative-ai-cdk-constructs)
**Documentation:** [awslabs.github.io/generative-ai-cdk-constructs](https://awslabs.github.io/generative-ai-cdk-constructs/)

**Best For:**
- RAG (Retrieval-Augmented Generation) applications
- Amazon Bedrock model deployment
- Knowledge base management
- Document ingestion pipelines
- Generative AI monitoring dashboards

**Key Constructs:**
```typescript
import {{ bedrock, opensearchserverless, s3bucketreader }} from '@cdklabs/generative-ai-cdk-constructs';

// Bedrock Knowledge Base with OpenSearch
const knowledgeBase = new bedrock.KnowledgeBase(this, 'KB', {{
  embeddingsModel: bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V1,
  vectorStore: new opensearchserverless.VectorCollection(this, 'VectorStore', {{
    collectionName: '{args.adw_id}-vectors'
  }})
}});

// S3 Data Source for RAG
const dataSource = new s3bucketreader.S3BucketReader(this, 'DataSource', {{
  bucket: dataBucket,
  knowledgeBase: knowledgeBase,
  chunkingStrategy: {{
    chunkSize: 512,
    overlapPercentage: 20
  }}
}});
```

**Available Constructs:**
- `bedrock.KnowledgeBase` - Vector database backed knowledge bases
- `bedrock.Agent` - Bedrock Agents with action groups
- `bedrock.GuardrailsMonitoring` - Safety and content filtering
- `bedrock.CloudWatchDashboard` - Bedrock metrics dashboard
- `opensearchserverless.VectorCollection` - Serverless vector store
- `s3bucketreader.S3BucketReader` - Document ingestion from S3

**Example Use Cases:**
1. RAG chatbot with S3 document store
2. AI-powered search over knowledge base
3. Multi-agent orchestration with Bedrock Agents

---

#### Amazon Bedrock Construct Library
**Repository:** [awslabs.github.io/generative-ai-cdk-constructs/src/cdk-lib/bedrock](https://awslabs.github.io/generative-ai-cdk-constructs/src/cdk-lib/bedrock/)

**Focus:** Lower-level Bedrock API access

```typescript
import {{ bedrock }} from 'aws-cdk-lib/aws-bedrock';

// Create Bedrock model invocation
const model = new bedrock.CfnFoundationModel(this, 'Model', {{
  modelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
  modelArn: 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet'
}});
```

---

### 🤖 SageMaker Constructs

#### Custom SageMaker Endpoint Construct
**Repository:** [CustomSageMakerEndpoint](https://awslabs.github.io/generative-ai-cdk-constructs/apidocs/classes/CustomSageMakerEndpoint.html)

**Purpose:** Simplified deployment of custom SageMaker endpoints with standardized configurations

```typescript
import {{ CustomSageMakerEndpoint }} from '@cdklabs/generative-ai-cdk-constructs';

const endpoint = new CustomSageMakerEndpoint(this, 'Endpoint', {{
  modelId: '{args.adw_id}_dev_inference',
  instanceType: sagemaker.InstanceType.ML_G5_XLARGE,
  instanceCount: 1,
  modelDataUrl: 's3://{args.adw_id}-dev-models/model.tar.gz',
  environment: {{
    'MODEL_NAME': 'my-custom-model',
    'INFERENCE_MODE': 'realtime'
  }},
  autoScaling: {{
    minCapacity: 1,
    maxCapacity: 3,
    targetValue: 70,
    scaleInCooldown: 300,
    scaleOutCooldown: 60
  }}
}});
```

**Features:**
- Auto-scaling configuration
- CloudWatch metrics integration
- Model monitoring hooks
- Automatic endpoint naming

---

### 📊 Solutions Constructs

#### AWS Solutions Constructs
**Repository:** [github.com/awslabs/aws-solutions-constructs](https://github.com/awslabs/aws-solutions-constructs)

**Best For:**
- Multi-service patterns (Lambda + DynamoDB, API Gateway + Lambda, etc.)
- Analytics pipelines (Kinesis + Lambda + S3)
- Data processing (S3 + Lambda + SQS)

**Example - API Gateway + Lambda + DynamoDB:**
```typescript
import {{ ApiGatewayToLambdaToDynamoDB }} from '@aws-solutions-constructs/aws-apigateway-lambda-dynamodb';

const construct = new ApiGatewayToLambdaToDynamoDB(this, 'ApiLambdaDB', {{
  lambdaFunctionProps: {{
    runtime: lambda.Runtime.PYTHON_3_11,
    handler: 'index.handler',
    code: lambda.Code.fromAsset('lambda/api_handler')
  }},
  dynamoTableProps: {{
    tableName: '{args.adw_id}_dev_resources',
    partitionKey: {{ name: 'id', type: dynamodb.AttributeType.STRING }},
    billingMode: dynamodb.BillingMode.PAY_PER_REQUEST
  }}
}});
```

**Available Patterns (100+):**
- `aws-apigateway-lambda`
- `aws-lambda-dynamodb`
- `aws-s3-lambda`
- `aws-lambda-sqs-lambda` (event-driven)
- `aws-cloudfront-s3` (static site)
- `aws-lambda-sagemakerendpoint` - Lambda invoking SageMaker
- `aws-kinesisfirehose-s3-and-kinesisanalytics` - Analytics pipeline

---

### 📈 Monitoring Constructs

#### cdk-monitoring-constructs
**Repository:** [github.com/cdklabs/cdk-monitoring-constructs](https://github.com/cdklabs/cdk-monitoring-constructs)

**Purpose:** Simplified CloudWatch alarms, dashboards, and metrics

```typescript
import {{ MonitoringFacade }} from 'cdk-monitoring-constructs';

const monitoring = new MonitoringFacade(this, 'Monitoring', {{
  alarmFactoryDefaults: {{
    alarmNamePrefix: '{args.adw_id}-dev',
    actionsEnabled: true,
    action: new SnsAction(alertTopic)
  }}
}});

// Monitor Lambda function
monitoring.monitorLambdaFunction({{
  lambdaFunction: apiHandlerFunction,
  addLatencyP99Alarm: {{ maxLatency: Duration.seconds(3) }},
  addErrorRateAlarm: {{ maxErrorRate: 5 }},
  addThrottlesRateAlarm: {{ maxThrottlesRate: 2 }}
}});

// Monitor SageMaker endpoint
monitoring.monitorSageMakerEndpoint({{
  endpoint: inferenceEndpoint,
  addModelLatencyP99Alarm: {{ maxLatency: Duration.milliseconds(500) }},
  addInvocationErrorsAlarm: {{ maxErrorRate: 1 }}
}});
```

---

## 2. Data & Analytics Constructs

### Data Lake Constructs

#### cdk-datalake-constructs
**Repository:** [github.com/aws-samples/aws-cdk-datalake](https://github.com/aws-samples/aws-cdk-datalake)

**Stack:**
- S3 (raw, processed, curated buckets)
- AWS Glue (ETL, Crawlers, Data Catalog)
- Amazon Athena (SQL queries)
- Lake Formation (permissions)

```typescript
import {{ DataLakeStack }} from 'cdk-datalake-constructs';

const dataLake = new DataLakeStack(this, 'DataLake', {{
  rawBucket: '{args.adw_id}-dev-raw',
  processedBucket: '{args.adw_id}-dev-processed',
  curatedBucket: '{args.adw_id}-dev-curated',
  glueCrawlerSchedule: 'cron(0 2 * * ? *)',  // Daily at 2 AM
  athenaWorkgroup: '{args.adw_id}-dev-workgroup'
}});
```

**Use Cases:**
- ML training data pipeline
- Log analytics
- Business intelligence

---

### EMR Serverless with Delta Lake

#### cdk-emrserverless-with-delta-lake
**Repository:** [github.com/aws-samples/cdk-emrserverless-with-delta-lake](https://github.com/aws-samples/cdk-emrserverless-with-delta-lake)

**For:** Large-scale data processing with ACID transactions

```typescript
import {{ EMRServerlessDeltaLake }} from 'cdk-emrserverless-with-delta-lake';

const emr = new EMRServerlessDeltaLake(this, 'EMR', {{
  applicationName: '{args.adw_id}-dev-emr',
  releaseLabel: 'emr-6.10.0',
  s3BucketName: '{args.adw_id}-dev-data',
  deltaTablePath: 's3://{args.adw_id}-dev-data/delta-tables/'
}});
```

---

### OpenSearch Constructs

#### cdk-opensearch
**Package:** [@aws-cdk/aws-opensearchservice](https://constructs.dev/packages/@aws-cdk/aws-opensearchservice)

```typescript
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';

const domain = new opensearch.Domain(this, 'Domain', {{
  version: opensearch.EngineVersion.OPENSEARCH_2_5,
  capacity: {{
    dataNodes: 2,
    dataNodeInstanceType: 't3.small.search',
    masterNodes: 0
  }},
  ebs: {{
    volumeSize: 20,
    volumeType: ec2.EbsDeviceVolumeType.GP3
  }},
  zoneAwareness: {{
    enabled: true,
    availabilityZoneCount: 2
  }},
  logging: {{
    slowSearchLogEnabled: true,
    appLogEnabled: true,
    slowIndexLogEnabled: true
  }}
}});
```

**Use Case:** Vector search for RAG applications

---

## 3. CI/CD & Testing Constructs

### cdk-pipelines-github
**Repository:** [github.com/cdklabs/cdk-pipelines-github](https://github.com/cdklabs/cdk-pipelines-github)

**Purpose:** CDK deployments via GitHub Actions

```typescript
import {{ GitHubWorkflow }} from 'cdk-pipelines-github';

const workflow = new GitHubWorkflow(app, 'Workflow', {{
  synth: new ShellStep('Synth', {{
    commands: ['npm ci', 'npm run build', 'npx cdk synth']
  }}),
  awsCredentials: AwsCredentials.fromOpenIdConnect({{
    gitHubActionRoleArn: 'arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole'
  }})
}});

workflow.addStage(devStage);
workflow.addStage(prodStage, {{
  pre: [new ManualApprovalStep('PromoteToProd')]
}});
```

---

### cdk-integ-tests (Alpha)
**Repository:** [github.com/aws/aws-cdk/tree/main/packages/aws-cdk-integ-tests-alpha](https://github.com/aws/aws-cdk/tree/main/packages/aws-cdk-integ-tests-alpha)

**Purpose:** Native CDK integration testing

```typescript
import {{ IntegTest }} from '@aws-cdk/integ-tests-alpha';

const integ = new IntegTest(app, 'SageMakerIntegTest', {{
  testCases: [stack],
  diffAssets: true,
  regions: ['us-east-1']
}});

// Invoke SageMaker endpoint
const invoke = integ.assertions.awsApiCall('SageMakerRuntime', 'invokeEndpoint', {{
  EndpointName: endpoint.endpointName,
  Body: JSON.stringify({{ input: 'test' }})
}});

invoke.expect(ExpectedResult.objectLike({{
  StatusCode: 200
}}));
```

---

## 4. Project-Specific Recommendations

### For This Project: {args.adw_id}

Based on `5_aws_services.yaml` analysis:

#### Recommended Constructs:

**1. API + Lambda + DynamoDB**
```typescript
// Use AWS Solutions Construct
import {{ ApiGatewayToLambdaToDynamoDB }} from '@aws-solutions-constructs/aws-apigateway-lambda-dynamodb';
```
**Rationale:** Reduces boilerplate, follows AWS best practices

**2. Cognito Authentication**
```typescript
// Use standard CDK lib
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

// Cognito Authorizer for API Gateway
const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'Authorizer', {{
  cognitoUserPools: [userPool]
}});
```

**3. S3 + CloudFront (Static Assets)**
```typescript
// Use AWS Solutions Construct
import {{ CloudFrontToS3 }} from '@aws-solutions-constructs/aws-cloudfront-s3';
```

**4. SageMaker (if ML project)**
```typescript
// Use Generative AI CDK Constructs
import {{ CustomSageMakerEndpoint }} from '@cdklabs/generative-ai-cdk-constructs';
```

**5. Monitoring**
```typescript
// Use cdk-monitoring-constructs
import {{ MonitoringFacade }} from 'cdk-monitoring-constructs';
```

---

## 5. Sample CDK Stack Structure

### Recommended Project Structure

```
infrastructure/
  cdk/
    bin/
      app.ts                           # CDK app entry point
    lib/
      stacks/
        compute-stack.ts               # Lambda functions
        storage-stack.ts               # S3 buckets
        database-stack.ts              # DynamoDB/RDS
        api-stack.ts                   # API Gateway
        auth-stack.ts                  # Cognito
        ml-stack.ts                    # SageMaker (optional)
        monitoring-stack.ts            # CloudWatch
      constructs/
        bedrock-rag-construct.ts       # Custom RAG construct
        sagemaker-endpoint-construct.ts # Custom SageMaker
    test/
      stacks/
        compute-stack.test.ts
        api-stack.test.ts
    cdk.json
    package.json
    tsconfig.json
```

---

### Example Implementation

**File:** `lib/stacks/ml-stack.ts`

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sagemaker from 'aws-cdk-lib/aws-sagemaker';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import {{ CustomSageMakerEndpoint }} from '@cdklabs/generative-ai-cdk-constructs';
import {{ Construct }} from 'constructs';

export class MLStack extends cdk.Stack {{
  public readonly endpoint: sagemaker.CfnEndpoint;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {{
    super(scope, id, props);

    // Model storage bucket
    const modelBucket = new s3.Bucket(this, 'ModelBucket', {{
      bucketName: '{args.adw_id}-dev-models',
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    }});

    // SageMaker execution role
    const role = new iam.Role(this, 'SageMakerRole', {{
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess')
      ]
    }});

    modelBucket.grantRead(role);

    // Custom SageMaker endpoint with auto-scaling
    const endpointConstruct = new CustomSageMakerEndpoint(this, 'Endpoint', {{
      modelId: '{args.adw_id}_dev_inference',
      instanceType: sagemaker.InstanceType.ML_G5_XLARGE,
      instanceCount: 1,
      modelDataUrl: modelBucket.s3UrlForObject('model.tar.gz'),
      executionRole: role,
      autoScaling: {{
        minCapacity: 1,
        maxCapacity: 3,
        targetValue: 70
      }}
    }});

    this.endpoint = endpointConstruct.endpoint;

    // Output endpoint name
    new cdk.CfnOutput(this, 'EndpointName', {{
      value: this.endpoint.attrEndpointName,
      description: 'SageMaker endpoint name'
    }});
  }}
}}
```

---

## 6. CDK Examples Repository

### Official AWS CDK Examples
**Repository:** [github.com/aws-samples/aws-cdk-examples](https://github.com/aws-samples/aws-cdk-examples)

**Relevant Examples:**
- `typescript/api-gateway-lambda-dynamodb/` - API + Lambda + DB
- `typescript/sagemaker/` - SageMaker endpoint deployment
- `typescript/cognito-api-lambda/` - Cognito auth with API Gateway
- `python/lambda-cron/` - Scheduled Lambda
- `typescript/cloudfront-s3-static-website/` - Static site

**How to Use:**
1. Clone repo: `git clone https://github.com/aws-samples/aws-cdk-examples.git`
2. Navigate to relevant example
3. Copy patterns into your project
4. Customize for your use case

---

## 7. Construct Hub Discovery

### Finding More Constructs

**Primary Resources:**
1. **Construct Hub:** [constructs.dev](https://constructs.dev) - Search by service, popularity, or recency
2. **GitHub Topic:** [github.com/topics/cdk-constructs](https://github.com/topics/cdk-constructs) - Browse trending
3. **AWS Labs:** [github.com/awslabs](https://github.com/awslabs) - Official experimental constructs
4. **AWS Blogs:** [aws.amazon.com/blogs/devops/category/developer-tools/aws-cdk/](https://aws.amazon.com/blogs/devops/category/developer-tools/aws-cdk/) - New releases

**Search Strategy:**
```
# Find SageMaker constructs
constructs.dev → Search: "sagemaker"

# Find RAG constructs
constructs.dev → Search: "rag" or "bedrock" or "knowledge base"

# Find monitoring constructs
constructs.dev → Search: "cloudwatch" or "monitoring"
```

---

## 8. Implementation Checklist

### Before Starting CDK Development

- [ ] Review `5_aws_services.yaml` to identify required services
- [ ] Check Construct Hub for existing patterns
- [ ] Evaluate AWS Solutions Constructs for multi-service patterns
- [ ] For ML projects: Review Generative AI CDK Constructs
- [ ] Set up CDK project structure (see Section 5)
- [ ] Install required construct libraries
- [ ] Configure CI/CD pipeline (cdk-pipelines-github)
- [ ] Set up integration tests (cdk-integ-tests-alpha)
- [ ] Enable monitoring (cdk-monitoring-constructs)

### Construct Selection Criteria

**Prefer AWS Solutions Constructs when:**
- ✅ Pattern matches your use case (API + Lambda + DB, etc.)
- ✅ Reduces boilerplate code by 50%+
- ✅ Follows AWS Well-Architected best practices

**Prefer Generative AI CDK Constructs when:**
- ✅ Building RAG applications
- ✅ Using Amazon Bedrock
- ✅ Deploying custom SageMaker models
- ✅ Need built-in monitoring dashboards

**Use Standard CDK when:**
- ✅ Simple single-service deployment
- ✅ Need fine-grained control
- ✅ No existing construct matches use case

---

## 9. Next Steps

1. **Research Phase:**
   - Review Construct Hub for project-specific constructs
   - Evaluate AWS Solutions Constructs patterns
   - Check CDK examples for similar architectures

2. **POC Phase:**
   - Implement 1 stack using recommended constructs
   - Test deployment in dev environment
   - Validate monitoring and logging

3. **Implementation Phase:**
   - Build remaining stacks
   - Set up CI/CD pipeline
   - Deploy to staging for UAT

4. **Production Phase:**
   - Final security review
   - Deploy to production with manual approval
   - Enable automated monitoring

---

## 10. References

- **Official AWS CDK Docs:** [docs.aws.amazon.com/cdk](https://docs.aws.amazon.com/cdk/)
- **CDK Workshop:** [cdkworkshop.com](https://cdkworkshop.com/)
- **CDK Patterns:** [cdkpatterns.com](https://cdkpatterns.com/)
- **Generative AI Constructs Docs:** [awslabs.github.io/generative-ai-cdk-constructs](https://awslabs.github.io/generative-ai-cdk-constructs/)
- **Construct Hub:** [constructs.dev](https://constructs.dev/)

---

**Review Status:** Pending stakeholder approval
**Last Updated:** {{current_date}}
**Recommended Review Cadence:** Quarterly (new constructs released frequently)
"""),
        ("11_validation_gates.yaml", f"""# Validation Gates & Success Metrics

project_id: {args.adw_id}
environment: dev

## Overview
# This file defines success criteria, validation gates, and metrics for each phase of the project.
# Gates must be passed before proceeding to the next phase.

---

## Phase 1: Discovery

validation_gates:
  - gate_id: DG-001
    name: "Discovery Brief Complete"
    type: documentation
    required: true
    criteria:
      - Discovery brief document created
      - Project scope clearly defined
      - Stakeholder interviews completed
    approval_required: true
    approver: Product Owner

success_metrics:
  quantitative:
    - metric: "Stakeholder interviews completed"
      target: "≥ 3 interviews"
      measurement: "Count of interview transcripts"
    - metric: "Requirements documented"
      target: "≥ 10 user stories identified"
      measurement: "Count in discovery brief"
    - metric: "Budget estimate accuracy"
      target: "±20% of final cost"
      measurement: "Variance analysis at project end"

  qualitative:
    - metric: "Stakeholder alignment"
      target: "All key stakeholders agree on scope"
      measurement: "Sign-off from Product Owner + Tech Lead"
    - metric: "Technical feasibility"
      target: "No major technical blockers identified"
      measurement: "Technical risk assessment completed"
    - metric: "Requirements clarity"
      target: "Requirements unambiguous and testable"
      measurement: "Peer review by 2+ team members"

---

## Phase 2: Scoping

validation_gates:
  - gate_id: SG-001
    name: "Technical Architecture Approved"
    type: technical_review
    required: true
    criteria:
      - Architecture diagram completed
      - AWS services selected
      - Data models defined
      - Security requirements documented
    approval_required: true
    approver: Tech Lead + Security Team

  - gate_id: SG-002
    name: "Cost Estimate Approved"
    type: financial_review
    required: true
    criteria:
      - Monthly cost estimate within budget
      - Cost optimization strategies documented
      - Scaling cost projections provided
    approval_required: true
    approver: Finance + Product Owner

  - gate_id: SG-003
    name: "CDK Constructs Reviewed"
    type: technical_review
    required: true
    criteria:
      - Recommended CDK constructs identified
      - Implementation approach documented
      - Dependencies and libraries listed
    approval_required: false
    approver: Tech Lead

success_metrics:
  quantitative:
    - metric: "AWS services documented"
      target: "100% of required services identified"
      measurement: "Count in 5_aws_services.yaml"
    - metric: "Cost estimate accuracy"
      target: "Within ±15% of actual monthly cost"
      measurement: "Compare estimate to actual AWS bill Month 1"
    - metric: "Data entities modeled"
      target: "≥ 5 entities with full schemas"
      measurement: "Count in 4_data_models.yaml"
    - metric: "User flows documented"
      target: "≥ 3 primary user flows"
      measurement: "Count in 3_user_flows.yaml"

  qualitative:
    - metric: "Architecture scalability"
      target: "Supports 10x user growth without redesign"
      measurement: "Architecture review by senior engineer"
    - metric: "Security posture"
      target: "OWASP Top 10 mitigations documented"
      measurement: "Security review in 9_user_auth_rbac.md"
    - metric: "AWS best practices"
      target: "Follows AWS Well-Architected Framework"
      measurement: "Well-Architected review checklist"

---

## Phase 3: Planning

validation_gates:
  - gate_id: PG-001
    name: "Sprint Plan Approved"
    type: project_management
    required: true
    criteria:
      - Stories broken down into tasks
      - Story points estimated
      - Sprint capacity calculated
      - Dependencies mapped
    approval_required: true
    approver: Scrum Master + Tech Lead

success_metrics:
  quantitative:
    - metric: "Stories created"
      target: "≥ 3 stories for MVP"
      measurement: "Count in 8_agile_stories.yaml"
    - metric: "Story point estimation variance"
      target: "±30% of actual effort"
      measurement: "Compare estimates to actuals at sprint end"
    - metric: "Dependencies identified"
      target: "100% of inter-story dependencies mapped"
      measurement: "Dependency graph in planning doc"

  qualitative:
    - metric: "Story clarity"
      target: "All stories have clear acceptance criteria"
      measurement: "Peer review by development team"
    - metric: "Team confidence"
      target: "Team agrees sprint is achievable"
      measurement: "Sprint planning vote (thumbs up/down)"

---

## Phase 4-6: Development (Per Story)

validation_gates:
  - gate_id: DEV-001
    name: "Code Complete"
    type: development
    required: true
    criteria:
      - All acceptance criteria implemented
      - Code committed to feature branch
      - No placeholder/TODO comments
    approval_required: false
    approver: Self-review

  - gate_id: DEV-002
    name: "Unit Tests Passing"
    type: testing
    required: true
    criteria:
      - Unit test coverage ≥ 80%
      - All unit tests passing
      - No skipped tests without justification
    approval_required: false
    approver: Automated CI/CD

success_metrics:
  quantitative:
    - metric: "Test coverage"
      target: "≥ 80% line coverage"
      measurement: "Coverage report from pytest/jest"
    - metric: "Code complexity"
      target: "Cyclomatic complexity ≤ 10 per function"
      measurement: "Static analysis (Radon/SonarQube)"
    - metric: "Story completion time"
      target: "≤ Estimated story points × 1.5"
      measurement: "Time tracking in GitHub issues"
    - metric: "Bugs introduced"
      target: "≤ 2 bugs per story"
      measurement: "Count of bugs filed against story"

  qualitative:
    - metric: "Code readability"
      target: "Code is self-documenting with clear naming"
      measurement: "Code review feedback"
    - metric: "Documentation quality"
      target: "Functions have docstrings, complex logic explained"
      measurement: "Code review checklist"
    - metric: "Adherence to standards"
      target: "Follows team coding standards"
      measurement: "Linter passing (Black, Ruff, ESLint)"

---

## Phase 7: Testing

validation_gates:
  - gate_id: TEST-001
    name: "Unit Tests Passing"
    type: automated_testing
    required: true
    criteria:
      - 100% of unit tests passing
      - Test coverage ≥ 80%
      - No flaky tests
    approval_required: false
    approver: Automated CI/CD

  - gate_id: TEST-002
    name: "E2E Tests Passing"
    type: automated_testing
    required: true
    criteria:
      - 100% of E2E tests passing
      - Critical user flows validated
      - Test retry successful (if initially failed)
    approval_required: false
    approver: Automated CI/CD

  - gate_id: TEST-003
    name: "Performance Benchmarks Met"
    type: performance_testing
    required: true
    criteria:
      - API latency ≤ 500ms (p95)
      - Page load time ≤ 2s
      - No memory leaks detected
    approval_required: false
    approver: Automated performance tests

success_metrics:
  quantitative:
    - metric: "Test pass rate"
      target: "100% passing"
      measurement: "CI/CD test results"
    - metric: "Test execution time"
      target: "Full test suite ≤ 10 minutes"
      measurement: "CI/CD pipeline duration"
    - metric: "Test coverage"
      target: "≥ 80% line coverage, ≥ 90% critical paths"
      measurement: "Coverage report"
    - metric: "API response time (p95)"
      target: "≤ 500ms"
      measurement: "Performance test results"
    - metric: "Database query time (p95)"
      target: "≤ 100ms"
      measurement: "Query profiling"

  qualitative:
    - metric: "Test quality"
      target: "Tests validate behavior, not implementation"
      measurement: "Test code review"
    - metric: "Error handling"
      target: "All error scenarios covered"
      measurement: "Exception handling review"

---

## Phase 8: Code Review

validation_gates:
  - gate_id: REV-001
    name: "No Blocking Issues"
    type: code_review
    required: true
    criteria:
      - Zero blocker-level issues
      - Security vulnerabilities addressed
      - Performance issues resolved
    approval_required: true
    approver: Senior Developer

  - gate_id: REV-002
    name: "Tech Debt Documented"
    type: code_review
    required: true
    criteria:
      - All tech debt items logged in backlog
      - Justification provided for deferred work
      - Timeline for tech debt resolution
    approval_required: false
    approver: Tech Lead

success_metrics:
  quantitative:
    - metric: "Blocker issues"
      target: "0 blockers"
      measurement: "Count of blocker-level issues"
    - metric: "Critical issues"
      target: "≤ 2 critical issues"
      measurement: "Count of critical-level issues"
    - metric: "Code review turnaround time"
      target: "≤ 24 hours"
      measurement: "Time from review request to approval"
    - metric: "Review iterations"
      target: "≤ 3 rounds of feedback"
      measurement: "Count of review comments cycles"

  qualitative:
    - metric: "Code quality"
      target: "Maintainable, follows SOLID principles"
      measurement: "Code review rubric score ≥ 8/10"
    - metric: "Security posture"
      target: "No security vulnerabilities introduced"
      measurement: "Security scan (Snyk, Dependabot)"
    - metric: "Design patterns"
      target: "Appropriate patterns for the problem"
      measurement: "Architecture review feedback"

---

## Phase 9: Configuration

validation_gates:
  - gate_id: CFG-001
    name: "Environment Variables Set"
    type: configuration
    required: true
    criteria:
      - All required env vars documented
      - Secrets stored in Secrets Manager
      - Config synced to Parameter Store
    approval_required: false
    approver: DevOps Engineer

  - gate_id: CFG-002
    name: "Secrets Rotation Configured"
    type: security
    required: true
    criteria:
      - Secret rotation policies enabled
      - DB credentials rotate every 30 days
      - API keys rotate every 90 days
    approval_required: true
    approver: Security Team

success_metrics:
  quantitative:
    - metric: "Config coverage"
      target: "100% of required configs defined"
      measurement: "Config validation script"
    - metric: "Secrets in code"
      target: "0 hardcoded secrets"
      measurement: "git-secrets scan"

  qualitative:
    - metric: "Config management"
      target: "All configs version-controlled"
      measurement: "Config templates in Git"
    - metric: "Secret security"
      target: "All secrets encrypted at rest"
      measurement: "AWS Secrets Manager encryption"

---

## Phase 10: Deployment

validation_gates:
  - gate_id: DEP-001
    name: "Pre-Deployment Checklist Complete"
    type: deployment_readiness
    required: true
    criteria:
      - All tests passing
      - Code review approved
      - Security scan passed
      - Deployment runbook ready
    approval_required: true
    approver: Tech Lead + DevOps

  - gate_id: DEP-002
    name: "Infrastructure Deployed"
    type: infrastructure
    required: true
    criteria:
      - CDK stacks deployed successfully
      - All health checks passing
      - Monitoring dashboards configured
    approval_required: false
    approver: Automated CDK deployment

  - gate_id: DEP-003
    name: "Smoke Tests Passing"
    type: post_deployment_testing
    required: true
    criteria:
      - API endpoints responding
      - Database connectivity confirmed
      - Authentication flow working
    approval_required: false
    approver: Automated smoke tests

  - gate_id: DEP-004
    name: "Production Approval"
    type: business_approval
    required: true
    criteria:
      - UAT completed in staging
      - Product Owner sign-off
      - Go/No-go decision made
    approval_required: true
    approver: Product Owner + Tech Lead
    applies_to: production_only

success_metrics:
  quantitative:
    - metric: "Deployment success rate"
      target: "≥ 95% successful deployments"
      measurement: "CI/CD deployment logs"
    - metric: "Rollback rate"
      target: "≤ 10% of deployments"
      measurement: "Count of rollbacks / total deployments"
    - metric: "Deployment time"
      target: "≤ 20 minutes for full stack"
      measurement: "CI/CD pipeline duration"
    - metric: "Infrastructure drift"
      target: "0 drift detected"
      measurement: "CloudFormation drift detection"
    - metric: "Post-deployment errors"
      target: "≤ 5 errors in first 24 hours"
      measurement: "CloudWatch error logs"

  qualitative:
    - metric: "Deployment confidence"
      target: "Team confident in deployment process"
      measurement: "Retrospective feedback"
    - metric: "Rollback readiness"
      target: "Rollback procedure tested and documented"
      measurement: "Runbook review"
    - metric: "Monitoring coverage"
      target: "All critical metrics monitored"
      measurement: "CloudWatch dashboard review"

---

## Phase 11: Infrastructure Testing

validation_gates:
  - gate_id: INF-001
    name: "Health Checks Passing"
    type: infrastructure_validation
    required: true
    criteria:
      - All AWS resources healthy
      - Database connections working
      - API endpoints responding
    approval_required: false
    approver: Automated health checks

  - gate_id: INF-002
    name: "Security Scan Passed"
    type: security_validation
    required: true
    criteria:
      - No critical security vulnerabilities
      - IAM permissions follow least privilege
      - Encryption enabled for data at rest
    approval_required: true
    approver: Security Team

success_metrics:
  quantitative:
    - metric: "Security vulnerabilities"
      target: "0 critical, ≤ 5 medium"
      measurement: "Prowler/ScoutSuite scan results"
    - metric: "Infrastructure uptime"
      target: "99.9% availability"
      measurement: "CloudWatch uptime metrics"
    - metric: "Resource utilization"
      target: "≤ 70% average CPU/memory"
      measurement: "CloudWatch resource metrics"

  qualitative:
    - metric: "Infrastructure resilience"
      target: "Survives single AZ failure"
      measurement: "Chaos engineering tests"
    - metric: "Backup strategy"
      target: "Automated backups configured"
      measurement: "AWS Backup review"

---

## Project-Wide Success Criteria

overall_success_metrics:
  quantitative:
    - metric: "On-time delivery"
      target: "±10% of estimated timeline"
      measurement: "Project completion date vs estimate"
    - metric: "Budget adherence"
      target: "±15% of estimated budget"
      measurement: "Total cost vs estimate"
    - metric: "Test coverage"
      target: "≥ 80% overall"
      measurement: "Combined coverage report"
    - metric: "Production incidents"
      target: "≤ 2 P1 incidents in first month"
      measurement: "Incident tracking system"
    - metric: "User adoption"
      target: "≥ 70% of target users active in Month 1"
      measurement: "Analytics dashboard"
    - metric: "API performance"
      target: "p95 latency ≤ 500ms"
      measurement: "CloudWatch metrics"
    - metric: "System availability"
      target: "99.9% uptime"
      measurement: "CloudWatch uptime"

  qualitative:
    - metric: "Code quality"
      target: "Maintainable, well-documented codebase"
      measurement: "Code review feedback + SonarQube"
    - metric: "Team satisfaction"
      target: "Team satisfied with process and outcome"
      measurement: "Retrospective feedback"
    - metric: "Stakeholder satisfaction"
      target: "Product Owner satisfied with deliverables"
      measurement: "Stakeholder survey"
    - metric: "Technical debt"
      target: "Tech debt items documented and prioritized"
      measurement: "Backlog review"
    - metric: "Documentation completeness"
      target: "All systems documented for handoff"
      measurement: "Documentation review checklist"
    - metric: "Security compliance"
      target: "Meets all compliance requirements"
      measurement: "Compliance audit"

---

## Approval Gate Summary

gate_hierarchy:
  discovery:
    - DG-001 (Discovery Brief Complete)
  scoping:
    - SG-001 (Technical Architecture Approved)
    - SG-002 (Cost Estimate Approved)
    - SG-003 (CDK Constructs Reviewed)
  planning:
    - PG-001 (Sprint Plan Approved)
  development:
    - DEV-001 (Code Complete)
    - DEV-002 (Unit Tests Passing)
  testing:
    - TEST-001 (Unit Tests Passing)
    - TEST-002 (E2E Tests Passing)
    - TEST-003 (Performance Benchmarks Met)
  code_review:
    - REV-001 (No Blocking Issues)
    - REV-002 (Tech Debt Documented)
  configuration:
    - CFG-001 (Environment Variables Set)
    - CFG-002 (Secrets Rotation Configured)
  deployment:
    - DEP-001 (Pre-Deployment Checklist Complete)
    - DEP-002 (Infrastructure Deployed)
    - DEP-003 (Smoke Tests Passing)
    - DEP-004 (Production Approval)
  infrastructure_testing:
    - INF-001 (Health Checks Passing)
    - INF-002 (Security Scan Passed)

critical_path_gates:
  # These gates are on the critical path and must be passed
  - SG-001  # Architecture must be approved before development
  - DEV-002 # Tests must pass before code review
  - REV-001 # No blockers before deployment
  - DEP-004 # Production approval required
  - INF-002 # Security scan before go-live

---

## Notes

- All quantitative metrics should be tracked in project dashboard
- Qualitative metrics require human review and sign-off
- Gates marked `approval_required: true` need explicit approval before proceeding
- Production gates (DEP-004) have additional scrutiny
- Failed gates can be re-attempted after remediation
- Gate failures should trigger automated notifications to approvers
"""),
        ("12_llm_prompts.yaml", f"""# LLM Prompts Configuration

project_id: {args.adw_id}
environment: dev

## Overview
# This file defines LLM prompts, system prompts, model configurations, and tools
# for various agents in the software development workflow.

---

prompts:

  ## Discovery Agent
  - agent_id: discovery
    name: "Discovery Agent"
    description: "Analyzes client requirements and generates discovery brief"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.3
      max_tokens: 8000
      top_p: 0.9

    system_prompt: |
      You are an expert Technical Discovery Analyst specializing in software project scoping.

      Your role is to:
      1. Analyze client requirements and business goals
      2. Identify technical constraints and opportunities
      3. Qualify the project for feasibility and value
      4. Generate comprehensive discovery briefs

      Key principles:
      - Ask clarifying questions when requirements are ambiguous
      - Focus on business outcomes, not just features
      - Identify risks and dependencies early
      - Provide realistic timeline and budget estimates
      - Consider scalability and maintainability from the start

      Output format:
      - Structured markdown document
      - Clear sections: Overview, Goals, Requirements, Risks, Timeline, Budget
      - Use tables for structured data (requirements matrix, risk register)
      - Include diagrams where helpful (user flows, architecture sketches)

    tools:
      - name: exa_search
        description: "Search for similar projects, technical research, market analysis"
        enabled: true
      - name: web_fetch
        description: "Fetch documentation, competitor analysis, industry standards"
        enabled: true
      - name: file_write
        description: "Write discovery brief to specs/{args.adw_id}/1_discovery_brief.md"
        enabled: true

    context_template: |
      # Client Information
      {{{{ client_info }}}}

      # Project Requirements
      {{{{ requirements }}}}

      # Constraints
      - Budget: {{{{ budget }}}}
      - Timeline: {{{{ timeline }}}}
      - Team: {{{{ team_size }}}} developers

      # Additional Context
      {{{{ additional_context }}}}

    few_shot_examples:
      - input: "I need a simple e-commerce site with product listings and checkout"
        output: |
          # Discovery Brief: E-commerce Platform

          ## Project Overview
          Client requests a simple e-commerce platform with core features:
          - Product catalog with search/filtering
          - Shopping cart functionality
          - Secure checkout with payment processing

          ## Success Criteria
          - Users can browse products (quantitative: page load < 2s)
          - Users can complete purchase (qualitative: intuitive UX)
          - Payment processing secure (compliance: PCI-DSS)

          ## Technical Approach
          - Frontend: React/Next.js for SEO and performance
          - Backend: Python FastAPI for API layer
          - Database: PostgreSQL for product catalog
          - Payments: Stripe integration
          - Hosting: AWS (ECS + RDS + CloudFront)

          ## Estimated Timeline: 8-12 weeks
          ## Estimated Budget: $40,000 - $60,000

---

  ## Scoping Agent
  - agent_id: scoping
    name: "Scoping Agent"
    description: "Generates technical specifications, architecture, and AWS service selections"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.2
      max_tokens: 16000
      top_p: 0.9

    system_prompt: |
      You are a Senior Solutions Architect specializing in AWS cloud architecture.

      Your role is to:
      1. Design scalable, secure, and cost-effective architectures
      2. Select appropriate AWS services for each requirement
      3. Define data models and API contracts
      4. Document security and compliance requirements
      5. Estimate costs with accuracy

      Key principles:
      - Prefer AWS-native services to minimize integration complexity
      - Follow AWS Well-Architected Framework (security, reliability, performance, cost, operational excellence)
      - Design for scalability from day one
      - Implement defense-in-depth security
      - Optimize for cost without sacrificing quality

      Output artifacts:
      - Architecture diagrams (Mermaid format)
      - AWS service specifications (YAML)
      - Data models (YAML + ERD)
      - User flows (YAML)
      - Cost estimates (Markdown)
      - Security requirements (Markdown)
      - CDK construct recommendations (Markdown)

    tools:
      - name: exa_search
        description: "Research AWS services, CDK constructs, best practices"
        enabled: true
      - name: aws_documentation
        description: "Fetch AWS service documentation, pricing, limits"
        enabled: true
      - name: file_read
        description: "Read discovery brief for context"
        enabled: true
      - name: file_write
        description: "Write scoping documents (architecture, data models, etc.)"
        enabled: true

    context_template: |
      # Discovery Brief
      {{{{ discovery_brief }}}}

      # Project Requirements
      {{{{ requirements }}}}

      # Constraints
      - Max monthly AWS cost: {{{{ max_monthly_cost }}}}
      - Compliance: {{{{ compliance_requirements }}}}
      - SLA: {{{{ sla_requirements }}}}

      # Preferences
      - Tech stack: {{{{ tech_stack }}}}
      - Deployment: {{{{ deployment_preferences }}}}

    guidance: |
      When selecting AWS services:
      1. Start with serverless (Lambda, DynamoDB, API Gateway) for simplicity
      2. Use RDS only if complex queries or transactions needed
      3. Use S3 + CloudFront for static assets
      4. Use Cognito for authentication unless SSO required
      5. Use SageMaker for ML workloads
      6. Use CloudWatch for monitoring (always)

      Cost optimization:
      - Use reserved instances for predictable workloads
      - Use auto-scaling for variable workloads
      - Use lifecycle policies for S3 storage
      - Use on-demand for development, reserved for production

---

  ## Planning Agent
  - agent_id: planning
    name: "Planning Agent"
    description: "Creates agile stories, sprint plans, and estimates"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.3
      max_tokens: 12000
      top_p: 0.9

    system_prompt: |
      You are an experienced Agile Project Manager and Product Owner.

      Your role is to:
      1. Break down technical specifications into user stories
      2. Estimate story complexity (story points)
      3. Organize stories into sprints
      4. Identify dependencies and risks
      5. Create detailed acceptance criteria

      Key principles:
      - Stories should be independently deployable (INVEST criteria)
      - Acceptance criteria should be testable
      - Estimate conservatively (include buffer for unknowns)
      - Front-load risky work to surface issues early
      - Balance technical debt with new features

      Output format:
      - Agile stories in YAML format
      - Sprint plan in Markdown
      - Dependency graph (Mermaid)
      - Risk register

    tools:
      - name: file_read
        description: "Read scoping docs for context"
        enabled: true
      - name: file_write
        description: "Write agile stories and sprint plans"
        enabled: true

    context_template: |
      # Technical Specifications
      {{{{ technical_specs }}}}

      # Sprint Configuration
      - Sprint duration: {{{{ sprint_duration }}}} weeks
      - Number of sprints: {{{{ num_sprints }}}}
      - Team velocity: {{{{ velocity }}}} points/sprint

      # Priorities
      {{{{ priorities }}}}

    story_template: |
      - id: {{{{ story_id }}}}
        title: "{{{{ title }}}}"
        description: |
          As a {{{{ user_role }}}},
          I want to {{{{ capability }}}},
          So that {{{{ benefit }}}}.

        acceptance_criteria:
          - {{{{ criterion_1 }}}}
          - {{{{ criterion_2 }}}}

        technical_notes: |
          {{{{ technical_implementation_notes }}}}

        story_points: {{{{ points }}}}
        priority: {{{{ priority }}}}
        dependencies: {{{{ dependency_story_ids }}}}

---

  ## Development Agent
  - agent_id: development
    name: "Development Agent"
    description: "Implements user stories with code, tests, and documentation"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.2
      max_tokens: 16000
      top_p: 0.9

    system_prompt: |
      You are an expert Full-Stack Software Engineer specializing in Python, TypeScript, and AWS.

      Your role is to:
      1. Implement user stories with production-quality code
      2. Write comprehensive unit tests (≥80% coverage)
      3. Document code with clear docstrings and comments
      4. Follow coding standards and best practices
      5. Commit code with meaningful commit messages

      Key principles:
      - Write clean, maintainable, self-documenting code
      - Test behavior, not implementation details
      - Handle errors gracefully with proper logging
      - Use type hints and validation (Pydantic, TypeScript)
      - Follow SOLID principles
      - Optimize for readability over cleverness

      Code quality standards:
      - Functions: ≤ 50 lines, single responsibility
      - Cyclomatic complexity: ≤ 10
      - Test coverage: ≥ 80%
      - No hardcoded secrets or magic numbers
      - All public functions have docstrings

    tools:
      - name: file_read
        description: "Read story details, existing code, specs"
        enabled: true
      - name: file_write
        description: "Write implementation code"
        enabled: true
      - name: edit
        description: "Edit existing code files"
        enabled: true
      - name: bash
        description: "Run tests, linters, formatters"
        enabled: true
      - name: grep
        description: "Search codebase for patterns"
        enabled: true

    context_template: |
      # Story Details
      {{{{ story }}}}

      # Acceptance Criteria
      {{{{ acceptance_criteria }}}}

      # Technical Context
      - Code location: trees/{args.adw_id}/{{{{ component }}}}
      - Tech stack: {{{{ tech_stack }}}}
      - Dependencies: {{{{ dependencies }}}}

      # Existing Code
      {{{{ related_files }}}}

    code_style_guide: |
      Python:
      - Use Black for formatting
      - Use Ruff for linting
      - Use type hints (mypy strict mode)
      - Docstrings: Google style

      TypeScript:
      - Use ESLint + Prettier
      - Strict mode enabled
      - JSDoc comments for public APIs

      General:
      - Meaningful variable names (no single letters except loop iterators)
      - Constants in UPPER_CASE
      - Private methods prefixed with underscore
      - Async functions clearly named (fetch_*, load_*, etc.)

---

  ## Testing Agent
  - agent_id: testing
    name: "Testing Agent"
    description: "Runs tests, analyzes failures, and auto-fixes issues"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.1
      max_tokens: 12000
      top_p: 0.9

    system_prompt: |
      You are a QA Engineer and Test Automation Specialist.

      Your role is to:
      1. Run unit tests and E2E tests
      2. Analyze test failures and error messages
      3. Identify root causes of failures
      4. Implement fixes to resolve test failures
      5. Validate fixes by re-running tests

      Key principles:
      - Read error messages carefully and completely
      - Identify patterns in failures (systemic vs one-off)
      - Fix root cause, not symptoms
      - Verify fix doesn't break other tests
      - Maximum retry attempts: Unit=4, E2E=2

      Test analysis approach:
      1. Read full error stack trace
      2. Identify failing line and function
      3. Check test expectations vs actual behavior
      4. Review recent code changes that might have caused failure
      5. Implement minimal fix
      6. Re-run tests to validate

    tools:
      - name: bash
        description: "Run pytest, jest, coverage reports"
        enabled: true
      - name: file_read
        description: "Read test files, implementation code, error logs"
        enabled: true
      - name: edit
        description: "Fix code to resolve test failures"
        enabled: true
      - name: grep
        description: "Search for related code patterns"
        enabled: true

    context_template: |
      # Test Results
      {{{{ test_results }}}}

      # Failure Details
      {{{{ failure_details }}}}

      # Recent Changes
      {{{{ git_diff }}}}

      # Retry Attempt
      Attempt {{{{ retry_attempt }}}} of {{{{ max_retries }}}}

    retry_strategy: |
      Attempt 1: Fix obvious errors (typos, import issues)
      Attempt 2: Fix logic errors based on stack trace
      Attempt 3: Review test expectations vs implementation
      Attempt 4: Escalate to human review if still failing

---

  ## Code Review Agent
  - agent_id: code_review
    name: "Code Review Agent"
    description: "Reviews code quality, identifies issues, and suggests improvements"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.3
      max_tokens: 16000
      top_p: 0.9

    system_prompt: |
      You are a Senior Staff Engineer conducting a thorough code review.

      Your role is to:
      1. Review code for quality, security, and best practices
      2. Classify issues by severity (blocker, critical, tech-debt, nit)
      3. Provide specific, actionable feedback
      4. Auto-fix blocker issues when possible
      5. Document tech debt for future work

      Review checklist:
      - Security: No hardcoded secrets, proper input validation, secure auth
      - Performance: Efficient algorithms, proper caching, no N+1 queries
      - Maintainability: Clear naming, DRY principle, proper abstraction
      - Testing: Adequate coverage, meaningful tests, edge cases covered
      - Documentation: Docstrings, comments for complex logic, README updated
      - Error handling: Graceful degradation, proper logging, user-friendly errors

      Issue severity:
      - BLOCKER: Prevents deployment (security vuln, broken functionality)
      - CRITICAL: Serious issue but workaround exists (performance, maintainability)
      - TECH_DEBT: Should be fixed eventually (code smell, minor refactor)
      - NIT: Nice-to-have improvements (naming, comments)

    tools:
      - name: file_read
        description: "Read code files for review"
        enabled: true
      - name: edit
        description: "Auto-fix blocker issues"
        enabled: true
      - name: bash
        description: "Run security scans, linters"
        enabled: true
      - name: file_write
        description: "Write review summary"
        enabled: true

    context_template: |
      # Files Changed
      {{{{ changed_files }}}}

      # Diff
      {{{{ git_diff }}}}

      # Story Context
      {{{{ story_details }}}}

      # Automated Checks
      - Linter: {{{{ linter_results }}}}
      - Security scan: {{{{ security_scan_results }}}}
      - Coverage: {{{{ coverage_percentage }}}}%

    review_format: |
      # Code Review: {{{{ story_id }}}}

      ## Summary
      {{{{ high_level_assessment }}}}

      ## Issues Found

      ### BLOCKER ({{{{ blocker_count }}}})
      - [File:Line] Description and fix

      ### CRITICAL ({{{{ critical_count }}}})
      - [File:Line] Description and recommendation

      ### TECH_DEBT ({{{{ tech_debt_count }}}})
      - [File:Line] Description and future improvement

      ## Positive Highlights
      - Good practices observed

      ## Overall Assessment
      ✅ APPROVED / ⏸️ NEEDS WORK / ❌ BLOCKED

---

  ## Infrastructure Testing Agent
  - agent_id: infrastructure_testing
    name: "Infrastructure Testing Agent"
    description: "Validates AWS infrastructure deployment and health"

    model:
      provider: anthropic
      model_id: claude-sonnet-4-5-20250929
      temperature: 0.1
      max_tokens: 8000
      top_p: 0.9

    system_prompt: |
      You are a DevOps Engineer and Cloud Infrastructure Specialist.

      Your role is to:
      1. Validate AWS resources are deployed correctly
      2. Run health checks on all services
      3. Verify security configurations
      4. Check for infrastructure drift
      5. Generate infrastructure test report

      Validation checklist:
      - All CloudFormation stacks deployed successfully
      - No stack drift detected
      - All health checks passing
      - Security groups properly configured
      - IAM roles follow least privilege
      - Encryption enabled for data at rest
      - Backups configured
      - Monitoring dashboards created
      - Alarms configured

      Security validation:
      - Run Prowler security scan
      - Check for public S3 buckets
      - Verify MFA enabled on root account
      - Check for unused IAM users
      - Validate password policies

    tools:
      - name: bash
        description: "Run AWS CLI commands, security scans"
        enabled: true
      - name: file_read
        description: "Read CDK output, CloudFormation templates"
        enabled: true
      - name: file_write
        description: "Write infrastructure test report"
        enabled: true

    context_template: |
      # Deployment Details
      - Environment: {{{{ environment }}}}
      - Region: {{{{ region }}}}
      - Stack names: {{{{ stack_names }}}}

      # Expected Resources
      {{{{ expected_resources }}}}

      # Security Requirements
      {{{{ security_requirements }}}}

---

## Model Selection Guide

model_recommendations:
  discovery_scoping:
    recommended_model: claude-sonnet-4-5-20250929
    rationale: "Complex reasoning, architecture design, cost analysis"
    alternative: claude-opus-4-20250514
    temperature: 0.2-0.3

  development:
    recommended_model: claude-sonnet-4-5-20250929
    rationale: "Code generation, balanced quality and speed"
    alternative: claude-sonnet-4-20250514
    temperature: 0.1-0.2

  testing_review:
    recommended_model: claude-sonnet-4-5-20250929
    rationale: "Analytical tasks, bug fixing, code review"
    temperature: 0.1

  documentation:
    recommended_model: claude-sonnet-4-5-20250929
    rationale: "Clear technical writing"
    temperature: 0.3-0.4

---

## Tool Configuration

default_tools:
  all_agents:
    - file_read
    - file_write
    - bash

  research_agents:
    - exa_search
    - web_fetch
    - aws_documentation

  development_agents:
    - edit
    - grep
    - glob

  infrastructure_agents:
    - aws_cli
    - cloudwatch

---

## Context Window Management

context_strategies:
  large_codebases:
    strategy: "Use grep/glob to find relevant files, read only what's needed"
    max_files_per_context: 10
    prioritize: "Changed files, related files, tests"

  long_documents:
    strategy: "Summarize first, then read sections as needed"
    chunk_size: 5000

  API_responses:
    strategy: "Extract only relevant fields"
    max_response_size: 2000

---

## Notes

- All prompts use Anthropic Claude models
- Temperature varies by task: creative (0.3-0.4), analytical (0.1-0.2)
- Tools are enabled per agent based on their role
- Context templates use {{{{ }}}} syntax for variable substitution
- Few-shot examples improve quality for complex tasks
- Retry strategies prevent infinite loops
""")
    ]

    print("\nCreating scoping documents...")
    for filename, content in files_to_create:
        file_path = specs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   [OK] Created: {file_path}")

    # Update state
    state.update_phase(
        "scoping",
        completed=False,
        ml_research=str(specs_dir / "2_ml_research.md"),
        user_flows=str(specs_dir / "3_user_flows.yaml"),
        data_models=str(specs_dir / "4_data_models.yaml"),
        aws_native_analysis=str(specs_dir / "5a_aws_native_analysis.md"),
        aws_services=str(specs_dir / "5_aws_services.yaml"),
        architecture=str(specs_dir / "6_architecture.mmd"),
        cost_estimate=str(specs_dir / "7_cost_estimate.md"),
        data_schema=str(specs_dir / "8_data_schema.mmd"),
        user_auth_rbac=str(specs_dir / "9_user_auth_rbac.md"),
        cdk_constructs=str(specs_dir / "10_cdk_constructs.md"),
        validation_gates=str(specs_dir / "11_validation_gates.yaml"),
        llm_prompts=str(specs_dir / "12_llm_prompts.yaml")
    )
    state.save()

    # Generate CDK configurations
    print("\n>>> Generating CDK configurations...")
    cdk_config_dir = specs_dir / "cdk_config"
    cdk_config_dir.mkdir(exist_ok=True)

    # Parse AWS services to extract infrastructure requirements
    import yaml
    aws_services_file = specs_dir / "5_aws_services.yaml"
    try:
        with open(aws_services_file, 'r') as f:
            aws_services_data = yaml.safe_load(f)

        # Extract infrastructure needs from services
        infra_requirements = {
            "infrastructure": {
                "compute": {},
                "storage": {},
                "database": {},
                "auth": {},
                "networking": {},
                "monitoring": {}
            }
        }

        # Parse services and populate requirements
        services = aws_services_data.get("services", [])
        for service in services:
            service_name = service.get("service", "")

            if service_name == "Lambda":
                infra_requirements["infrastructure"]["compute"]["serverless"] = True
                functions = service.get("functions", [])
                if functions:
                    first_func = functions[0]
                    infra_requirements["infrastructure"]["compute"]["runtime"] = first_func.get("runtime", "python3.11")
                    infra_requirements["infrastructure"]["compute"]["memory"] = first_func.get("memory", 512)
                    infra_requirements["infrastructure"]["compute"]["timeout"] = first_func.get("timeout", 30)

            elif service_name == "RDS":
                infra_requirements["infrastructure"]["database"]["relational"] = True
                config = service.get("config", {})
                infra_requirements["infrastructure"]["database"]["engine"] = config.get("engine", "postgres")
                infra_requirements["infrastructure"]["database"]["instanceClass"] = config.get("instanceClass", "db.t3.micro")

            elif service_name == "DynamoDB":
                infra_requirements["infrastructure"]["database"]["nosql"] = True

            elif service_name == "S3":
                infra_requirements["infrastructure"]["storage"]["objectStorage"] = True
                infra_requirements["infrastructure"]["storage"]["versioning"] = True

            elif service_name == "CloudFront":
                infra_requirements["infrastructure"]["storage"]["cdn"] = True

            elif service_name == "Cognito":
                infra_requirements["infrastructure"]["auth"]["userPool"] = True

            elif service_name == "SageMaker":
                # ML services handled separately
                pass

        # Set networking defaults
        infra_requirements["infrastructure"]["networking"]["api"] = True
        infra_requirements["infrastructure"]["networking"]["apiType"] = "REST"

        # Generate CDK config YAML
        logger = logging.getLogger(args.adw_id)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(args.adw_id)

        cdk_config_path = generate_cdk_config_yaml(
            client_name=args.adw_id,
            environment="dev",
            project_requirements=infra_requirements,
            output_dir=str(cdk_config_dir),
            logger=logger
        )
        print(f"   [OK] Generated CDK config: {cdk_config_path}")

        # Generate CDK construct templates for identified services
        constructs_dir = cdk_config_dir / "constructs"
        constructs_dir.mkdir(exist_ok=True)

        generated_constructs = []
        for service in services:
            service_name = service.get("service", "")
            construct_type = None

            if service_name == "Lambda":
                construct_type = "lambda"
                construct_name = "APIHandler"
            elif service_name == "DynamoDB":
                construct_type = "dynamodb"
                construct_name = "DataStore"
            elif service_name == "S3":
                construct_type = "s3"
                construct_name = "Storage"
            elif service_name == "APIGateway" or (service_name == "Lambda" and construct_type == "lambda"):
                # Generate API Gateway construct if we have Lambda
                if construct_type == "lambda":
                    api_construct_path = generate_cdk_construct_template(
                        construct_name="API",
                        construct_type="apigateway",
                        output_dir=str(constructs_dir),
                        logger=logger
                    )
                    generated_constructs.append(api_construct_path)
                    print(f"   [OK] Generated construct: {Path(api_construct_path).name}")

            if construct_type:
                construct_path = generate_cdk_construct_template(
                    construct_name=construct_name,
                    construct_type=construct_type,
                    output_dir=str(constructs_dir),
                    logger=logger
                )
                generated_constructs.append(construct_path)
                print(f"   [OK] Generated construct: {Path(construct_path).name}")

        # Generate Parameter Store setup script
        parameters = {
            "project_name": args.adw_id,
            "environment": "dev",
            "discovery_brief": discovery_brief[:200] if len(discovery_brief) > 200 else discovery_brief
        }

        param_script_path = generate_parameter_store_script(
            parameters=parameters,
            prefix=f"/sdaw/{args.adw_id}/dev",
            output_dir=str(cdk_config_dir),
            logger=logger
        )
        print(f"   [OK] Generated Parameter Store script: {Path(param_script_path).name}")

        # Create infrastructure config and update state
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

    print(f"\n[SUCCESS] Scoping templates created!")
    print(f"\nReview files in: {specs_dir}")
    print(f"\nNext: uv run adws/adw_planning.py --adw-id {args.adw_id}")


if __name__ == "__main__":
    main()
