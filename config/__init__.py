"""
Configuration package for Options Strategy Lifecycle Platform

This package provides environment-specific configuration management
and settings for the Options Strategy Lifecycle Platform.
"""

from .environments import EnvironmentConfig, get_environment_config

__version__ = "1.0.0"
__all__ = ["EnvironmentConfig", "get_environment_config"]