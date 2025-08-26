---
created: 2025-08-26T11:04:13Z
last_updated: 2025-08-26T11:04:13Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Coding Standards & Conventions

### General Principles

#### Code Quality Standards
- **Readability First:** Code should be self-documenting and clear
- **Consistency:** Follow established patterns throughout the codebase  
- **Simplicity:** Favor simple, straightforward solutions
- **Performance:** Optimize for performance where it matters
- **Security:** Security considerations in every design decision

#### Documentation Requirements
- **Function Documentation:** Every public function must have documentation
- **API Documentation:** All APIs must have complete documentation
- **Architecture Docs:** Major design decisions must be documented
- **README Files:** Every module needs a comprehensive README

### Language-Specific Guidelines

#### Python Style (If Selected)
```python
# Function naming: snake_case
def calculate_moving_average(prices: List[float], window: int) -> List[float]:
    """Calculate simple moving average.
    
    Args:
        prices: List of price values
        window: Rolling window size
        
    Returns:
        List of moving average values
    """
    pass

# Class naming: PascalCase  
class TradingStrategy:
    """Base class for all trading strategies."""
    pass

# Constants: UPPER_SNAKE_CASE
MAX_POSITION_SIZE = 1000000
DEFAULT_TIMEFRAME = "1h"
```

#### TypeScript Style (If Selected)
```typescript
// Interface naming: PascalCase with 'I' prefix
interface ITradingStrategy {
    name: string;
    execute(market: IMarketData): ISignal;
}

// Function naming: camelCase
const calculateSharpeRatio = (returns: number[], riskFreeRate: number): number => {
    // Implementation
    return 0;
};

// Enum naming: PascalCase
enum OrderType {
    MARKET = 'market',
    LIMIT = 'limit',
    STOP = 'stop'
}
```

#### Rust Style (If Selected)
```rust
// Function naming: snake_case
pub fn calculate_volatility(returns: &[f64]) -> f64 {
    // Implementation
    0.0
}

// Struct naming: PascalCase
pub struct TradingStrategy {
    pub name: String,
    pub parameters: HashMap<String, f64>,
}

// Constants: UPPER_SNAKE_CASE
const MAX_DRAWDOWN_THRESHOLD: f64 = 0.20;
```

## File Organization & Naming

### Current Patterns (PM System)

#### Directory Structure
- **Commands:** `kebab-case.md` (e.g., `epic-start.md`)
- **Scripts:** `kebab-case.sh` (e.g., `epic-status.sh`) 
- **Documentation:** `kebab-case.md` for multi-word files
- **Configuration:** `UPPERCASE.md` for root-level configs (e.g., `CLAUDE.md`)

### Planned Patterns (Application Code)

#### Source Code Structure
```
src/
├── core/              # Core trading engine
│   ├── engine.py      # Main trading engine
│   ├── portfolio.py   # Portfolio management
│   └── orders.py      # Order management
├── strategies/        # Trading strategies
│   ├── base.py        # Base strategy class
│   ├── momentum.py    # Momentum strategies
│   └── mean_revert.py # Mean reversion strategies
├── data/             # Data management
│   ├── providers.py   # Data provider interfaces
│   ├── storage.py     # Data storage layer
│   └── validators.py  # Data validation
└── utils/            # Utility functions
    ├── math.py        # Mathematical utilities
    ├── indicators.py  # Technical indicators
    └── helpers.py     # General helpers
```

#### Test Structure (Mirrors Source)
```
tests/
├── unit/             # Unit tests
│   ├── core/         # Core module tests
│   ├── strategies/   # Strategy tests  
│   └── data/         # Data module tests
├── integration/      # Integration tests
│   ├── api/          # API integration tests
│   └── database/     # Database tests
└── e2e/             # End-to-end tests
    ├── backtest/     # Backtesting E2E
    └── live/         # Live trading E2E
```

### File Naming Conventions

#### Source Files
- **Python:** `snake_case.py` (e.g., `moving_average.py`)
- **TypeScript:** `camelCase.ts` or `kebab-case.ts` (e.g., `tradingStrategy.ts`)
- **Rust:** `snake_case.rs` (e.g., `order_manager.rs`)

#### Test Files
- **Pattern:** `test_<module_name>` or `<module_name>.test`
- **Examples:** `test_portfolio.py`, `tradingStrategy.test.ts`

#### Configuration Files
- **Environment:** `.env`, `.env.local`, `.env.production`
- **Configuration:** `config.json`, `settings.yaml`
- **Docker:** `Dockerfile`, `docker-compose.yml`

## Comment Style & Documentation

### Code Comments

#### Comment Philosophy
- **Why Over What:** Explain reasoning, not obvious implementation
- **Business Logic:** Document trading logic and business rules
- **Complex Algorithms:** Detailed explanation of mathematical concepts
- **Performance Notes:** Document optimization decisions

#### Comment Examples
```python
# Good: Explains why
# Use exponential decay to give more weight to recent price movements
# as markets tend to have momentum in the short term
weight = np.exp(-decay_factor * age)

# Bad: States the obvious  
# Multiply weight by decay factor
weight = weight * decay_factor
```

### Function Documentation

