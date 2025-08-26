#!/usr/bin/env python3
"""
AWS CDK App Entry Point for Options Strategy Lifecycle Platform

This is the main entry point for the CDK application that defines the
Options Strategy Lifecycle Platform infrastructure. It creates and
configures the CDK app with proper environment settings for deployment
to ap-south-1 (Asia Pacific - Mumbai) region.

The app supports multiple environments (dev, staging, prod) using the
centralized configuration system from config/environments.py with:
- Environment-specific resource configurations
- Comprehensive validation and error handling
- Structured parameter management
- Compliance and security settings
- Cost optimization configurations

Usage:
    python app.py                    # Deploy to dev environment
    CDK_ENVIRONMENT=staging cdk deploy  # Deploy to staging
    CDK_ENVIRONMENT=prod cdk deploy --profile production  # Deploy to production
    cdk synth                        # Generate CloudFormation templates
    cdk diff                         # Show changes between deployed and local
"""

import os
import sys
from aws_cdk import App, Environment
from infrastructure import OptionsStrategyPlatformStack
from config.environments import get_environment_config, validate_environment_config


def validate_and_get_config():
    """
    Get and validate environment configuration
    
    Returns:
        tuple: (env_config, aws_env)
        
    Raises:
        ValueError: If configuration validation fails
        SystemExit: If environment is invalid or configuration has errors
    """
    # Get environment name
    env_name = os.environ.get("CDK_ENVIRONMENT", "dev")
    
    try:
        # Get environment configuration
        env_config = get_environment_config(env_name)
    except ValueError as e:
        print(f"❌ Invalid environment configuration: {e}")
        sys.exit(1)
    
    # Validate configuration
    validation_errors = validate_environment_config(env_config)
    if validation_errors:
        print("❌ Environment configuration validation failed:")
        for error in validation_errors:
            print(f"   - {error}")
        print(f"\nPlease fix the configuration issues in config/environments.py")
        sys.exit(1)
    
    # Create AWS environment
    aws_env = Environment(
        account=env_config.aws_account,
        region=env_config.aws_region
    )
    
    return env_config, aws_env


def print_deployment_info(env_config):
    """
    Print comprehensive deployment information
    
    Args:
        env_config: Environment configuration object
    """
    print("🚀 Options Strategy Platform CDK App")
    print(f"   Environment: {env_config.env_name}")
    print(f"   Region: {env_config.aws_region}")
    print(f"   Stack: {env_config.stack_name}")
    print(f"   Account: {env_config.aws_account or 'Not specified (will use default)'}")
    print()
    
    # Network configuration
    print("🌐 Network Configuration:")
    print(f"   VPC CIDR: {env_config.networking.vpc_cidr}")
    print(f"   Max AZs: {env_config.networking.max_azs}")
    print(f"   NAT Gateway: {'Enabled' if env_config.networking.enable_nat_gateway else 'Disabled'}")
    print()
    
    # Security configuration
    print("🔒 Security Configuration:")
    print(f"   WAF: {'Enabled' if env_config.security.enable_waf else 'Disabled'}")
    print(f"   Shield: {'Enabled' if env_config.security.enable_shield else 'Disabled'}")
    print(f"   VPC Endpoints: {'Enabled' if env_config.security.enable_vpc_endpoints else 'Disabled'}")
    print(f"   Encryption at Rest: {'Enabled' if env_config.security.enable_encryption_at_rest else 'Disabled'}")
    print()
    
    # Compliance and monitoring
    print("📊 Monitoring & Compliance:")
    print(f"   Log Retention: {env_config.monitoring.log_retention_days} days")
    print(f"   X-Ray Tracing: {'Enabled' if env_config.monitoring.enable_xray_tracing else 'Disabled'}")
    print(f"   Data Residency: {env_config.compliance.data_residency_region}")
    print(f"   Backup Retention: {env_config.compliance.backup_retention_days} days")
    print()
    
    # Feature flags
    enabled_features = [k for k, v in env_config.feature_flags.items() if v]
    if enabled_features:
        print("🎯 Enabled Features:")
        for feature in enabled_features:
            print(f"   - {feature}")
        print()
    
    # Resource sizing
    print("💻 Resource Configuration:")
    print(f"   Lambda Memory: {env_config.resources.lambda_memory_size}MB")
    print(f"   ECS CPU/Memory: {env_config.resources.ecs_cpu}/{env_config.resources.ecs_memory}")
    print(f"   RDS Instance: {env_config.resources.rds_instance_class}")
    print()
    
    # Cost optimization
    cost_features = []
    if env_config.cost_optimization.enable_spot_instances:
        cost_features.append("Spot Instances")
    if env_config.cost_optimization.enable_scheduled_scaling:
        cost_features.append("Scheduled Scaling")
    if env_config.cost_optimization.enable_lifecycle_policies:
        cost_features.append("Lifecycle Policies")
    
    if cost_features:
        print("💰 Cost Optimization:")
        for feature in cost_features:
            print(f"   - {feature}")
        print()


def main():
    """Main function to create and configure the CDK app"""
    
    try:
        print("🔍 Initializing Options Strategy Platform...")
        print()
        
        # Get and validate environment configuration
        env_config, aws_env = validate_and_get_config()
        
        # Print deployment information
        print_deployment_info(env_config)
        
        # Create CDK app
        print("🏗️  Creating CDK application...")
        app = App()
        
        # Create the main infrastructure stack
        stack_name = env_config.stack_name
        
        print(f"📦 Creating infrastructure stack: {stack_name}")
        OptionsStrategyPlatformStack(
            app,
            stack_name,
            env_config=env_config,
            env=aws_env,
            description=f"Options Strategy Lifecycle Platform - {env_config.env_name.title()} Environment",
            stack_name=stack_name,
        )
        
        # Add app-level tags
        app.node.set_context("@aws-cdk/core:enableStackNameDuplicates", True)
        
        # Set context for better error messages
        app.node.set_context("@aws-cdk/core:stackRelativeExports", True)
        
        print("✅ CDK application initialized successfully")
        print()
        print("🚀 Ready to deploy!")
        print("   Run: cdk deploy")
        print("   Or:  cdk synth (to generate CloudFormation)")
        print("   Or:  cdk diff (to see changes)")
        print()
        
        # Synthesize the app
        app.synth()
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to create CDK app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()