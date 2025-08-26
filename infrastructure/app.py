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
        env_name: str = "dev",
        vpc_cidr: str = "10.0.0.0/16",
        max_azs: int = 2,
        **kwargs
    ) -> None:
        """
        Initialize the Options Strategy Platform Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            vpc_cidr: CIDR block for the VPC
            max_azs: Maximum number of availability zones
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.vpc_cidr = vpc_cidr
        self.max_azs = max_azs
        
        # Apply standard tags to all resources in this stack
        self._apply_standard_tags()
        
        # Create networking infrastructure using modular stack
        self.networking_stack = NetworkingStack(
            scope,
            f"{construct_id}-Networking",
            env_name=env_name,
            vpc_cidr=vpc_cidr,
            max_azs=max_azs,
            **kwargs
        )
        
        # Get VPC reference from networking stack
        self.vpc = self.networking_stack.vpc
        
        # Create security infrastructure using modular stack
        self.security_stack = SecurityStack(
            scope,
            f"{construct_id}-Security",
            vpc=self.vpc,
            env_name=env_name,
            enable_strict_nacls=(env_name == "prod"),
            **kwargs
        )
        
        # Get security groups reference
        self.security_groups = self.security_stack.security_groups
        
        # Create IAM roles and policies
        self.iam_roles = self._create_iam_roles()
        
        # Create CloudWatch resources
        self.log_groups = self._create_cloudwatch_resources()
        
        # Create Parameter Store entries
        self._create_parameter_store_entries()
        
        # Create CloudWatch dashboard
        self._create_monitoring_dashboard()
        
        # Output important resource identifiers
        self._create_stack_outputs()

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources in this stack"""
        tags_config = {
            "Project": "OptionsStrategyPlatform",
            "Environment": self.env_name,
            "Owner": "platform-team",
            "CostCenter": "trading-systems",
            "DataResidency": "india",
            "ManagedBy": "CDK",
            "Stack": self.stack_name,
        }
        
        for key, value in tags_config.items():
            Tags.of(self).add(key, value)

    def _create_iam_roles(self) -> Dict[str, iam.Role]:
        """
        Create IAM roles and policies following principle of least privilege
        
        Returns:
            Dict[str, iam.Role]: Dictionary of created IAM roles
        """
        roles = {}
        
        # Lambda Execution Role
        roles["lambda_execution"] = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=f"options-strategy-lambda-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ],
        )
        
        # Add custom policy for Lambda functions
        lambda_policy = iam.Policy(
            self,
            "LambdaCustomPolicy",
            policy_name=f"options-strategy-lambda-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath",
                    ],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/{self.env_name}/*"
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/options-strategy-{self.env_name}-*"
                    ],
                ),
            ],
        )
        
        roles["lambda_execution"].attach_inline_policy(lambda_policy)
        
        # ECS Task Execution Role
        roles["ecs_execution"] = iam.Role(
            self,
            "ECSExecutionRole",
            role_name=f"options-strategy-ecs-execution-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )
        
        # ECS Task Role
        roles["ecs_task"] = iam.Role(
            self,
            "ECSTaskRole",
            role_name=f"options-strategy-ecs-task-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        
        # Add custom policy for ECS tasks
        ecs_policy = iam.Policy(
            self,
            "ECSTaskCustomPolicy",
            policy_name=f"options-strategy-ecs-task-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath",
                    ],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/{self.env_name}/*"
                    ],
                ),
            ],
        )
        
        roles["ecs_task"].attach_inline_policy(ecs_policy)
        
        return roles

    def _create_cloudwatch_resources(self) -> Dict[str, logs.LogGroup]:
        """
        Create CloudWatch log groups and basic monitoring setup
        
        Returns:
            Dict[str, logs.LogGroup]: Dictionary of created log groups
        """
        log_groups = {}
        
        # Application Log Group
        log_groups["app"] = logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"/aws/application/options-strategy/{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # API Gateway Log Group
        log_groups["api"] = logs.LogGroup(
            self,
            "APIGatewayLogGroup",
            log_group_name=f"/aws/apigateway/options-strategy/{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # Lambda Log Group (will be created automatically, but we set retention)
        log_groups["lambda"] = logs.LogGroup(
            self,
            "LambdaLogGroup",
            log_group_name=f"/aws/lambda/options-strategy-{self.env_name}",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        return log_groups

    def _create_parameter_store_entries(self) -> None:
        """Create Parameter Store entries for configuration management"""
        
        # Environment-specific parameters
        parameters = {
            "environment": self.env_name,
            "region": self.region,
            "lambda-execution-role-arn": self.iam_roles["lambda_execution"].role_arn,
            "ecs-execution-role-arn": self.iam_roles["ecs_execution"].role_arn,
            "ecs-task-role-arn": self.iam_roles["ecs_task"].role_arn,
        }
        
        for key, value in parameters.items():
            ssm.StringParameter(
                self,
                f"Parameter{key.replace('-', '').title()}",
                parameter_name=f"/options-strategy/{self.env_name}/{key}",
                string_value=value,
                description=f"Options Strategy Platform - {key} for {self.env_name}",
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
                        dimensions_map={"LogGroupName": f"/aws/application/options-strategy/{self.env_name}"},
                    )
                ],
                width=12,
                height=6,
            )
        )

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for important resource identifiers"""
        
        CfnOutput(
            self,
            "LambdaExecutionRoleArn",
            value=self.iam_roles["lambda_execution"].role_arn,
            description="ARN of Lambda execution role",
            export_name=f"OptionsStrategy-{self.env_name}-Lambda-Role-ARN",
        )
        
        CfnOutput(
            self,
            "ECSExecutionRoleArn",
            value=self.iam_roles["ecs_execution"].role_arn,
            description="ARN of ECS execution role",
            export_name=f"OptionsStrategy-{self.env_name}-ECS-Execution-Role-ARN",
        )
        
        CfnOutput(
            self,
            "ECSTaskRoleArn",
            value=self.iam_roles["ecs_task"].role_arn,
            description="ARN of ECS task role",
            export_name=f"OptionsStrategy-{self.env_name}-ECS-Task-Role-ARN",
        )