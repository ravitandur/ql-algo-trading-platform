---
created: 2025-08-26T12:32:21Z
last_updated: 2025-08-26T12:32:21Z
version: 1.0
author: Claude Code PM System
---

# System Patterns & Architecture

## Observed Project Management Patterns

### Epic-Driven Development Pattern
The project demonstrates a sophisticated epic-based development approach:

#### Command Pattern Implementation
- **Structure:** Each PM command encapsulated as separate executable module
- **Location:** `.claude/commands/` with 47 distinct command implementations
- **Examples:** `epic-start.md`, `prd-new.md`, `context-create.md`
- **Benefits:** Modular, extensible, self-documenting workflow

#### Agent-Based Task Automation
- **Implementation:** Specialized AI agents for different development tasks
- **Location:** `.claude/agents/` with 4 specialized agents
- **Examples:** `code-analyzer.md`, `test-runner.md`, `parallel-worker.md`
- **Benefits:** Context optimization, parallel execution, specialized expertise

#### Sequential Task Decomposition
- **Pattern:** Large features broken into sequential, dependency-ordered tasks
- **Implementation:** 34 tasks for options-strategy-lifecycle epic
- **Dependencies:** Each task explicitly depends on previous task completion
- **GitHub Integration:** Direct correlation between tasks and GitHub issues

## Planned Application Architecture Patterns

### Event-Driven Microservices Architecture

#### Core Trading Engine Pattern
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   EventBridge       │───▶│   Lambda Functions  │───▶│   DynamoDB Tables   │
│   (Scheduling)      │    │   (Business Logic)  │    │   (Data Storage)    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Time-Based        │    │   Step Functions    │    │   SQS Queues        │
│   Strategy Triggers │    │   (Orchestration)   │    │   (Async Processing)│
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

#### Strategy Pattern for Trading Logic
- **Base Strategy Interface:** Abstract strategy class for all trading algorithms
- **Concrete Implementations:** Specific strategies (straddles, spreads, etc.)
- **Strategy Registry:** Dynamic strategy loading and configuration
- **Runtime Selection:** User-selectable strategies with parameters

#### Broker Abstraction Pattern
```python
# Abstract Broker Interface
class BrokerInterface:
    def place_order(self, order: Order) -> OrderResult
    def get_positions(self, account: Account) -> List[Position]
    def get_market_data(self, symbol: str) -> MarketData

# Concrete Implementations
class ZerodhaBroker(BrokerInterface): ...
class AngelBroker(BrokerInterface): ...
class FinvasiaBroker(BrokerInterface): ...
```

### Event-Driven Data Flow

#### CQRS (Command Query Responsibility Segregation)
```
Commands (Write Side):        Queries (Read Side):
┌─────────────────────┐      ┌─────────────────────┐
│   Order Placement   │      │   Portfolio View    │
│   Position Updates  │      │   Performance       │
│   Strategy Config   │      │   Market Data       │
└─────────────────────┘      └─────────────────────┘
         │                            │
         ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Command Store     │      │   Read Projections  │
│   (DynamoDB)        │      │   (Optimized Views) │
└─────────────────────┘      └─────────────────────┘
```

#### Event Sourcing for Audit Trail
- **Event Store:** All trading actions stored as immutable events
- **Event Replay:** Ability to reconstruct state from event history
- **Compliance:** Full audit trail for regulatory requirements
- **Debugging:** Complete visibility into system behavior

### Serverless Architecture Patterns

#### Lambda Function Organization
```
src/api/
├── orders/           # Order management functions
├── strategies/       # Strategy CRUD operations
├── portfolios/       # Portfolio tracking functions
├── webhooks/         # Broker webhook handlers
└── scheduled/        # EventBridge triggered functions
```

#### Cold Start Mitigation
- **Provisioned Concurrency:** For latency-critical functions
- **Connection Pooling:** Database connection reuse
- **Warm-up Patterns:** Keep critical functions warm
- **Lightweight Dependencies:** Minimize function package size

## Data Management Patterns

### Single Table Design (DynamoDB)
```
PK                   SK                    Attributes
USER#123            PROFILE               {name, email, settings}
USER#123            BASKET#456            {basket_config}
USER#123            STRATEGY#789          {strategy_params}
BASKET#456          STRATEGY#789          {strategy_in_basket}
ORDER#999           EXECUTION#001         {execution_details}
```

