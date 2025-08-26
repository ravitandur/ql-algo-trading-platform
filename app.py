#!/usr/bin/env python3
"""
AWS CDK App Entry Point for Options Strategy Lifecycle Platform

This is the main entry point for the CDK application that defines the
Options Strategy Lifecycle Platform infrastructure. It creates and
configures the CDK app with proper environment settings for deployment
to ap-south-1 (Asia Pacific - Mumbai) region.

The app supports multiple environments (dev, staging, prod) and applies
appropriate configuration for each environment including:
- Resource naming conventions
- Tagging strategies
- Security configurations
- Cost optimization settings

Usage:
    python app.py                    # Deploy to dev environment
    cdk deploy --profile production  # Deploy to production
    cdk synth                        # Generate CloudFormation templates
    cdk diff                         # Show changes between deployed and local
"""

import os
from aws_cdk import App, Environment
from infrastructure import OptionsStrategyPlatformStack


def get_environment_config() -> dict:
    """
    Get environment-specific configuration
    
    Returns:
        dict: Environment configuration including AWS account and region
    """
    # Default to dev environment if not specified
    env_name = os.environ.get("CDK_ENVIRONMENT", "dev")
    
    # Environment-specific configurations
    env_configs = {
        "dev": {
            "account": os.environ.get("CDK_DEFAULT_ACCOUNT"),
            "region": "ap-south-1",  # Mumbai region for Indian market compliance
            "vpc_cidr": "10.0.0.0/16",
            "max_azs": 2,  # Cost optimization for dev
        },
        "staging": {
            "account": os.environ.get("CDK_DEFAULT_ACCOUNT"),
            "region": "ap-south-1",
            "vpc_cidr": "10.1.0.0/16", 
            "max_azs": 2,
        },
        "prod": {
            "account": os.environ.get("CDK_DEFAULT_ACCOUNT"), 
            "region": "ap-south-1",
            "vpc_cidr": "10.2.0.0/16",
            "max_azs": 3,  # High availability for production
        }
    }
    
    if env_name not in env_configs:
        raise ValueError(f"Unknown environment: {env_name}. Supported: {list(env_configs.keys())}")
    
    config = env_configs[env_name]
    config["env_name"] = env_name
    
    return config


def create_stack_name(env_name: str) -> str:
    """
    Create standardized stack name
    
    Args:
        env_name: Environment name (dev, staging, prod)
        
    Returns:
        str: Standardized stack name
    """
    return f"OptionsStrategyPlatform-{env_name.title()}"


def main():
    """Main function to create and configure the CDK app"""
    
    # Get environment configuration
    env_config = get_environment_config()
    env_name = env_config["env_name"]
    
    # Create CDK app
    app = App()
    
    # Create AWS environment configuration
    aws_env = Environment(
        account=env_config["account"],
        region=env_config["region"]
    )
    
    # Create the main infrastructure stack
    stack_name = create_stack_name(env_name)
    
    OptionsStrategyPlatformStack(
        app,
        stack_name,
        env_name=env_name,
        vpc_cidr=env_config["vpc_cidr"],
        max_azs=env_config["max_azs"],
        env=aws_env,
        description=f"Options Strategy Lifecycle Platform - {env_name.title()} Environment",
        stack_name=stack_name,
    )
    
    # Add app-level tags
    app.node.set_context("@aws-cdk/core:enableStackNameDuplicates", True)
    
    # Print deployment information
    print(f"🚀 Options Strategy Platform CDK App")
    print(f"   Environment: {env_name}")
    print(f"   Region: {env_config['region']}")
    print(f"   Stack: {stack_name}")
    print(f"   Account: {env_config['account'] or 'Not specified (will use default)'}")
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()