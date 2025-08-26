"""
IAM Stack for Options Strategy Lifecycle Platform

This module defines the IAM roles, policies, and permissions for the Options Strategy
Lifecycle Platform, following the principle of least privilege and designed for
deployment in ap-south-1 (Asia Pacific - Mumbai) region to comply with Indian
market data residency requirements.

The stack creates role-based access patterns for different service types:
- Lambda execution roles with VPC access and Parameter Store permissions
- ECS execution and task roles for containerized workloads
- API Gateway execution roles for REST API operations
- Event-driven roles for EventBridge and SQS integration
- Database access roles for RDS and DynamoDB operations

All roles are environment-scoped and include comprehensive logging permissions
for CloudWatch integration and security auditing.
"""

import os
from typing import Dict, List, Optional, Any
from aws_cdk import (
    Stack,
    StackProps,
    CfnOutput,
    Tags,
    aws_iam as iam,
)
from constructs import Construct
from ..constructs.iam_construct import OptionsStrategyIAMConstruct


class IAMStack(Stack):
    """
    Dedicated IAM Stack for Options Strategy Lifecycle Platform
    
    This stack manages all IAM resources including roles, policies, and service
    principals required by the platform. It provides a centralized location
    for access control management and follows AWS security best practices.
    
    Features:
    - Environment-specific role naming and scoping
    - Principle of least privilege access policies
    - Comprehensive Parameter Store permissions for configuration management
    - CloudWatch logging permissions for all services
    - Cross-service communication policies
    - Indian market data residency compliance through ap-south-1 deployment
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        enable_enhanced_permissions: bool = False,
        **kwargs
    ) -> None:
        """
        Initialize the IAM Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            enable_enhanced_permissions: Enable additional permissions for production
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.enable_enhanced_permissions = enable_enhanced_permissions
        
        # Apply standard tags to all resources in this stack
        self._apply_standard_tags()
        
        # Create IAM construct for common role patterns
        self.iam_construct = OptionsStrategyIAMConstruct(
            self,
            "OptionsStrategyIAM",
            env_name=env_name,
            enable_enhanced_permissions=enable_enhanced_permissions,
        )
        
        # Create service-specific roles
        self.service_roles = self._create_service_roles()
        
        # Create cross-service policies
        self.cross_service_policies = self._create_cross_service_policies()
        
        # Create CloudFormation outputs
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
            "Stack": "IAM",
            "Component": "security",
        }
        
        for key, value in tags_config.items():
            Tags.of(self).add(key, value)

    def _create_service_roles(self) -> Dict[str, iam.Role]:
        """
        Create service-specific IAM roles beyond the common patterns
        
        Returns:
            Dict[str, iam.Role]: Dictionary of service-specific IAM roles
        """
        roles = {}
        
        # API Gateway Execution Role
        roles["api_gateway"] = iam.Role(
            self,
            "APIGatewayExecutionRole",
            role_name=f"options-strategy-api-gateway-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                )
            ],
        )
        
        # Add custom API Gateway policy
        api_gateway_policy = iam.Policy(
            self,
            "APIGatewayCustomPolicy",
            policy_name=f"options-strategy-api-gateway-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:InvokeFunction",
                    ],
                    resources=[
                        f"arn:aws:lambda:{self.region}:{self.account}:function:options-strategy-{self.env_name}-*"
                    ],
                ),
            ],
        )
        roles["api_gateway"].attach_inline_policy(api_gateway_policy)
        
        # EventBridge Role for event-driven architecture
        roles["eventbridge"] = iam.Role(
            self,
            "EventBridgeRole",
            role_name=f"options-strategy-eventbridge-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
        )
        
        # Add EventBridge policy for cross-service integration
        eventbridge_policy = iam.Policy(
            self,
            "EventBridgeCustomPolicy",
            policy_name=f"options-strategy-eventbridge-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:InvokeFunction",
                        "sqs:SendMessage",
                        "sns:Publish",
                    ],
                    resources=[
                        f"arn:aws:lambda:{self.region}:{self.account}:function:options-strategy-{self.env_name}-*",
                        f"arn:aws:sqs:{self.region}:{self.account}:options-strategy-{self.env_name}-*",
                        f"arn:aws:sns:{self.region}:{self.account}:options-strategy-{self.env_name}-*",
                    ],
                ),
            ],
        )
        roles["eventbridge"].attach_inline_policy(eventbridge_policy)
        
        # Database Access Role for applications
        roles["database_access"] = iam.Role(
            self,
            "DatabaseAccessRole",
            role_name=f"options-strategy-db-access-role-{self.env_name}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com")
            ),
        )
        
        # Add database access policy
        db_policy_statements = [
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:BatchGetItem",
                    "dynamodb:BatchWriteItem",
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/options-strategy-{self.env_name}-*"
                ],
            ),
        ]
        
        # Add RDS permissions for production environments
        if self.enable_enhanced_permissions or self.env_name == "prod":
            db_policy_statements.append(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "rds-db:connect",
                    ],
                    resources=[
                        f"arn:aws:rds-db:{self.region}:{self.account}:dbuser:*/options-strategy-{self.env_name}-*"
                    ],
                )
            )
        
        db_access_policy = iam.Policy(
            self,
            "DatabaseAccessPolicy",
            policy_name=f"options-strategy-db-access-policy-{self.env_name}",
            statements=db_policy_statements,
        )
        roles["database_access"].attach_inline_policy(db_access_policy)
        
        return roles

    def _create_cross_service_policies(self) -> Dict[str, iam.Policy]:
        """
        Create policies for cross-service communication
        
        Returns:
            Dict[str, iam.Policy]: Dictionary of cross-service policies
        """
        policies = {}
        
        # Trading Service Communication Policy
        policies["trading_communication"] = iam.Policy(
            self,
            "TradingCommunicationPolicy",
            policy_name=f"options-strategy-trading-comm-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sqs:SendMessage",
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                    ],
                    resources=[
                        f"arn:aws:sqs:{self.region}:{self.account}:options-strategy-{self.env_name}-*"
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sns:Publish",
                        "sns:Subscribe",
                        "sns:Unsubscribe",
                    ],
                    resources=[
                        f"arn:aws:sns:{self.region}:{self.account}:options-strategy-{self.env_name}-*"
                    ],
                ),
            ],
        )
        
        # Monitoring and Alerting Policy
        policies["monitoring"] = iam.Policy(
            self,
            "MonitoringPolicy",
            policy_name=f"options-strategy-monitoring-policy-{self.env_name}",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "cloudwatch:PutMetricData",
                        "cloudwatch:GetMetricStatistics",
                        "cloudwatch:ListMetrics",
                    ],
                    resources=["*"],  # CloudWatch metrics require wildcard
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams",
                    ],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/*/options-strategy-{self.env_name}-*"
                    ],
                ),
            ],
        )
        
        return policies

    @property
    def lambda_execution_role(self) -> iam.Role:
        """Get Lambda execution role from IAM construct"""
        return self.iam_construct.lambda_execution_role

    @property
    def ecs_execution_role(self) -> iam.Role:
        """Get ECS execution role from IAM construct"""
        return self.iam_construct.ecs_execution_role

    @property
    def ecs_task_role(self) -> iam.Role:
        """Get ECS task role from IAM construct"""
        return self.iam_construct.ecs_task_role

    @property
    def all_roles(self) -> Dict[str, iam.Role]:
        """Get all IAM roles created in this stack"""
        all_roles = {}
        all_roles.update(self.iam_construct.roles)
        all_roles.update(self.service_roles)
        return all_roles

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for important IAM resource identifiers"""
        
        # Core service role outputs
        CfnOutput(
            self,
            "LambdaExecutionRoleArn",
            value=self.lambda_execution_role.role_arn,
            description="ARN of Lambda execution role",
            export_name=f"OptionsStrategy-{self.env_name}-Lambda-Role-ARN",
        )
        
        CfnOutput(
            self,
            "ECSExecutionRoleArn",
            value=self.ecs_execution_role.role_arn,
            description="ARN of ECS execution role",
            export_name=f"OptionsStrategy-{self.env_name}-ECS-Execution-Role-ARN",
        )
        
        CfnOutput(
            self,
            "ECSTaskRoleArn",
            value=self.ecs_task_role.role_arn,
            description="ARN of ECS task role",
            export_name=f"OptionsStrategy-{self.env_name}-ECS-Task-Role-ARN",
        )
        
        # Service-specific role outputs
        CfnOutput(
            self,
            "APIGatewayRoleArn",
            value=self.service_roles["api_gateway"].role_arn,
            description="ARN of API Gateway execution role",
            export_name=f"OptionsStrategy-{self.env_name}-APIGateway-Role-ARN",
        )
        
        CfnOutput(
            self,
            "EventBridgeRoleArn",
            value=self.service_roles["eventbridge"].role_arn,
            description="ARN of EventBridge execution role",
            export_name=f"OptionsStrategy-{self.env_name}-EventBridge-Role-ARN",
        )
        
        CfnOutput(
            self,
            "DatabaseAccessRoleArn",
            value=self.service_roles["database_access"].role_arn,
            description="ARN of database access role",
            export_name=f"OptionsStrategy-{self.env_name}-Database-Role-ARN",
        )