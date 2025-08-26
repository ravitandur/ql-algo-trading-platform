---
created: 2025-08-26T11:04:13Z
last_updated: 2025-08-26T11:04:13Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Current Directory Layout

```
ql-algo-trading-platform/
├── .claude/                     # Claude Code PM System
│   ├── agents/                  # Sub-agent configurations
│   ├── commands/               # PM command definitions
│   ├── context/               # Project context documentation
│   ├── epics/                 # Epic management
│   ├── prds/                  # Product requirement documents
│   ├── rules/                 # Project rules and patterns
│   └── scripts/               # Automation scripts
├── .git/                       # Git repository data
├── .idea/                      # IDE configuration (untracked)
└── CLAUDE.md                   # Project rules and guidelines
```

## Planned Architecture (To Be Implemented)

### Core Platform Structure
```
ql-algo-trading-platform/
├── src/                        # Source code
│   ├── core/                   # Core trading engine
│   ├── strategies/             # Trading strategies
│   ├── data/                   # Data management
│   ├── api/                    # API layer
│   └── utils/                  # Utility functions
├── tests/                      # Test suites
├── docs/                       # Documentation
├── config/                     # Configuration files
└── scripts/                    # Build and deployment scripts
```

## File Naming Patterns

### Current Patterns (PM System)
- **Commands:** `kebab-case.md` (e.g., `epic-start.md`)
- **Scripts:** `kebab-case.sh` (e.g., `epic-status.sh`)
- **Configuration:** `UPPERCASE.md` for root-level configs

### Planned Patterns (Application Code)
- **Source Files:** To be determined based on chosen language
- **Tests:** Mirror source structure with test suffix
- **Documentation:** `kebab-case.md` for consistency

## Module Organization

### Current Modules (PM System)
1. **Agents:** Specialized AI agents for different tasks
2. **Commands:** Interactive PM commands
3. **Scripts:** Automation and utility scripts
4. **Rules:** Development patterns and guidelines

### Planned Modules (Application)
1. **Core Engine:** Central trading logic
2. **Strategy Framework:** Pluggable trading strategies
3. **Data Pipeline:** Market data ingestion and processing
4. **Risk Management:** Position sizing and risk controls
5. **API Layer:** External integrations and endpoints

## Directory Responsibilities

### `.claude/` - Project Management
- **Purpose:** Claude Code PM system configuration
- **Contains:** Commands, scripts, documentation, rules
- **Ownership:** PM system maintenance

### `src/` - Application Code (Planned)
- **Purpose:** Core application logic
- **Contains:** Business logic, algorithms, APIs
- **Ownership:** Development team

### `tests/` - Quality Assurance (Planned)
- **Purpose:** Test suites and quality gates
- **Contains:** Unit tests, integration tests, benchmarks
- **Ownership:** Development team

### `docs/` - Documentation (Planned)
- **Purpose:** Project documentation
- **Contains:** Architecture docs, API specs, guides
- **Ownership:** Technical writing

## Key Organizational Principles

### Separation of Concerns
- PM system isolated in `.claude/`
- Application code in dedicated directories
- Configuration separate from code

### Scalability Considerations
- Modular structure for easy extension
- Clear boundaries between components
- Plugin architecture for strategies

### Development Workflow
- Source code follows chosen language conventions
- Test structure mirrors source structure
- Documentation co-located with relevant code