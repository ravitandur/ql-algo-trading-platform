"""
Main CDK Stack for Options Strategy Lifecycle Platform

This module defines the core AWS infrastructure stack for the Options Strategy
Lifecycle Platform, including IAM roles, CloudWatch resources, and foundational
services required for the trading platform.

This stack now uses modular networking and security stacks for better
separation of concerns and maintainability.

The stack is designed for deployment in ap-south-1 (Asia Pacific - Mumbai) region
to comply with Indian market data residency requirements.
"""

import os
from typing import Dict, Any, Optional
from aws_cdk import (
    App,
    Stack,
    StackProps,
    Environment,
    CfnOutput,
    Tags,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_ssm as ssm,
    aws_cloudwatch as cloudwatch,
)
from constructs import Construct
from .stacks.networking_stack import NetworkingStack
from .stacks.security_stack import SecurityStack
from .stacks.iam_stack import IAMStack
from .stacks.config_stack import ConfigurationStack
from .stacks.monitoring_stack import MonitoringStack


class OptionsStrategyPlatformStack(Stack):
    """
    Main CDK Stack for Options Strategy Lifecycle Platform
    
    This stack creates the foundational infrastructure including:
    - Networking infrastructure (delegated to NetworkingStack)
    - Security groups and policies (delegated to SecurityStack)
    - IAM roles and policies following principle of least privilege
    - CloudWatch log groups and basic monitoring
    - Parameter Store entries for configuration management
    - Resource tagging for proper cost allocation and management
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: Any,  # EnvironmentConfig type
        **kwargs
    ) -> None:
        """
        Initialize the Options Strategy Platform Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_config: Environment configuration object
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_config = env_config
        self.env_name = env_config.env_name
        
        # Apply standard tags to all resources in this stack
        self._apply_standard_tags()
        
        # Create networking infrastructure using modular stack
        self.networking_stack = NetworkingStack(
            self,
            "Networking",
            env_name=self.env_name,
            vpc_cidr=env_config.networking.vpc_cidr,
            max_azs=env_config.networking.max_azs,
            **kwargs
        )
        
        # Get VPC reference from networking stack
        self.vpc = self.networking_stack.vpc
        
        # Create security infrastructure using modular stack
        self.security_stack = SecurityStack(
            self,
            "Security",
            vpc=self.vpc,
            env_name=self.env_name,
            enable_strict_nacls=env_config.security.enable_strict_nacls,
            **kwargs
        )
        
        # Get security groups reference
        self.security_groups = self.security_stack.security_groups
        
        # Create IAM infrastructure using dedicated stack
        self.iam_stack = IAMStack(
            self,
            "IAM",
            env_name=self.env_name,
            enable_enhanced_permissions=env_config.is_production,
            **kwargs
        )
        
        # Get IAM roles reference
        self.iam_roles = self.iam_stack.all_roles
        
        # Create CloudWatch resources
        self.log_groups = self._create_cloudwatch_resources()
        
        # Create configuration management using dedicated stack
        self.config_stack = ConfigurationStack(
            self,
            "Config",
            env_config=env_config,
            vpc=self.vpc,
            iam_roles=self.iam_roles,
            **kwargs
        )
        
        # Create comprehensive monitoring stack
        self.monitoring_stack = MonitoringStack(
            self,
            "Monitoring",
            env_name=self.env_name,
            vpc=self.vpc,
            notification_email=env_config.monitoring.alarm_notification_email,
            enable_detailed_monitoring=env_config.monitoring.enable_detailed_monitoring,
            enable_cost_alerts=env_config.monitoring.enable_cost_alerts,
            log_retention_days=env_config.monitoring.log_retention_days,
            **kwargs
        )
        
        # Create basic CloudWatch dashboard (legacy - now supplemented by monitoring stack)
        self._create_monitoring_dashboard()
        
        # Output important resource identifiers
        self._create_stack_outputs()

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources in this stack"""
        # Tags are now handled through env_config.resource_tags
        
        for key, value in self.env_config.resource_tags.items():
            Tags.of(self).add(key, value)

    @property
    def lambda_execution_role(self) -> iam.Role:
        """Get Lambda execution role from IAM stack"""
        return self.iam_stack.lambda_execution_role
    
    @property
    def ecs_execution_role(self) -> iam.Role:
        """Get ECS execution role from IAM stack"""
        return self.iam_stack.ecs_execution_role
    
    @property
    def ecs_task_role(self) -> iam.Role:
        """Get ECS task role from IAM stack"""
        return self.iam_stack.ecs_task_role

    def _create_cloudwatch_resources(self) -> Dict[str, logs.LogGroup]:
        """
        Create CloudWatch log groups and basic monitoring setup
        
        Returns:
            Dict[str, logs.LogGroup]: Dictionary of created log groups
        """
        log_groups = {}
        
        # Get retention period from environment config
        if self.env_config.monitoring.log_retention_days <= 7:
            retention = logs.RetentionDays.ONE_WEEK
        elif self.env_config.monitoring.log_retention_days <= 14:
            retention = logs.RetentionDays.TWO_WEEKS
        elif self.env_config.monitoring.log_retention_days <= 30:
            retention = logs.RetentionDays.ONE_MONTH
        elif self.env_config.monitoring.log_retention_days <= 90:
            retention = logs.RetentionDays.THREE_MONTHS
        else:
            retention = logs.RetentionDays.ONE_YEAR
        
        removal_policy = RemovalPolicy.RETAIN if self.env_config.is_production else RemovalPolicy.DESTROY
        
        # Application Log Group
        log_groups["app"] = logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"{self.env_config.get_log_group_prefix()}/application",
            retention=retention,
            removal_policy=removal_policy,
        )
        
        # API Gateway Log Group
        log_groups["api"] = logs.LogGroup(
            self,
            "APIGatewayLogGroup",
            log_group_name=f"{self.env_config.get_log_group_prefix()}/apigateway",
            retention=retention,
            removal_policy=removal_policy,
        )
        
        # Lambda Log Group (will be created automatically, but we set retention)
        log_groups["lambda"] = logs.LogGroup(
            self,
            "LambdaLogGroup",
            log_group_name=f"/aws/lambda/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )
        
        return log_groups

    def _create_legacy_parameter_store_entries(self) -> None:
        """Create legacy Parameter Store entries for backward compatibility"""
        
        # Legacy parameters for backward compatibility
        # Main configuration is now handled by ConfigurationStack
        parameters = {
            "lambda-execution-role-arn": self.lambda_execution_role.role_arn,
            "ecs-execution-role-arn": self.ecs_execution_role.role_arn,
            "ecs-task-role-arn": self.ecs_task_role.role_arn,
        }
        
        for key, value in parameters.items():
            ssm.StringParameter(
                self,
                f"LegacyParameter{key.replace('-', '').title()}",
                parameter_name=f"/options-strategy/{self.env_name}/legacy/{key}",
                string_value=value,
                description=f"Legacy parameter - {key} for {self.env_name} (use ConfigurationStack instead)",
            )

    def _create_monitoring_dashboard(self) -> None:
        """Create CloudWatch dashboard for basic monitoring"""
        
        dashboard = cloudwatch.Dashboard(
            self,
            "OptionsStrategyDashboard",
            dashboard_name=f"OptionsStrategy-{self.env_name}",
        )
        
        # Add platform metrics widget
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Platform Overview",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Logs",
                        metric_name="IncomingLogEvents",
                        dimensions_map={"LogGroupName": f"{self.env_config.get_log_group_prefix()}/application"},
                    )
                ],
                width=12,
                height=6,
            )
        )

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for important resource identifiers"""
        
        # Core infrastructure outputs
        CfnOutput(
            self,
            "VPCId",
            value=self.vpc.vpc_id,
            description="VPC ID for the platform",
            export_name=f"OptionsStrategy-{self.env_name}-VPC-ID",
        )
        
        CfnOutput(
            self,
            "EnvironmentName",
            value=self.env_name,
            description="Environment name",
            export_name=f"OptionsStrategy-{self.env_name}-Environment",
        )
        
        # Stack references
        CfnOutput(
            self,
            "IAMStackName",
            value=self.iam_stack.stack_name,
            description="IAM stack name",
            export_name=f"OptionsStrategy-{self.env_name}-IAM-Stack",
        )
        
        CfnOutput(
            self,
            "ConfigStackName",
            value=self.config_stack.stack_name,
            description="Configuration stack name",
            export_name=f"OptionsStrategy-{self.env_name}-Config-Stack",
        )
        
        CfnOutput(
            self,
            "MonitoringStackName",
            value=self.monitoring_stack.stack_name,
            description="Monitoring stack name",
            export_name=f"OptionsStrategy-{self.env_name}-Monitoring-Stack",
        )