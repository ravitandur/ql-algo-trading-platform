"""
Options Strategy Lifecycle Platform Infrastructure Module

This module contains the AWS CDK infrastructure definitions for the
Options Strategy Lifecycle Platform, including:

- Core networking and security infrastructure
- Data processing and storage services
- API Gateway and Lambda functions
- Monitoring and logging setup
- Multi-environment configuration support

The infrastructure is designed specifically for the Indian market with
ap-south-1 region deployment and data residency compliance.
"""

__version__ = "0.1.0"
__author__ = "Trading Platform Team"

# Import core stack classes for easy access
from .app import OptionsStrategyPlatformStack

__all__ = [
    "OptionsStrategyPlatformStack",
]