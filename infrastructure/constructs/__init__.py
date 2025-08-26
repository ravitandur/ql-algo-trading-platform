"""
Infrastructure Constructs for Options Strategy Lifecycle Platform

This package contains reusable CDK constructs for the Options Strategy Lifecycle Platform.
Constructs are higher-level components that encapsulate AWS resources and best practices:

- OptionsStrategyVPC: Reusable VPC construct with multi-tier architecture
- More constructs can be added for common patterns and components

The construct approach allows for:
- Reusability across different stacks and environments
- Encapsulation of best practices and configurations
- Easier testing and validation
- Consistent resource creation patterns
"""

from .vpc_construct import OptionsStrategyVPC

__all__ = [
    "OptionsStrategyVPC",
]

# Version information
__version__ = "1.0.0"
__author__ = "Options Strategy Platform Team"
__email__ = "platform-team@company.com"