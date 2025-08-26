"""
Infrastructure Stacks for Options Strategy Lifecycle Platform

This package contains modular CDK stacks for the Options Strategy Lifecycle Platform.
Each stack is responsible for a specific aspect of the infrastructure:

- NetworkingStack: VPC, subnets, routing, and network-related resources
- SecurityStack: Security groups, NACLs, and security configurations
- More stacks can be added as the platform grows

The modular approach allows for:
- Better separation of concerns
- Independent deployment of different infrastructure components
- Easier maintenance and updates
- Reusability across environments
"""

from .networking_stack import NetworkingStack
from .security_stack import SecurityStack

__all__ = [
    "NetworkingStack",
    "SecurityStack",
]

# Version information
__version__ = "1.0.0"
__author__ = "Options Strategy Platform Team"
__email__ = "platform-team@company.com"