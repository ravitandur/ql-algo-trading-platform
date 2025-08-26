"""
Simplified CDK Stack for Options Strategy Lifecycle Platform

This module defines a simplified, single-stack approach to avoid circular dependencies
during development and testing. Once the architecture is stable, this can be refactored
back to the modular approach.
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


class SimpleOptionsStrategyStack(Stack):
    """
    Simplified CDK Stack for Options Strategy Lifecycle Platform
    
    This stack creates the foundational infrastructure in a single stack
    to avoid circular dependency issues during development.
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
        Initialize the Simple Options Strategy Platform Stack
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.vpc_cidr = vpc_cidr
        self.max_azs = max_azs
        
        # Apply standard tags
        self._apply_standard_tags()
        
        # Create VPC
        self._create_vpc()
        
        # Create IAM resources
        self._create_iam_resources()
        
        # Create CloudWatch resources
        self._create_cloudwatch_resources()
        
        # Create Parameter Store entries
        self._create_parameter_store()
        
        # Create outputs
        self._create_outputs()

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources"""
        tags = {
            "Project": "OptionsStrategyPlatform",
            "Environment": self.env_name,
            "Region": "ap-south-1",
            "DataResidency": "India",
            "CostCenter": "Trading",
            "Owner": "TradingTeam",
        }
        
        for key, value in tags.items():
            Tags.of(self).add(key, value)

    def _create_vpc(self) -> None:
        """Create VPC and networking components"""
        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "OptionsStrategyVPC",
            vpc_name=f"options-strategy-vpc-{self.env_name}",
            ip_addresses=ec2.IpAddresses.cidr(self.vpc_cidr),
            max_azs=self.max_azs,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateApp",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateDB",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            nat_gateway_provider=ec2.NatProvider.gateway(),
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )
        
        # Create Security Groups
        self.alb_sg = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )
        
        self.app_sg = ec2.SecurityGroup(
            self,
            "ApplicationSecurityGroup",
            vpc=self.vpc,
            description="Security group for application servers",
            allow_all_outbound=True,
        )
        
        self.db_sg = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for databases",
            allow_all_outbound=False,
        )
        
        # Configure security group rules
        self.alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS from anywhere",
        )
        
        self.app_sg.add_ingress_rule(
            peer=self.alb_sg,
            connection=ec2.Port.tcp(8000),
            description="App port from ALB",
        )
        
        self.db_sg.add_ingress_rule(
            peer=self.app_sg,
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from app servers",
        )

    def _create_iam_resources(self) -> None:
        """Create IAM roles and policies"""
        # Lambda execution role
        self.lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=f"options-strategy-lambda-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )
        
        # ECS task execution role
        self.ecs_execution_role = iam.Role(
            self,
            "ECSExecutionRole",
            role_name=f"options-strategy-ecs-execution-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )
        
        # ECS task role
        self.ecs_task_role = iam.Role(
            self,
            "ECSTaskRole",
            role_name=f"options-strategy-ecs-task-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

    def _create_cloudwatch_resources(self) -> None:
        """Create CloudWatch log groups and monitoring"""
        # Determine retention based on environment
        retention = logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH
        removal_policy = RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN
        
        # Application logs
        self.app_log_group = logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"/aws/ecs/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )
        
        # Lambda logs
        self.lambda_log_group = logs.LogGroup(
            self,
            "LambdaLogGroup",
            log_group_name=f"/aws/lambda/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )
        
        # API Gateway logs
        self.api_log_group = logs.LogGroup(
            self,
            "APILogGroup",
            log_group_name=f"/aws/apigateway/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )

    def _create_parameter_store(self) -> None:
        """Create Parameter Store entries"""
        parameters = {
            "vpc-id": self.vpc.vpc_id,
            "vpc-cidr": self.vpc_cidr,
            "public-subnet-ids": ",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            "private-subnet-ids": ",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            "isolated-subnet-ids": ",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            "alb-sg-id": self.alb_sg.security_group_id,
            "app-sg-id": self.app_sg.security_group_id,
            "db-sg-id": self.db_sg.security_group_id,
            "lambda-role-arn": self.lambda_role.role_arn,
            "ecs-execution-role-arn": self.ecs_execution_role.role_arn,
            "ecs-task-role-arn": self.ecs_task_role.role_arn,
        }
        
        for key, value in parameters.items():
            ssm.StringParameter(
                self,
                f"Parameter{key.replace('-', '').title()}",
                parameter_name=f"/options-strategy/{self.env_name}/{key}",
                string_value=value,
                description=f"{key} for Options Strategy Platform {self.env_name}",
            )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs"""
        CfnOutput(self, "VPCId", value=self.vpc.vpc_id)
        CfnOutput(self, "VPCCidr", value=self.vpc_cidr)
        CfnOutput(self, "Environment", value=self.env_name)
        CfnOutput(self, "LambdaRoleArn", value=self.lambda_role.role_arn)
        CfnOutput(self, "ECSExecutionRoleArn", value=self.ecs_execution_role.role_arn)
        CfnOutput(self, "ECSTaskRoleArn", value=self.ecs_task_role.role_arn)