### Time-Series Data Pattern
- **Hot Data:** Recent data in DynamoDB for fast access
- **Warm Data:** Older data in S3 Parquet for analysis
- **Cold Data:** Archived data with lifecycle policies
- **Query Optimization:** Partitioning by date and user

### Cache-Aside Pattern
```
Application → Cache (ElastiCache) → Database (DynamoDB)
     ↓             ↑                      ↑
   Cache Miss    Cache Hit              Primary Data
```

## Integration Patterns

### API Gateway Pattern
```
Client → API Gateway → Lambda Authorizer → Lambda Function → DynamoDB
   ↓                      ↓                     ↓              ↓
Request              JWT Validation       Business Logic   Data Storage
```

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
```

### Retry with Exponential Backoff
- **Implementation:** Automatic retry for transient failures
- **Broker APIs:** Retry failed API calls to brokers
- **Dead Letter Queues:** Handle permanently failed messages
- **Jitter:** Random delays to prevent thundering herd

## Error Handling Patterns

### Defensive Programming
```python
class OrderService:
    def place_order(self, order: Order) -> Result[OrderConfirmation, OrderError]:
        # Validation
        if not self._validate_order(order):
            return Err(OrderError.INVALID_ORDER)
        
        # Risk Checks
        if not self._check_risk_limits(order):
            return Err(OrderError.RISK_LIMIT_EXCEEDED)
        
        # Broker Integration
        try:
            result = self.broker.place_order(order)
            return Ok(result)
        except BrokerError as e:
            return Err(OrderError.BROKER_FAILURE)
```

### Graceful Degradation
- **Market Data Failures:** Use cached data with staleness indicators
- **Broker API Failures:** Queue orders for retry or manual processing
- **Database Issues:** Fallback to read replicas or cached responses
- **Service Degradation:** Disable non-critical features during issues

## Security Patterns

### Zero Trust Architecture
```
Every Request → Authentication → Authorization → Business Logic → Audit Log
     ↓              ↓              ↓               ↓              ↓
   API Key      JWT Validation   Role Check    Execute Action  Log Event
```

### Secrets Management Pattern
- **Parameter Store:** API keys and configuration
- **Key Rotation:** Automatic credential rotation
- **Encryption:** All secrets encrypted at rest
- **Access Control:** Principle of least privilege

## Monitoring & Observability Patterns

### Three Pillars of Observability
1. **Metrics:** Quantitative measurements (latency, throughput, errors)
2. **Logs:** Discrete event records with context
3. **Traces:** Request flow through distributed system

### Structured Logging Pattern
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "order_placed",
    user_id=user_id,
    order_id=order.id,
    symbol=order.symbol,
    quantity=order.quantity,
    broker="zerodha",
    latency_ms=response_time
)
```

### Health Check Pattern
```
/health/ready    → Service can accept requests
/health/live     → Service is running (for restart decisions)
/health/deep     → Full dependency check (external APIs, database)
```

## Testing Patterns

### Test Pyramid Implementation
```
E2E Tests (Few):
├── Full user journey tests
├── Critical path validation
└── Cross-service integration

Integration Tests (Some):
├── API contract testing
├── Database integration
├── Broker API integration
└── Event flow validation

Unit Tests (Many):
├── Business logic validation
├── Data transformation
├── Edge case handling
└── Error scenarios
```

### Test Doubles Strategy
- **Mocks:** External service responses (broker APIs)
- **Stubs:** Predictable data sources (market data)
- **Fakes:** In-memory implementations (database)
- **Spies:** Behavior verification (event publishing)

## Development Workflow Patterns

### GitFlow with Epic Branches
```
main ← epic/options-strategy-lifecycle ← task/github-issue-2
 ↑              ↑                              ↑
Prod        Feature Branch                Task Branch
```

### Continuous Integration Pattern
1. **Code Push:** Developer pushes to task branch
2. **Automated Tests:** Unit and integration tests run
3. **Code Quality:** Linting, type checking, security scans
4. **Preview Deploy:** Temporary environment for testing
5. **Review:** Code review and approval process
6. **Merge:** Integrate into epic branch

### Infrastructure as Code Pattern
- **CDK Stacks:** Environment-specific stack definitions
- **Drift Detection:** Regular infrastructure drift checks
- **Rollback Strategy:** Blue/green deployments for safety
- **Configuration Management:** Environment variables through Parameter Store