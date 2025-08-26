---
created: 2025-08-26T12:32:21Z
last_updated: 2025-08-26T12:32:21Z
version: 1.0
author: Claude Code PM System
---

# Technology Context

## Current Technology Stack

### Development Environment
- **Operating System:** macOS (Darwin 24.6.0)
- **IDE:** IntelliJ IDEA (configured for multi-language support)
- **Version Control:** Git with GitHub integration
- **Shell:** Bash (for automation scripts)

### Project Management Technology
- **Claude Code PM:** Comprehensive project management system
- **GitHub CLI:** Issue management and repository operations
- **GitHub Extensions:** gh-sub-issue for hierarchical issue management
- **Markdown:** Documentation and specification format

## Committed Technology Decisions

### Backend Technology Stack
- **Primary Language:** Python 3.9+ (confirmed for entire application)
- **Infrastructure:** AWS CDK (Python) for Infrastructure as Code
- **Cloud Provider:** Amazon Web Services (AWS)
- **Primary Region:** ap-south-1 (Asia Pacific - Mumbai)
- **Architecture:** Event-driven serverless microservices

### AWS Services Architecture
```yaml
Core Services:
  - AWS Lambda: Serverless compute for business logic
  - DynamoDB: NoSQL database for operational data
  - EventBridge: Event routing and scheduling
  - Step Functions: Workflow orchestration
  - SQS: Message queuing and async processing
  - API Gateway: HTTP/REST API endpoints

Data & Storage:
  - S3: Object storage for files and backups
  - DynamoDB: Primary operational database
  - Parquet: Historical data storage format
  - CloudWatch Logs: Application logging

Security & Monitoring:
  - Cognito: User authentication and management
  - IAM: Fine-grained access control
  - CloudWatch: Monitoring and alerting
  - Systems Manager: Configuration management
```

### Regional Configuration
- **Primary Region:** ap-south-1 (Asia Pacific - Mumbai)
- **Rationale:** Optimal latency for Indian financial markets
- **Compliance:** Indian data residency requirements
- **Market Timing:** IST (Indian Standard Time) optimization

## External Integrations

### Broker API Integrations (Planned)
#### Primary Broker: Zerodha
- **API:** Kite Connect API
- **SDK:** Python KiteConnect library
- **Features:** Order placement, market data, portfolio tracking
- **Authentication:** API key + access token

#### Secondary Brokers
- **Angel One:** SmartAPI integration
- **Finvasia:** Shoonya API integration  
- **Future:** Zebu and other Indian brokers

### Market Data Sources
- **Primary:** Zerodha market data feeds
- **Backup:** Alternative data providers for redundancy
- **Real-time:** WebSocket connections for live data
- **Historical:** REST API for backtesting data

## Development Tools & Frameworks

### Python Ecosystem
```yaml
Core Framework:
  - FastAPI: Modern async web framework
  - Pydantic: Data validation and serialization
  - SQLAlchemy: Database ORM (if needed)
  - Asyncio: Asynchronous programming

AWS Integration:
  - boto3: AWS SDK for Python
  - aws-cdk-lib: AWS CDK library
  - lambda-powertools: AWS Lambda utilities

Testing:
  - pytest: Testing framework
  - pytest-asyncio: Async testing support
  - moto: AWS service mocking
  - httpx: Async HTTP client for testing

Development:
  - black: Code formatting
  - flake8: Code linting
  - mypy: Static type checking
  - pre-commit: Git hooks for quality gates
```

### Infrastructure as Code
- **CDK Version:** AWS CDK v2 (latest)
- **Language:** Python CDK (not TypeScript)
- **Deployment:** Automated through CDK pipelines
- **Environment Management:** Separate stacks for dev/staging/prod

## Current Dependencies

### Project Management Dependencies
- **Git:** Version control and collaboration
- **GitHub CLI:** Repository and issue management
- **Bash:** Shell scripting and automation
- **Markdown:** Documentation format

