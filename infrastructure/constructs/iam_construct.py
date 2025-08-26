"""
Reusable IAM Construct for Options Strategy Lifecycle Platform

This module provides a reusable construct for creating common IAM role patterns
used across the Options Strategy Lifecycle Platform. It encapsulates best practices
for role creation, policy attachment, and permission management.

The construct follows the principle of least privilege and is designed for
deployment in ap-south-1 (Asia Pacific - Mumbai) region to comply with Indian
market data residency requirements.

Key Features:
- Standardized role naming conventions
- Environment-scoped permissions
- Comprehensive Parameter Store access patterns
- CloudWatch logging permissions for all services
- Secure service-to-service communication policies
"""

from typing import Dict, List, Optional
from aws_cdk import (
    aws_iam as iam,
    Tags,
)
from constructs import Construct


class OptionsStrategyIAMConstruct(Construct):
    """
    Reusable IAM construct for common role patterns

    This construct provides standardized IAM roles for common service patterns
    in the Options Strategy Platform, including Lambda functions, ECS tasks,
    and other AWS services. It ensures consistent permission management and
    follows security best practices.

    Features:
    - Lambda execution roles with VPC and Parameter Store access
    - ECS execution and task roles for containerized workloads
    - Standardized policy templates for common access patterns
    - Environment-specific resource scoping
    - Comprehensive logging permissions
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        enable_enhanced_permissions: bool = False,
        custom_parameter_paths: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the IAM construct

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            enable_enhanced_permissions: Enable additional permissions for production
            custom_parameter_paths: Additional Parameter Store paths to grant access to
        """
        super().__init__(scope, construct_id)

        self.env_name = env_name
        self.enable_enhanced_permissions = enable_enhanced_permissions
        self.custom_parameter_paths = custom_parameter_paths or []

        # Get stack context for resource ARN construction
        from aws_cdk import Stack
        stack = Stack.of(self)
        self.region = stack.region
        self.account = stack.account

        # Apply standard tags
        self._apply_standard_tags()

        # Create common IAM roles
        self.roles = self._create_common_roles()

        # Store references to frequently used roles
        self.lambda_execution_role = self.roles["lambda_execution"]
        self.ecs_execution_role = self.roles["ecs_execution"]
        self.ecs_task_role = self.roles["ecs_task"]

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources in this construct"""
        tags_config = {
            "Project": "OptionsStrategyPlatform",
            "Environment": self.env_name,
            "Owner": "platform-team",
            "CostCenter": "trading-systems",
            "DataResidency": "india",
            "ManagedBy": "CDK",
            "Component": "iam-construct",
        }

        for key, value in tags_config.items():
            Tags.of(self).add(key, value)

    def _create_common_roles(self) -> Dict[str, iam.Role]:
        """
        Create common IAM roles used across the platform

        Returns:
            Dict[str, iam.Role]: Dictionary of created IAM roles
        """
        roles = {}

        # Lambda Execution Role
        roles["lambda_execution"] = self._create_lambda_execution_role()

        # ECS Execution Role
        roles["ecs_execution"] = self._create_ecs_execution_role()

        # ECS Task Role
        roles["ecs_task"] = self._create_ecs_task_role()

        return roles

    def _create_lambda_execution_role(self) -> iam.Role:
        """
        Create Lambda execution role with comprehensive permissions

        Returns:
            iam.Role: Lambda execution role
        """
        role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=f"options-strategy-lambda-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ],
            description=f"Lambda execution role for Options Strategy Platform - {self.env_name}",
        )

        # Create custom policy for Lambda functions
        lambda_policy = iam.Policy(
            self,
            "LambdaCustomPolicy",
            policy_name=f"options-strategy-lambda-policy-{self.env_name}",
            statements=self._get_lambda_policy_statements(),
        )

        role.attach_inline_policy(lambda_policy)
        return role

    def _create_ecs_execution_role(self) -> iam.Role:
        """
        Create ECS execution role for container management

        Returns:
            iam.Role: ECS execution role
        """
        role = iam.Role(
            self,
            "ECSExecutionRole",
            role_name=f"options-strategy-ecs-execution-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
            description=f"ECS execution role for Options Strategy Platform - {self.env_name}",
        )

        # Add custom policy for ECS execution
        ecs_execution_policy = iam.Policy(
            self,
            "ECSExecutionCustomPolicy",
            policy_name=f"options-strategy-ecs-execution-policy-{self.env_name}",
            statements=self._get_ecs_execution_policy_statements(),
        )

        role.attach_inline_policy(ecs_execution_policy)
        return role

    def _create_ecs_task_role(self) -> iam.Role:
        """
        Create ECS task role for application-level permissions

        Returns:
            iam.Role: ECS task role
        """
        role = iam.Role(
            self,
            "ECSTaskRole",
            role_name=f"options-strategy-ecs-task-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description=f"ECS task role for Options Strategy Platform - {self.env_name}",
        )

        # Add custom policy for ECS tasks
        ecs_task_policy = iam.Policy(
            self,
            "ECSTaskCustomPolicy",
            policy_name=f"options-strategy-ecs-task-policy-{self.env_name}",
            statements=self._get_ecs_task_policy_statements(),
        )

        role.attach_inline_policy(ecs_task_policy)
        return role

    def _get_lambda_policy_statements(self) -> List[iam.PolicyStatement]:
        """
        Get policy statements for Lambda execution role

        Returns:
            List[iam.PolicyStatement]: Lambda policy statements
        """
        statements = [
            # Parameter Store access
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                ],
                resources=self._get_parameter_store_arns(),
            ),
            # CloudWatch logging
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/options-strategy-{self.env_name}-*",
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/options-strategy-{self.env_name}-*:log-stream:*",
                ],
            ),
            # X-Ray tracing for enhanced monitoring
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],
            ),
        ]

        # Add enhanced permissions for production environments
        if self.enable_enhanced_permissions or self.env_name == "prod":
            statements.extend(self._get_enhanced_lambda_permissions())

        return statements

    def _get_ecs_execution_policy_statements(
        self,
    ) -> List[iam.PolicyStatement]:
        """
        Get policy statements for ECS execution role

        Returns:
            List[iam.PolicyStatement]: ECS execution policy statements
        """
        return [
            # ECR access for container images
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=[
                    f"arn:aws:ecr:{self.region}:{self.account}:repository/options-strategy-{self.env_name}/*",
                    f"arn:aws:ecr:{self.region}:{self.account}:repository/*",  # For base images
                ],
            ),
            # Parameter Store access for secrets
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                ],
                resources=self._get_parameter_store_arns(),
            ),
        ]

    def _get_ecs_task_policy_statements(self) -> List[iam.PolicyStatement]:
        """
        Get policy statements for ECS task role

        Returns:
            List[iam.PolicyStatement]: ECS task policy statements
        """
        statements = [
            # Parameter Store access for application configuration
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                ],
                resources=self._get_parameter_store_arns(),
            ),
            # CloudWatch metrics and logging
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "cloudwatch:PutMetricData",
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/ecs/options-strategy-{self.env_name}*",
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/ecs/options-strategy-{self.env_name}*:log-stream:*",
                ],
            ),
            # X-Ray tracing
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],
            ),
        ]

        # Add enhanced permissions for production environments
        if self.enable_enhanced_permissions or self.env_name == "prod":
            statements.extend(self._get_enhanced_ecs_permissions())

        return statements

    def _get_enhanced_lambda_permissions(self) -> List[iam.PolicyStatement]:
        """
        Get enhanced permissions for Lambda in production environments

        Returns:
            List[iam.PolicyStatement]: Enhanced Lambda policy statements
        """
        return [
            # VPC Endpoint access for secure communication
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AttachNetworkInterface",
                    "ec2:DetachNetworkInterface",
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "ec2:ResourceTag/Project": "OptionsStrategyPlatform",
                        "ec2:ResourceTag/Environment": self.env_name,
                    }
                },
            ),
            # KMS access for encryption
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                ],
                resources=[f"arn:aws:kms:{self.region}:{self.account}:key/*"],
                conditions={
                    "StringEquals": {
                        "kms:ViaService": [f"ssm.{self.region}.amazonaws.com"]
                    }
                },
            ),
        ]

    def _get_enhanced_ecs_permissions(self) -> List[iam.PolicyStatement]:
        """
        Get enhanced permissions for ECS in production environments

        Returns:
            List[iam.PolicyStatement]: Enhanced ECS policy statements
        """
        return [
            # Service discovery for microservices
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "servicediscovery:DiscoverInstances",
                    "servicediscovery:GetService",
                    "servicediscovery:ListServices",
                ],
                resources=[
                    f"arn:aws:servicediscovery:{self.region}:{self.account}:service/*"
                ],
            ),
            # Application Load Balancer target group registration
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "elasticloadbalancing:RegisterTargets",
                    "elasticloadbalancing:DeregisterTargets",
                ],
                resources=[
                    f"arn:aws:elasticloadbalancing:{self.region}:{self.account}:targetgroup/options-strategy-{self.env_name}-*"
                ],
            ),
        ]

    def _get_parameter_store_arns(self) -> List[str]:
        """
        Get Parameter Store ARNs for access permissions

        Returns:
            List[str]: Parameter Store ARN patterns
        """
        base_arns = [
            f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/{self.env_name}/*",
            f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/shared/*",
        ]

        # Add custom parameter paths if specified
        for path in self.custom_parameter_paths:
            base_arns.append(
                f"arn:aws:ssm:{self.region}:{self.account}:parameter{path}/*"
            )

        return base_arns

    def create_custom_role(
        self,
        role_id: str,
        role_name: str,
        service_principal: str,
        policy_statements: List[iam.PolicyStatement],
        managed_policies: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> iam.Role:
        """
        Create a custom IAM role with specified permissions

        Args:
            role_id: Construct ID for the role
            role_name: IAM role name
            service_principal: AWS service that can assume this role
            policy_statements: List of policy statements to attach
            managed_policies: List of managed policy ARNs to attach
            description: Role description

        Returns:
            iam.Role: Created IAM role
        """
        # Create the role
        role = iam.Role(
            self,
            role_id,
            role_name=f"options-strategy-{role_name}-{self.env_name}",
            assumed_by=iam.ServicePrincipal(service_principal),
            description=description
            or f"Custom role for {role_name} in {self.env_name} environment",
        )

        # Attach managed policies if specified
        if managed_policies:
            for policy_arn in managed_policies:
                role.add_managed_policy(
                    iam.ManagedPolicy.from_managed_policy_arn(
                        self, f"{role_id}ManagedPolicy", policy_arn
                    )
                )

        # Create and attach custom policy if statements are provided
        if policy_statements:
            custom_policy = iam.Policy(
                self,
                f"{role_id}CustomPolicy",
                policy_name=f"options-strategy-{role_name}-policy-{self.env_name}",
                statements=policy_statements,
            )
            role.attach_inline_policy(custom_policy)

        return role

    def add_parameter_store_access(
        self,
        role: iam.Role,
        parameter_paths: List[str],
        actions: Optional[List[str]] = None,
    ) -> None:
        """
        Add Parameter Store access to an existing role

        Args:
            role: IAM role to modify
            parameter_paths: List of parameter paths to grant access to
            actions: List of SSM actions to allow (defaults to read-only)
        """
        if not actions:
            actions = [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath",
            ]

        # Create ARNs for parameter paths
        parameter_arns = []
        for path in parameter_paths:
            parameter_arns.append(
                f"arn:aws:ssm:{self.region}:{self.account}:parameter{path}/*"
            )

        # Create and attach policy
        policy = iam.Policy(
            self,
            f"{role.role_name}ParameterAccess",
            policy_name=f"{role.role_name}-parameter-access",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=actions,
                    resources=parameter_arns,
                )
            ],
        )

        role.attach_inline_policy(policy)
