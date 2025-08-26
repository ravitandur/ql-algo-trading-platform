"""
Main CDK Stack for Options Strategy Lifecycle Platform

This module defines the core AWS infrastructure stack for the Options Strategy
Lifecycle Platform, including VPC, security groups, IAM roles, and foundational
services required for the trading platform.

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


class OptionsStrategyPlatformStack(Stack):
    """
    Main CDK Stack for Options Strategy Lifecycle Platform
    
    This stack creates the foundational infrastructure including:
    - VPC with public and private subnets across multiple AZs
    - Security groups for different service layers
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
        **kwargs
    ) -> None:
        """
        Initialize the Options Strategy Platform Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Apply standard tags to all resources in this stack
        self._apply_standard_tags()
        
        # Create core networking infrastructure
        self.vpc = self._create_vpc()
        
        # Create security groups
        self.security_groups = self._create_security_groups()
        
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

    def _create_vpc(self) -> ec2.Vpc:
        """
        Create VPC with public and private subnets across multiple AZs
        
        Returns:
            ec2.Vpc: The created VPC
        """
        vpc = ec2.Vpc(
            self,
            "OptionsStrategyVPC",
            vpc_name=f"options-strategy-vpc-{self.env_name}",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,  # Use 3 AZs for high availability
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private-app",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private-db",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )
        
        # Add VPC Flow Logs for security monitoring
        vpc_flow_log_role = iam.Role(
            self,
            "VPCFlowLogRole",
            assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/VPCFlowLogsDeliveryRolePolicy"
                )
            ],
        )
        
        vpc_log_group = logs.LogGroup(
            self,
            "VPCFlowLogGroup",
            log_group_name=f"/aws/vpc/flowlogs/{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                vpc_log_group, vpc_flow_log_role
            ),
        )
        
        return vpc

    def _create_security_groups(self) -> Dict[str, ec2.SecurityGroup]:
        """
        Create security groups for different service layers
        
        Returns:
            Dict[str, ec2.SecurityGroup]: Dictionary of created security groups
        """
        security_groups = {}
        
        # API Gateway / Load Balancer Security Group
        security_groups["alb"] = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            security_group_name=f"options-strategy-alb-sg-{self.env_name}",
        )
        
        security_groups["alb"].add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS traffic from internet",
        )
        
        security_groups["alb"].add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP traffic from internet (redirect to HTTPS)",
        )
        
        # Application / Lambda Security Group
        security_groups["app"] = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=self.vpc,
            description="Security group for application services",
            security_group_name=f"options-strategy-app-sg-{self.env_name}",
        )
        
        security_groups["app"].add_ingress_rule(
            peer=security_groups["alb"],
            connection=ec2.Port.tcp(8080),
            description="Traffic from ALB to application",
        )
        
        # Database Security Group
        security_groups["db"] = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for database services",
            security_group_name=f"options-strategy-db-sg-{self.env_name}",
        )
        
        security_groups["db"].add_ingress_rule(
            peer=security_groups["app"],
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL access from application",
        )
        
        security_groups["db"].add_ingress_rule(
            peer=security_groups["app"],
            connection=ec2.Port.tcp(6379),
            description="Redis access from application",
        )
        
        # Cache Security Group
        security_groups["cache"] = ec2.SecurityGroup(
            self,
            "CacheSecurityGroup",
            vpc=self.vpc,
            description="Security group for caching services",
            security_group_name=f"options-strategy-cache-sg-{self.env_name}",
        )
        
        security_groups["cache"].add_ingress_rule(
            peer=security_groups["app"],
            connection=ec2.Port.tcp(11211),
            description="Memcached access from application",
        )
        
        return security_groups

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
            "vpc-id": self.vpc.vpc_id,
            "private-subnet-ids": ",".join(
                [subnet.subnet_id for subnet in self.vpc.private_subnets]
            ),
            "public-subnet-ids": ",".join(
                [subnet.subnet_id for subnet in self.vpc.public_subnets]
            ),
            "database-security-group-id": self.security_groups["db"].security_group_id,
            "app-security-group-id": self.security_groups["app"].security_group_id,
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
        
        # Add VPC metrics widget
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="VPC Flow Logs",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/VPC",
                        metric_name="PacketsDropped",
                        dimensions_map={"VPC": self.vpc.vpc_id},
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
            "VPCId",
            value=self.vpc.vpc_id,
            description="ID of the created VPC",
            export_name=f"OptionsStrategy-{self.env_name}-VPC-ID",
        )
        
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="IDs of private subnets",
            export_name=f"OptionsStrategy-{self.env_name}-Private-Subnet-IDs",
        )
        
        CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="IDs of public subnets",
            export_name=f"OptionsStrategy-{self.env_name}-Public-Subnet-IDs",
        )
        
        CfnOutput(
            self,
            "DatabaseSecurityGroupId",
            value=self.security_groups["db"].security_group_id,
            description="ID of database security group",
            export_name=f"OptionsStrategy-{self.env_name}-DB-SG-ID",
        )
        
        CfnOutput(
            self,
            "AppSecurityGroupId",
            value=self.security_groups["app"].security_group_id,
            description="ID of application security group",
            export_name=f"OptionsStrategy-{self.env_name}-App-SG-ID",
        )
        
        CfnOutput(
            self,
            "LambdaExecutionRoleArn",
            value=self.iam_roles["lambda_execution"].role_arn,
            description="ARN of Lambda execution role",
            export_name=f"OptionsStrategy-{self.env_name}-Lambda-Role-ARN",
        )