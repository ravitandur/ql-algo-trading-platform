# Deployment Guide - Options Strategy Lifecycle Platform

This document provides comprehensive deployment instructions for the Options Strategy Lifecycle Platform, including setup, configuration, deployment procedures, monitoring, and troubleshooting.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Configuration](#configuration)
- [Deployment Process](#deployment-process)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)
- [Maintenance](#maintenance)
- [FAQ](#faq)

## Overview

The Options Strategy Lifecycle Platform is deployed using AWS CDK (Cloud Development Kit) with infrastructure as code principles. The platform is designed for the Indian market with deployment to the `ap-south-1` (Asia Pacific - Mumbai) region to ensure data residency compliance.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Options Strategy Platform                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Web App   │  │  API Gateway │  │  Monitoring │            │
│  │   (React)   │  │   (REST)    │  │ (CloudWatch)│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Lambda    │  │  DynamoDB   │  │     VPC     │            │
│  │ Functions   │  │   Tables    │  │  Networking │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Environments

- **dev** - Development environment for testing
- **staging** - Pre-production environment for integration testing
- **prod** - Production environment for live trading

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.0+)
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. **Node.js** (v18.0+)
   ```bash
   # Using nvm
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 18
   nvm use 18
   ```

3. **Python** (v3.11+)
   ```bash
   # On macOS with Homebrew
   brew install python@3.11
   
   # On Ubuntu
   sudo apt-get install python3.11 python3.11-pip
   ```

4. **AWS CDK** (v2.100+)
   ```bash
   npm install -g aws-cdk@latest
   ```

### AWS Account Setup

1. **AWS Account Requirements**
   - Valid AWS account with appropriate permissions
   - Access to `ap-south-1` region
   - Sufficient service limits for resources

2. **IAM Permissions**
   Required permissions for deployment:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "cloudformation:*",
           "iam:*",
           "lambda:*",
           "apigateway:*",
           "dynamodb:*",
           "ec2:*",
           "logs:*",
           "cloudwatch:*",
           "sns:*",
           "ssm:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **AWS CLI Configuration**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Default region: ap-south-1
   # Default output format: json
   ```

## Environment Setup

### Clone Repository

```bash
git clone https://github.com/your-org/options-strategy-lifecycle.git
cd options-strategy-lifecycle
```

### Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify CDK installation
cdk --version
```

### Environment Variables

Create environment-specific configuration:

```bash
# For development
export CDK_ENVIRONMENT=dev
export CDK_DEFAULT_REGION=ap-south-1
export NOTIFICATION_EMAIL=your-email@company.com

# For staging
export CDK_ENVIRONMENT=staging
export STAGING_NOTIFICATION_EMAIL=staging-alerts@company.com

# For production
export CDK_ENVIRONMENT=prod
export PROD_NOTIFICATION_EMAIL=prod-alerts@company.com
```

## Configuration

### Environment Configuration

The platform uses environment-specific configuration located in `config/environments.py`. Key configuration areas:

#### Development Environment
```python
dev_config = EnvironmentConfig(
    env_name="dev",
    aws_region="ap-south-1",
    networking=NetworkingConfig(
        vpc_cidr="10.0.0.0/16",
        max_azs=2,
        enable_nat_gateway=True
    ),
    resources=ResourceConfig(
        lambda_memory_size=512,
        lambda_timeout=30,
        rds_instance_class="db.t3.micro"
    )
)
```

#### Production Environment
```python
prod_config = EnvironmentConfig(
    env_name="prod",
    aws_region="ap-south-1",
    networking=NetworkingConfig(
        vpc_cidr="10.2.0.0/16", 
        max_azs=3,
        enable_nat_gateway=True
    ),
    resources=ResourceConfig(
        lambda_memory_size=2048,
        lambda_timeout=300,
        rds_instance_class="db.r5.large"
    )
)
```

### Customization Options

Modify configuration in `config/environments.py`:

1. **Resource Sizing**: Adjust compute and memory settings
2. **Networking**: Configure VPC CIDR, subnets, and AZ count
3. **Security**: Enable/disable security features
4. **Monitoring**: Set log retention and monitoring levels
5. **Cost Optimization**: Configure cost-saving features

## Deployment Process

### Quick Start

For a standard development deployment:

```bash
# Deploy to development
./scripts/deploy.sh dev

# Deploy to staging with diff preview
./scripts/deploy.sh staging --diff

# Deploy to production with approval
./scripts/deploy.sh prod --approve
```

### Step-by-Step Deployment

#### 1. Pre-deployment Validation

```bash
# Check prerequisites
./scripts/deploy.sh dev --dry-run

# Review what will be deployed
cdk synth
cdk diff
```

#### 2. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/ap-south-1
```

#### 3. Deploy Infrastructure

```bash
# Development
./scripts/deploy.sh dev

# Staging
./scripts/deploy.sh staging --diff

# Production (with extra confirmations)
./scripts/deploy.sh prod --approve
```

#### 4. Post-deployment Verification

```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name OptionsStrategyPlatform-Dev

# Verify resources
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=OptionsStrategyPlatform"
```

### Deployment Options

#### Command Line Options

```bash
# Available options for deploy.sh
--diff              # Show differences before deploying
--dry-run           # Perform validation without deployment
--approve           # Skip manual approval prompts
--rollback          # Rollback to previous version
--skip-synth        # Skip CDK synthesis
--skip-validation   # Skip pre-deployment checks
--no-notify         # Disable notifications
--timeout SECONDS   # Set deployment timeout
```

#### Environment Variables

```bash
# Core configuration
CDK_ENVIRONMENT=dev|staging|prod
CDK_DEFAULT_ACCOUNT=123456789012
CDK_DEFAULT_REGION=ap-south-1

# Notification settings
NOTIFICATION_EMAIL=alerts@company.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Security settings
SKIP_VALIDATION=false  # Set to true to skip security checks
```

### CI/CD Integration

The platform includes GitHub Actions workflows for automated deployment:

#### Manual Deployment Workflow

```yaml
name: Deploy to Environment
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - dev
          - staging
          - prod
```

#### Automated Deployment Workflow

```yaml
name: Continuous Deployment
on:
  push:
    branches:
      - main      # Deploy to dev
      - staging   # Deploy to staging
      - prod      # Deploy to production
```

## Monitoring and Observability

### CloudWatch Dashboards

The platform automatically creates comprehensive monitoring dashboards:

#### Executive Dashboard
- Business metrics and KPIs
- Platform health overview
- Trading volume statistics
- User activity metrics

**Access**: AWS Console → CloudWatch → Dashboards → `OptionsStrategy-Executive-{env}`

#### Operations Dashboard
- API Gateway metrics (requests, latency, errors)
- Lambda function performance
- Database performance metrics
- System availability metrics

**Access**: AWS Console → CloudWatch → Dashboards → `OptionsStrategy-Operations-{env}`

#### Technical Dashboard
- Infrastructure metrics (VPC, security)
- Log analysis and error tracking
- Performance deep-dive metrics
- Resource utilization

**Access**: AWS Console → CloudWatch → Dashboards → `OptionsStrategy-Technical-{env}`

### Alerts and Notifications

#### Alert Types

1. **Critical Alerts** (P1)
   - API 5xx errors > 10 per 5 minutes
   - Lambda error rate > 10 per 5 minutes
   - Database connection failures

2. **Warning Alerts** (P2/P3)
   - API 4xx errors > 50 per 5 minutes
   - Lambda duration > 30 seconds
   - High resource utilization

3. **Security Alerts**
   - Suspicious network activity
   - Failed authentication attempts
   - Security group changes

4. **Cost Alerts**
   - Budget threshold exceeded
   - Unexpected cost increases
   - Resource usage spikes

#### Notification Channels

- **Email**: Configured via `NOTIFICATION_EMAIL` environment variable
- **Slack**: Configured via `SLACK_WEBHOOK_URL` environment variable
- **SNS**: Automatic SNS topics created for each environment

### Log Management

#### Log Groups

- `/aws/options-strategy/{env}/application` - Application logs
- `/aws/options-strategy/{env}/monitoring` - Monitoring logs
- `/aws/options-strategy/{env}/trading` - Trading activity logs
- `/aws/options-strategy/{env}/performance` - Performance metrics
- `/aws/options-strategy/{env}/errors` - Error logs
- `/aws/options-strategy/{env}/audit` - Compliance audit logs

#### Log Retention

- **Development**: 7 days
- **Staging**: 30 days
- **Production**: 90 days

#### Log Analysis Queries

Pre-configured CloudWatch Logs Insights queries:

```sql
-- Error Analysis
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
| sort @timestamp desc

-- Performance Analysis
fields @timestamp, @duration
| filter @duration > 1000
| stats avg(@duration), max(@duration) by bin(5m)

-- Trading Volume Analysis
fields @timestamp, @message
| filter @message like /TRADE_EXECUTED/
| stats count() as trade_count by bin(1h)
```

## Security Considerations

### Data Residency Compliance

- All resources deployed in `ap-south-1` region
- Data encryption at rest and in transit
- Compliance with Indian market data regulations

### Network Security

- VPC with private subnets for application components
- Security groups with least privilege access
- Network ACLs for additional layer of protection
- VPC Flow Logs for network monitoring

### Access Control

- IAM roles with minimum required permissions
- Service-to-service authentication via IAM roles
- API Gateway with authentication and authorization
- Parameter Store for secure configuration management

### Security Monitoring

- CloudTrail for API activity logging
- VPC Flow Logs for network monitoring
- Security group change notifications
- Failed authentication attempt tracking

### Secrets Management

- AWS Parameter Store for configuration
- No hardcoded secrets in code
- Environment-specific secret isolation
- Automatic secret rotation where possible

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Issues

**Error**: `CDKToolkit stack not found`

**Solution**:
```bash
cdk bootstrap aws://ACCOUNT-NUMBER/ap-south-1
```

#### 2. Permission Denied Errors

**Error**: `User is not authorized to perform: cloudformation:CreateStack`

**Solution**: Ensure IAM user has required permissions or use appropriate AWS profile:
```bash
aws configure --profile production
export AWS_PROFILE=production
```

#### 3. Resource Limit Exceeded

**Error**: `VPC limit exceeded in region ap-south-1`

**Solution**: Request service limit increase or clean up unused resources:
```bash
aws ec2 describe-vpcs --region ap-south-1
aws ec2 delete-vpc --vpc-id vpc-xxxxxxxx
```

#### 4. Dependency Resolution Errors

**Error**: `Unable to resolve dependencies`

**Solution**: 
```bash
pip install --upgrade -r requirements.txt
cdk synth --debug
```

### Deployment Failures

#### Stack Creation Failed

1. Check CloudFormation stack events:
   ```bash
   aws cloudformation describe-stack-events --stack-name OptionsStrategyPlatform-Dev
   ```

2. Review deployment logs:
   ```bash
   tail -f logs/deploy_YYYYMMDD_HHMMSS.log
   ```

3. Check resource limits and quotas:
   ```bash
   aws service-quotas list-service-quotas --service-code ec2
   ```

#### Rollback Required

1. Automatic rollback during deployment:
   ```bash
   ./scripts/deploy.sh dev --rollback
   ```

2. Manual rollback to previous version:
   ```bash
   aws cloudformation cancel-update-stack --stack-name OptionsStrategyPlatform-Dev
   aws cloudformation continue-update-rollback --stack-name OptionsStrategyPlatform-Dev
   ```

### Performance Issues

#### High Latency

1. Check CloudWatch metrics:
   - API Gateway latency metrics
   - Lambda duration metrics
   - Database performance metrics

2. Review logs for slow operations:
   ```bash
   aws logs start-query --log-group-name "/aws/options-strategy/prod/performance" \
     --start-time $(date -d '1 hour ago' +%s) \
     --end-time $(date +%s) \
     --query-string 'fields @timestamp, @duration | filter @duration > 1000'
   ```

#### Resource Exhaustion

1. Monitor CloudWatch metrics for:
   - Lambda memory utilization
   - Database connections
   - API Gateway throttling

2. Scale resources if needed:
   - Increase Lambda memory allocation
   - Increase database instance size
   - Enable auto-scaling where supported

## Rollback Procedures

### Automatic Rollback

The deployment script includes automatic rollback capabilities:

```bash
# Rollback current deployment if it fails
./scripts/deploy.sh prod --rollback
```

### Manual Rollback Steps

#### 1. Identify Target Version

```bash
# List CloudFormation stack events
aws cloudformation describe-stack-events --stack-name OptionsStrategyPlatform-Prod

# Identify last successful deployment
aws cloudformation list-stacks --stack-status-filter UPDATE_COMPLETE CREATE_COMPLETE
```

#### 2. Rollback Infrastructure

```bash
# Using CloudFormation
aws cloudformation cancel-update-stack --stack-name OptionsStrategyPlatform-Prod
aws cloudformation continue-update-rollback --stack-name OptionsStrategyPlatform-Prod
```

#### 3. Verify Rollback

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name OptionsStrategyPlatform-Prod

# Run health checks
./scripts/deploy.sh prod --dry-run
```

### Emergency Procedures

#### Complete Environment Destruction

⚠️ **WARNING**: This will permanently delete all resources!

```bash
# Backup data first
./scripts/destroy.sh prod --backup-data

# Destroy environment
./scripts/destroy.sh prod
```

#### Partial Resource Recovery

```bash
# Destroy only specific stacks
cdk destroy OptionsStrategyPlatform-Prod-Monitoring
cdk destroy OptionsStrategyPlatform-Prod-Security

# Redeploy specific components
cdk deploy OptionsStrategyPlatform-Prod-Monitoring
```

## Maintenance

### Regular Maintenance Tasks

#### Weekly

1. **Review CloudWatch Dashboards**
   - Check for any anomalies or trends
   - Review error rates and performance metrics
   - Validate alert configurations

2. **Security Review**
   - Review CloudTrail logs for suspicious activity
   - Check for security group changes
   - Validate access patterns

#### Monthly

1. **Cost Optimization Review**
   - Analyze AWS billing and usage
   - Identify unused or underutilized resources
   - Review and optimize instance sizing

2. **Backup Verification**
   - Test backup and recovery procedures
   - Verify Parameter Store backups
   - Validate configuration snapshots

#### Quarterly

1. **Security Audit**
   - Review IAM policies and roles
   - Update security configurations
   - Perform penetration testing

2. **Performance Review**
   - Analyze performance trends
   - Plan capacity upgrades
   - Review and update SLAs

### Updates and Upgrades

#### CDK Version Updates

```bash
# Check current version
cdk --version

# Update CDK
npm update -g aws-cdk

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Test with synthesis
cdk synth
```

#### Infrastructure Updates

1. **Test in Development First**
   ```bash
   ./scripts/deploy.sh dev --diff
   ./scripts/deploy.sh dev
   ```

2. **Deploy to Staging**
   ```bash
   ./scripts/deploy.sh staging --diff
   ./scripts/deploy.sh staging
   ```

3. **Production Deployment**
   ```bash
   ./scripts/deploy.sh prod --diff
   # Review changes carefully
   ./scripts/deploy.sh prod --approve
   ```

## FAQ

### Q: How do I change the AWS region?

**A**: The platform is specifically designed for `ap-south-1` region for Indian market compliance. Changing the region requires:
1. Update `aws_region` in `config/environments.py`
2. Ensure compliance with local regulations
3. Update any region-specific configurations
4. Redeploy the infrastructure

### Q: Can I deploy to multiple AWS accounts?

**A**: Yes, set different AWS profiles for each environment:
```bash
# Development account
export AWS_PROFILE=development
./scripts/deploy.sh dev

# Production account  
export AWS_PROFILE=production
./scripts/deploy.sh prod
```

### Q: How do I customize resource naming?

**A**: Modify the naming conventions in `config/environments.py`:
```python
@property
def resource_prefix(self) -> str:
    return f"custom-prefix-{self.env_name}"
```

### Q: What if deployment takes too long?

**A**: Increase timeout and check for bottlenecks:
```bash
./scripts/deploy.sh dev --timeout 3600  # 1 hour timeout

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name OptionsStrategyPlatform-Dev
```

### Q: How do I enable additional monitoring?

**A**: Modify monitoring configuration in `config/environments.py`:
```python
monitoring=MonitoringConfig(
    enable_detailed_monitoring=True,
    enable_xray_tracing=True,
    enable_enhanced_monitoring=True
)
```

### Q: Can I use custom domain names?

**A**: Yes, configure domain settings in the API Gateway stack:
```python
# Add custom domain configuration
api_gateway_domain = apigateway.DomainName(
    self, "CustomDomain",
    domain_name="api.yourdomain.com",
    certificate=certificate
)
```

### Q: How do I scale for higher load?

**A**: Adjust resource configurations in `config/environments.py`:
```python
resources=ResourceConfig(
    lambda_memory_size=3008,  # Maximum Lambda memory
    ecs_cpu=4096,            # Increase ECS CPU
    rds_instance_class="db.r5.2xlarge"  # Larger RDS instance
)
```

### Q: How do I backup and restore the platform?

**A**: Use the built-in backup functionality:
```bash
# Backup before destroying
./scripts/destroy.sh prod --backup-data

# Manual backup
aws ssm get-parameters-by-path --path "/options-strategy/prod" --recursive > backup.json

# Restore parameters
aws ssm put-parameter --name "param-name" --value "param-value"
```

---

## Support and Contributing

For additional help:
- Check the [GitHub Issues](https://github.com/your-org/options-strategy-lifecycle/issues)
- Review [Architecture Documentation](./architecture.md)
- Contact the platform team: platform-team@company.com

---

*Last updated: $(date)*
*Version: 1.0.0*