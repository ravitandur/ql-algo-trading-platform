---
created: 2025-08-26T12:32:21Z
last_updated: 2025-08-26T12:32:21Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Current Directory Layout

```
ql-algo-trading-platform/
├── .claude/                     # Claude Code PM System
│   ├── agents/                  # Specialized AI agents (4 agents)
│   ├── commands/                # PM commands and workflows (47 commands)
│   ├── context/                 # Project context documentation (10 files)
│   ├── epics/                   # Epic management directory
│   │   └── options-strategy-lifecycle/  # Active epic with 34 tasks + epic.md
│   ├── prds/                    # Product requirement documents
│   │   └── options-strategy-lifecycle.md
│   ├── rules/                   # Development patterns and guidelines (10 rules)
│   └── scripts/                 # Automation and utility scripts (14 scripts)
├── .git/                        # Git repository data
├── .gitignore                   # Comprehensive multi-language gitignore
├── .idea/                       # IntelliJ IDEA configuration (ignored)
└── CLAUDE.md                    # Project-specific rules and guidelines
```

## Epic Directory Structure

### Options Strategy Lifecycle Epic
```
.claude/epics/options-strategy-lifecycle/
├── epic.md                      # Main epic definition and overview
├── github-mapping.md            # GitHub issue mapping documentation
├── 2.md                         # Task: Set up AWS CDK infrastructure stack
├── 3.md                         # Task: Design and implement DynamoDB schema
├── 5.md                         # Task: Implement basic user authentication
├── 6.md                         # Task: Create Zerodha API integration service
├── 7.md                         # Task: Set up EventBridge scheduling
...
├── 34.md                        # Task: Build system metrics and KPI tracking
└── 35.md                        # Task: Design broker abstraction layer
```

**Task Naming:** Files named with GitHub issue numbers (2-35) for direct correlation

## Planned Application Structure

### AWS-Native Python Application
```
ql-algo-trading-platform/
├── infrastructure/              # AWS CDK (Python) infrastructure code
│   ├── stacks/                 # CDK stack definitions
│   ├── constructs/             # Reusable CDK constructs
│   └── app.py                  # CDK application entry point
├── src/                        # Application source code
│   ├── api/                    # API Gateway Lambda functions
│   ├── core/                   # Core business logic
│   ├── data/                   # Data models and schemas
│   ├── integrations/           # External service integrations
│   │   ├── zerodha/            # Zerodha broker integration
│   │   ├── angel/              # Angel One integration
│   │   └── finvasia/           # Finvasia integration
│   ├── services/               # Business service layer
│   └── utils/                  # Utility functions
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── docs/                       # Project documentation
├── scripts/                    # Build and deployment scripts
└── requirements.txt            # Python dependencies
```

## File Naming Patterns

### Current Patterns (PM System)
- **Commands:** `kebab-case.md` (e.g., `epic-start.md`)
- **Scripts:** `kebab-case.sh` (e.g., `epic-status.sh`)
- **Tasks:** `{github-issue-number}.md` (e.g., `2.md`, `35.md`)
- **Configuration:** `UPPERCASE.md` for project-level configs

### Planned Patterns (Application Code)
- **Python Files:** `snake_case.py` (e.g., `basket_service.py`)
- **CDK Stacks:** `PascalCase` classes (e.g., `OptionsStrategyStack`)
- **Lambda Functions:** `kebab-case` directory structure
- **Tests:** `test_*.py` or `*_test.py` patterns

## Module Organization

### Current Modules (PM System)
1. **Agents** (`agents/`): Task-specific AI automation
2. **Commands** (`commands/`): Interactive PM operations
3. **Context** (`context/`): Project documentation and context
4. **Epics** (`epics/`): Feature development management  
5. **Rules** (`rules/`): Development patterns and guidelines
6. **Scripts** (`scripts/`): Automation and utility scripts

### Planned Modules (Application)
1. **Infrastructure** (`infrastructure/`): AWS CDK deployment code
2. **API Layer** (`src/api/`): HTTP endpoints and GraphQL resolvers
3. **Business Logic** (`src/core/`): Core trading algorithms and logic
4. **Data Layer** (`src/data/`): Models, schemas, and persistence
5. **Integrations** (`src/integrations/`): External service connectors
6. **Services** (`src/services/`): Business service implementations

## Directory Responsibilities

### `.claude/` - Project Management Infrastructure
- **Purpose:** Comprehensive project management and automation
- **Contains:** Commands, agents, rules, documentation, epic management
- **Ownership:** PM system maintenance and development workflow
- **Size:** ~100 files across multiple subdirectories

### `infrastructure/` - AWS CDK Infrastructure (Planned)
- **Purpose:** Infrastructure as Code using AWS CDK (Python)
- **Contains:** Stack definitions, constructs, deployment configuration
- **Ownership:** DevOps and infrastructure management
- **Region:** ap-south-1 (Asia Pacific - Mumbai)

### `src/` - Application Source Code (Planned)
- **Purpose:** Core application implementation
- **Contains:** Business logic, APIs, services, integrations
- **Ownership:** Development team
- **Language:** Python 3.9+ with modern frameworks

### `tests/` - Quality Assurance (Planned)
- **Purpose:** Comprehensive test coverage
- **Contains:** Unit tests, integration tests, end-to-end tests
- **Ownership:** Development team with QA collaboration
- **Framework:** pytest with async support

## Key Organizational Principles

### Current Implementation
- **PM System Isolation:** All PM functionality contained in `.claude/`
- **Epic-Driven Development:** Features organized as epics with sequential tasks
- **GitHub Integration:** Direct correlation between tasks and GitHub issues
- **Documentation-First:** Comprehensive documentation before implementation

### Planned Implementation
- **Microservices Architecture:** Event-driven AWS services
- **Domain-Driven Design:** Clear boundaries between business domains
- **Infrastructure as Code:** Everything deployed through CDK
- **API-First:** All functionality exposed through well-defined APIs

## Development Workflow Structure

### Current Workflow
1. **Epic Creation:** Define comprehensive feature requirements
2. **Task Decomposition:** Break down into sequential implementation tasks
3. **GitHub Sync:** Create linked issues for project management
4. **Worktree Development:** Isolated branch development for each epic

### Development Environment
- **Main Branch:** Production-ready code only
- **Epic Branches:** Feature development in dedicated worktrees
- **Task Correlation:** Each GitHub issue corresponds to specific implementation
- **Sequential Execution:** Tasks must be completed in dependency order

### File Lifecycle
1. **PRD Creation:** `prd-new` command creates requirements document
2. **Epic Generation:** `prd-parse` converts PRD to actionable epic
3. **Task Decomposition:** `epic-decompose` creates individual task files
4. **GitHub Sync:** `epic-sync` creates corresponding GitHub issues
5. **Development:** Tasks completed in sequential order with commits