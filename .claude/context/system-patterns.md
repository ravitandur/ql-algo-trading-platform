---
created: 2025-08-26T11:04:13Z
last_updated: 2025-08-26T11:04:13Z
version: 1.0
author: Claude Code PM System
---

# System Patterns & Architecture

## Observed Architectural Patterns

### Project Management Layer
The Claude PM system demonstrates several key patterns:

#### Command Pattern
- **Implementation:** Each PM command is encapsulated as a separate module
- **Location:** `.claude/commands/pm/`
- **Examples:** `epic-start.md`, `issue-analyze.md`
- **Benefits:** Modular, extensible, easy to maintain

#### Agent-Based Architecture
- **Implementation:** Specialized agents for different tasks
- **Location:** `.claude/agents/`
- **Examples:** `code-analyzer.md`, `test-runner.md`
- **Benefits:** Separation of concerns, focused expertise

#### Script-Based Automation
- **Implementation:** Shell scripts for common operations
- **Location:** `.claude/scripts/pm/`
- **Examples:** `epic-status.sh`, `validate.sh`
- **Benefits:** Automation, consistency, repeatability

## Recommended Application Patterns

### Core Architecture: Event-Driven Microservices

#### Trading Engine Pattern
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Ingestion │───▶│  Strategy Engine │───▶│  Order Manager  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Market Data    │    │   Signals DB    │    │   Positions DB  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Strategy Pattern Implementation
- **Base Strategy Interface:** Abstract strategy class/trait
- **Concrete Strategies:** Individual trading algorithms
- **Strategy Registry:** Dynamic strategy loading
- **Benefits:** Pluggable algorithms, easy testing, modularity

#### Observer Pattern for Events
- **Market Data Events:** Price updates, volume changes
- **Trading Events:** Order fills, position changes
- **System Events:** Errors, health checks
- **Benefits:** Loose coupling, real-time responsiveness

### Data Flow Architecture

#### Pipeline Pattern
```
Raw Data → Validation → Normalization → Feature Engineering → Storage
    ↓           ↓            ↓                ↓              ↓
 Logging    Error        Format         Calculate       Database
           Handling     Conversion      Indicators        Cache
```

#### Repository Pattern
- **Data Access Layer:** Abstract database operations
- **Multiple Implementations:** SQL, NoSQL, Cache
- **Interface Consistency:** Uniform data access
- **Benefits:** Testability, flexibility, maintainability

### Risk Management Patterns

#### Circuit Breaker Pattern
- **Implementation:** Prevent cascade failures
- **Triggers:** High loss rates, API failures
- **Recovery:** Automatic/manual reset mechanisms
- **Benefits:** System stability, controlled degradation

#### Bulkhead Pattern
- **Implementation:** Resource isolation
- **Segregation:** By exchange, strategy, or asset class
- **Benefits:** Failure isolation, resource management

## Design Principles

### Established Principles (PM System)
1. **Modularity:** Each component has a single responsibility
2. **Configurability:** Behavior controlled through configuration
3. **Automation:** Manual tasks automated through scripts
4. **Documentation:** Self-documenting through markdown files

### Recommended Principles (Application)

#### SOLID Principles
- **Single Responsibility:** Each class/module has one job
- **Open/Closed:** Open for extension, closed for modification
- **Liskov Substitution:** Derived classes must be substitutable
- **Interface Segregation:** Many specific interfaces over one general
- **Dependency Inversion:** Depend on abstractions, not concretions

#### Trading-Specific Principles
- **Fail-Safe Defaults:** Conservative behavior when uncertain
- **Immutable Data:** Market data should not be modified
- **Audit Trail:** All decisions must be traceable
- **Real-Time First:** Low-latency requirements drive design

## Error Handling Patterns

### Current Pattern (PM System)
- **Graceful Degradation:** Continue with reduced functionality
- **User-Friendly Messages:** Clear error communication
- **Logging:** Detailed logs for debugging

### Recommended Patterns (Application)

#### Result/Option Pattern
- **Implementation:** Explicit error handling without exceptions
- **Benefits:** Forced error consideration, clearer code flow
- **Examples:** `Result<T, Error>` in Rust, `Optional<T>` patterns

#### Retry with Backoff
- **Use Cases:** Network failures, temporary API issues
- **Implementation:** Exponential backoff, jitter, circuit breaking
- **Benefits:** Resilience to temporary failures

## Testing Patterns

### Current Approach (PM System)
- **Validation Scripts:** Automated checking of system state
- **Integration Focus:** End-to-end workflow testing

### Recommended Patterns (Application)

#### Test Pyramid
```
    ┌─────────────┐
    │    E2E      │  ← Few, high-value integration tests
    ├─────────────┤
    │ Integration │  ← Moderate number of service tests  
    ├─────────────┤
    │    Unit     │  ← Many fast, focused unit tests
    └─────────────┘
```

#### Test Doubles Pattern
- **Mocks:** For external API interactions
- **Stubs:** For predictable data sources  
- **Fakes:** For simplified implementations
- **Benefits:** Fast tests, controlled conditions

## Configuration Patterns

### Current Pattern (PM System)
- **File-Based:** Markdown files for configuration
- **Hierarchical:** Organized by domain (commands, rules, etc.)

### Recommended Patterns (Application)
- **Environment-Based:** Different configs per environment
- **Layered Configuration:** Defaults < Environment < Runtime
- **Validation:** Schema validation for all configuration
- **Hot Reloading:** Runtime configuration updates where safe