#### Python Docstring Style (Google/Numpy)
```python
def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate the Sharpe ratio for a series of returns.
    
    The Sharpe ratio measures risk-adjusted performance by dividing excess returns
    by the standard deviation of returns. Higher values indicate better
    risk-adjusted performance.
    
    Args:
        returns: Array of periodic returns (e.g., daily, monthly)
        risk_free_rate: Annual risk-free rate (default: 0.02 = 2%)
        
    Returns:
        The Sharpe ratio as a float. Values > 1.0 are generally considered good.
        
    Raises:
        ValueError: If returns array is empty or contains invalid values
        
    Example:
        >>> returns = np.array([0.01, -0.02, 0.03, 0.005])
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe ratio: {sharpe:.2f}")
    """
    pass
```

#### TypeScript JSDoc Style
```typescript
/**
 * Calculate the maximum drawdown for a series of portfolio values.
 * 
 * Maximum drawdown represents the largest peak-to-trough decline
 * and is a key risk metric for trading strategies.
 * 
 * @param portfolioValues - Array of portfolio values over time
 * @returns The maximum drawdown as a decimal (e.g., 0.15 = 15% drawdown)
 * @throws {Error} When portfolio values array is empty or invalid
 * 
 * @example
 * ```typescript
 * const values = [100, 110, 105, 95, 120];
 * const maxDD = calculateMaxDrawdown(values);
 * console.log(`Max drawdown: ${(maxDD * 100).toFixed(2)}%`);
 * ```
 */
const calculateMaxDrawdown = (portfolioValues: number[]): number => {
    // Implementation
    return 0;
};
```

### Architecture Documentation

#### Design Decision Documents
```markdown
# ADR-001: Programming Language Selection

## Status
Proposed

## Context  
Need to select primary programming language for the trading platform.

## Decision
Python for initial implementation due to:
- Rich ecosystem of trading/math libraries
- Rapid development and prototyping
- Strong data science community
- Extensive documentation and examples

## Consequences
Positive:
- Faster development cycle
- Large talent pool
- Excellent libraries (pandas, numpy, etc.)

Negative:  
- Performance limitations for high-frequency trading
- GIL limitations for CPU-intensive tasks
- May need Rust/C++ for latency-critical components
```

## Version Control & Git Practices

### Branch Naming
- **Feature branches:** `feature/strategy-optimization`
- **Bug fixes:** `fix/portfolio-calculation-error`
- **Releases:** `release/v1.2.0`
- **Hotfixes:** `hotfix/critical-execution-bug`

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Examples
```bash
feat(portfolio): add real-time P&L calculation

Implement live portfolio value tracking with support for:
- Multi-asset position valuation
- Currency conversion for international assets  
- Real-time mark-to-market updates

Closes #123

fix(execution): resolve order timeout handling

Orders were not properly timing out due to async callback issues.
Added proper timeout handling and error recovery.

Fixes #456
```

### Code Review Guidelines

#### Review Checklist
- [ ] **Functionality:** Code works as intended
- [ ] **Performance:** No obvious performance issues
- [ ] **Security:** No security vulnerabilities
- [ ] **Style:** Follows project style guide
- [ ] **Tests:** Adequate test coverage
- [ ] **Documentation:** Proper documentation included

#### Review Size
- **Maximum:** 400 lines changed per PR
- **Preferred:** 200 lines or less per PR
- **Complex Changes:** Split into multiple smaller PRs

## Testing Standards

### Test Categories

#### Unit Tests
- **Coverage Target:** 90%+ for core business logic
- **Naming:** `test_<function_name>`
- **Structure:** Arrange, Act, Assert pattern
- **Mocking:** Mock external dependencies

#### Integration Tests  
- **Coverage:** All API endpoints and database operations
- **Environment:** Separate test environment
- **Data:** Use test fixtures and factories
- **Cleanup:** Proper test data cleanup

#### End-to-End Tests
- **Coverage:** Critical user journeys
- **Environment:** Staging environment
- **Frequency:** Run before releases
- **Documentation:** Clear test scenarios

### Test Examples

#### Python Unit Test
```python
def test_sharpe_ratio_calculation():
    """Test Sharpe ratio calculation with known values."""
    # Arrange
    returns = np.array([0.01, -0.02, 0.03, 0.005, -0.01])
    risk_free_rate = 0.02
    expected_sharpe = 0.447  # Pre-calculated expected value
    
    # Act
    result = calculate_sharpe_ratio(returns, risk_free_rate)
    
    # Assert
    assert abs(result - expected_sharpe) < 0.001
    assert isinstance(result, float)
```

## Performance & Optimization

### Performance Guidelines

#### General Rules
- **Measure First:** Profile before optimizing
- **Bottlenecks:** Focus on actual bottlenecks, not perceived ones
- **Readability:** Don't sacrifice readability for micro-optimizations
- **Caching:** Use caching for expensive computations

#### Specific Optimizations
- **Database:** Use connection pooling and prepared statements  
- **Memory:** Avoid unnecessary data copying
- **Algorithms:** Choose appropriate data structures and algorithms
- **Concurrency:** Use async/await for I/O operations

### Code Examples

#### Efficient Data Processing
```python
# Good: Vectorized operations
def calculate_returns_vectorized(prices: np.ndarray) -> np.ndarray:
    return np.diff(prices) / prices[:-1]

# Avoid: Loop-based operations for large datasets
def calculate_returns_loop(prices: List[float]) -> List[float]:
    returns = []
    for i in range(1, len(prices)):
        returns.append((prices[i] - prices[i-1]) / prices[i-1])
    return returns
```

This style guide ensures consistency, maintainability, and quality across the entire QL Algorithmic Trading Platform codebase.