### Development Dependencies (None Yet)
- **Current Count:** 0 packages (implementation not started)
- **Planned Count:** ~20-30 core dependencies
- **Security:** All dependencies will be vetted and pinned

## Database & Storage Strategy

### Primary Database: DynamoDB
```yaml
Table Design:
  - users: User profiles and authentication
  - baskets: Trading basket definitions
  - strategies: Individual strategy configurations
  - orders: Order tracking and lifecycle
  - positions: Current and historical positions
  - executions: Trade execution records

Indexes:
  - GSI: user_id for user-specific queries
  - LSI: timestamp for time-based queries
  - GSI: strategy_id for strategy-specific data
```

### Time-Series Data: Parquet + S3
- **Format:** Apache Parquet for efficiency
- **Storage:** S3 buckets with lifecycle policies
- **Access:** Athena for ad-hoc querying
- **Retention:** Configurable data retention policies

## Development Environment Setup

### Required Local Tools
```bash
# Version Control
git --version              # Git for source control
gh --version              # GitHub CLI for issues

# Python Development (Future)
python3 --version         # Python 3.9+
pip --version             # Package management
aws --version             # AWS CLI for deployment

# Development Environment
code --version            # VS Code (optional)
# OR IntelliJ IDEA (currently configured)
```

### AWS Environment Setup (Future)
```bash
# AWS Configuration
aws configure             # Set up credentials
aws sts get-caller-identity  # Verify authentication
aws cdk --version        # CDK CLI installation

# Region Configuration
export AWS_DEFAULT_REGION=ap-south-1
export AWS_REGION=ap-south-1
```

## Security Considerations

### Authentication & Authorization
- **User Auth:** AWS Cognito with JWT tokens
- **API Auth:** API Gateway with Cognito integration
- **Service Auth:** IAM roles for service-to-service
- **External APIs:** Secure credential storage in Systems Manager

### Data Security
- **Encryption at Rest:** DynamoDB and S3 encryption enabled
- **Encryption in Transit:** TLS 1.2+ for all communications
- **API Keys:** Stored in AWS Systems Manager Parameter Store
- **Network Security:** VPC configuration for Lambda functions

## Performance & Scalability

### Performance Targets
- **API Response:** <500ms for order placement
- **Data Processing:** Real-time market data updates
- **Concurrent Users:** 1000+ simultaneous active users
- **Order Throughput:** 10,000+ orders per second capacity

### Scalability Architecture
- **Auto-scaling:** Lambda automatic scaling
- **Database:** DynamoDB on-demand billing for elasticity
- **Message Processing:** SQS for handling traffic spikes
- **CDN:** CloudFront for static content delivery

## Monitoring & Observability

### Logging Strategy
```yaml
Application Logs:
  - Structured JSON logging
  - CloudWatch Logs integration
  - Log aggregation and search

Metrics:
  - Business KPIs (orders, P&L, execution rates)
  - Technical metrics (latency, errors, throughput)
  - Custom CloudWatch metrics

Alerting:
  - CloudWatch Alarms for critical metrics
  - SNS notifications for alerts
  - Slack/Email integration for teams
```

### Debugging & Troubleshooting
- **X-Ray:** Distributed tracing for requests
- **CloudWatch Insights:** Log analysis and querying
- **Custom Dashboards:** Real-time operational visibility
- **Health Checks:** Synthetic monitoring for critical paths

## Future Technology Considerations

### Potential Additions
- **Machine Learning:** SageMaker for strategy optimization
- **Real-time Analytics:** Kinesis for stream processing
- **Graph Database:** Neptune for relationship analysis
- **Container Orchestration:** ECS/EKS if needed for specific services

### Technology Evolution Path
1. **Phase 1:** Basic serverless implementation (current plan)
2. **Phase 2:** Advanced analytics and ML integration
3. **Phase 3:** Multi-region deployment for global markets
4. **Phase 4:** High-frequency trading optimizations