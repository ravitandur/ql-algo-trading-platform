#!/usr/bin/env python3
"""
Simplified AWS CDK App for Options Strategy Lifecycle Platform

This simplified version eliminates circular dependencies and provides
a clean foundation for testing and development.
"""

import os
from aws_cdk import (
    App,
    Environment,
)
from infrastructure.simple_app import SimpleOptionsStrategyStack


def main():
    """Main application entry point"""
    app = App()

    # Get environment configuration
    env_name = app.node.try_get_context("env") or "dev"
    region = app.node.try_get_context("region") or "ap-south-1"
    account = app.node.try_get_context("account") or os.getenv(
        "CDK_DEFAULT_ACCOUNT"
    )

    # Create environment configuration
    env = Environment(account=account, region=region)

    # Create the simplified stack
    stack_name = f"OptionsStrategy-{env_name.title()}"

    SimpleOptionsStrategyStack(
        app,
        stack_name,
        env_name=env_name,
        vpc_cidr="10.0.0.0/16",
        max_azs=2 if env_name == "dev" else 3,
        env=env,
        stack_name=stack_name,
        description=f"Options Strategy Lifecycle Platform - {env_name} environment",
    )

    app.synth()


if __name__ == "__main__":
    main()
