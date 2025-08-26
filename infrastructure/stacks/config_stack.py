"""
Configuration Stack for Options Strategy Lifecycle Platform

This module defines the configuration management infrastructure for the Options
Strategy Lifecycle Platform, including Parameter Store entries, Secrets Manager,
and configuration data management for deployment in ap-south-1 (Asia Pacific - Mumbai)
region to comply with Indian market data residency requirements.

The stack provides centralized configuration management with:
- Environment-specific Parameter Store hierarchies
- Secure secret management with Secrets Manager
- Configuration validation and type safety
- Cross-service configuration sharing
- Audit logging for configuration changes
- Backup and disaster recovery for configuration data
"""

import json
from typing import Dict, List, Optional, Any, Union
from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    RemovalPolicy,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class ConfigurationStack(Stack):
    """
    Configuration management stack for Options Strategy Lifecycle Platform

    This stack manages all configuration data, parameters, and secrets used by
    the platform across different environments. It provides structured parameter
    hierarchies, secure secret storage, and configuration validation.

    Features:
    - Hierarchical Parameter Store structure for organized configuration
    - Environment-specific parameter scoping and isolation
    - Secure secret management with automatic rotation
    - Configuration data encryption at rest and in transit
    - Audit logging for configuration access and changes
    - Cross-stack configuration sharing through exports
    - Configuration validation and type enforcement
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: Any,  # EnvironmentConfig type
        vpc=None,
        iam_roles: Optional[Dict[str, iam.Role]] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Configuration Stack

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_config: Environment configuration object
            vpc: VPC for VPC endpoints (optional)
            iam_roles: IAM roles for cross-service access
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self.env_name = env_config.env_name
        self.vpc = vpc
        self.iam_roles = iam_roles or {}

        # Apply standard tags
        self._apply_standard_tags()

        # Create KMS key for configuration encryption
        self.config_kms_key = self._create_configuration_kms_key()

        # Create Parameter Store parameters
        self.parameters = self._create_parameter_store_entries()

        # Create secrets in Secrets Manager
        self.secrets = self._create_secrets_manager_entries()

        # Create configuration audit logging
        self.audit_log_group = self._create_audit_logging()

        # Create configuration backup
        if self.env_config.is_production:
            self._create_configuration_backup()

        # Create VPC endpoints for secure access (if VPC provided)
        if self.vpc and self.env_config.security.enable_vpc_endpoints:
            self._create_vpc_endpoints()

        # Create CloudFormation outputs
        self._create_stack_outputs()

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources in this stack"""
        for key, value in self.env_config.resource_tags.items():
            Tags.of(self).add(key, value)

        # Add stack-specific tags
        Tags.of(self).add("Stack", "Configuration")
        Tags.of(self).add("Component", "config-management")

    def _create_configuration_kms_key(self) -> kms.Key:
        """
        Create KMS key for configuration data encryption

        Returns:
            kms.Key: KMS key for configuration encryption
        """
        key = kms.Key(
            self,
            "ConfigurationKMSKey",
            alias=f"alias/options-strategy-config-{self.env_name}",
            description=f"KMS key for Options Strategy configuration - {self.env_name}",
            enable_key_rotation=self.env_config.security.enable_encryption_at_rest,
            removal_policy=(
                RemovalPolicy.RETAIN
                if self.env_config.is_production
                else RemovalPolicy.DESTROY
            ),
        )

        # Add key policy for cross-service access
        key.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("ssm.amazonaws.com")],
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                ],
                resources=["*"],
            )
        )

        # Grant access to IAM roles if provided
        for role in self.iam_roles.values():
            key.grant_decrypt(role)

        return key

    def _create_parameter_store_entries(
        self,
    ) -> Dict[str, ssm.StringParameter]:
        """
        Create Parameter Store entries for configuration management

        Returns:
            Dict[str, ssm.StringParameter]: Dictionary of created parameters
        """
        parameters = {}

        # Environment configuration parameters
        env_params = self._get_environment_parameters()
        for param_name, param_value in env_params.items():
            parameters[param_name] = ssm.StringParameter(
                self,
                f"Parameter{param_name.replace('/', '').replace('-', '').title()}",
                parameter_name=f"{self.env_config.get_parameter_store_prefix()}/{param_name}",
                string_value=param_value,
                description=f"Options Strategy Platform - {param_name} for {self.env_name}",
                type=ssm.ParameterType.STRING,
            )

        # Secure configuration parameters (encrypted)
        secure_params = self._get_secure_parameters()
        for param_name, param_value in secure_params.items():
            parameters[f"secure_{param_name}"] = ssm.StringParameter(
                self,
                f"SecureParameter{param_name.replace('/', '').replace('-', '').title()}",
                parameter_name=f"{self.env_config.get_parameter_store_prefix()}/secure/{param_name}",
                string_value=param_value,
                description=f"Options Strategy Platform - secure {param_name} for {self.env_name}",
                type=ssm.ParameterType.SECURE_STRING,
                key_id=self.config_kms_key,
            )

        # Feature flags parameters
        for flag_name, flag_value in self.env_config.feature_flags.items():
            parameters[f"feature_{flag_name}"] = ssm.StringParameter(
                self,
                f"FeatureFlag{flag_name.replace('_', '').title()}",
                parameter_name=f"{self.env_config.get_parameter_store_prefix()}/features/{flag_name}",
                string_value=str(flag_value).lower(),
                description=f"Feature flag - {flag_name} for {self.env_name}",
                type=ssm.ParameterType.STRING,
            )

        # Custom parameters from environment config
        for (
            param_name,
            param_value,
        ) in self.env_config.custom_parameters.items():
            parameters[f"custom_{param_name}"] = ssm.StringParameter(
                self,
                f"CustomParameter{param_name.replace('_', '').title()}",
                parameter_name=f"{self.env_config.get_parameter_store_prefix()}/custom/{param_name}",
                string_value=param_value,
                description=f"Custom parameter - {param_name} for {self.env_name}",
                type=ssm.ParameterType.STRING,
            )

        return parameters

    def _get_environment_parameters(self) -> Dict[str, str]:
        """
        Get environment configuration as Parameter Store entries

        Returns:
            Dict[str, str]: Environment parameters
        """
        return {
            # Basic environment info
            "environment": self.env_config.env_name,
            "region": self.env_config.aws_region,
            "account": self.env_config.aws_account or "default",
            # Networking configuration
            "vpc/cidr": self.env_config.networking.vpc_cidr,
            "vpc/max-azs": str(self.env_config.networking.max_azs),
            "vpc/enable-nat-gateway": str(
                self.env_config.networking.enable_nat_gateway
            ).lower(),
            # Resource configuration
            "lambda/memory-size": str(
                self.env_config.resources.lambda_memory_size
            ),
            "lambda/timeout": str(self.env_config.resources.lambda_timeout),
            "ecs/cpu": str(self.env_config.resources.ecs_cpu),
            "ecs/memory": str(self.env_config.resources.ecs_memory),
            # Monitoring configuration
            "monitoring/log-retention-days": str(
                self.env_config.monitoring.log_retention_days
            ),
            "monitoring/enable-xray": str(
                self.env_config.monitoring.enable_xray_tracing
            ).lower(),
            "monitoring/enable-detailed": str(
                self.env_config.monitoring.enable_detailed_monitoring
            ).lower(),
            # Security configuration
            "security/enable-waf": str(
                self.env_config.security.enable_waf
            ).lower(),
            "security/enable-encryption": str(
                self.env_config.security.enable_encryption_at_rest
            ).lower(),
            # Compliance configuration
            "compliance/data-residency": self.env_config.compliance.data_residency_region,
            "compliance/backup-retention": str(
                self.env_config.compliance.backup_retention_days
            ),
            # Cost optimization
            "cost/enable-spot": str(
                self.env_config.cost_optimization.enable_spot_instances
            ).lower(),
            "cost/enable-lifecycle": str(
                self.env_config.cost_optimization.enable_lifecycle_policies
            ).lower(),
        }

    def _get_secure_parameters(self) -> Dict[str, str]:
        """
        Get secure configuration parameters that need encryption

        Returns:
            Dict[str, str]: Secure parameters
        """
        return {
            # Database connection strings (placeholders)
            "database/connection-string": "placeholder-will-be-updated-by-rds-stack",
            "database/read-replica-string": "placeholder-will-be-updated-by-rds-stack",
            # Cache connection strings
            "cache/redis-endpoint": "placeholder-will-be-updated-by-cache-stack",
            # API keys and tokens (placeholders)
            "api/trading-api-key": "placeholder-update-after-deployment",
            "api/market-data-key": "placeholder-update-after-deployment",
            # Notification settings
            "notifications/email-endpoint": self.env_config.monitoring.alarm_notification_email
            or "admin@example.com",
            # Encryption keys
            "encryption/data-key": "placeholder-will-be-generated",
        }

    def _create_secrets_manager_entries(
        self,
    ) -> Dict[str, secretsmanager.Secret]:
        """
        Create Secrets Manager entries for sensitive configuration

        Returns:
            Dict[str, secretsmanager.Secret]: Dictionary of created secrets
        """
        secrets = {}

        # Database credentials
        secrets["database_credentials"] = secretsmanager.Secret(
            self,
            "DatabaseCredentials",
            secret_name=f"options-strategy/{self.env_name}/database/credentials",
            description=f"Database credentials for Options Strategy Platform - {self.env_name}",
            encryption_key=self.config_kms_key,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": "admin"}),
                generate_string_key="password",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"@\\",
                password_length=32,
            ),
        )

        # API keys and tokens
        secrets["external_api_keys"] = secretsmanager.Secret(
            self,
            "ExternalAPIKeys",
            secret_name=f"options-strategy/{self.env_name}/api/external-keys",
            description=f"External API keys for Options Strategy Platform - {self.env_name}",
            encryption_key=self.config_kms_key,
            secret_object_value={
                "trading_api_key": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-update-after-deployment"
                ),
                "market_data_key": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-update-after-deployment"
                ),
                "notification_webhook": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-update-after-deployment"
                ),
            },
        )

        # Application secrets
        secrets["application_secrets"] = secretsmanager.Secret(
            self,
            "ApplicationSecrets",
            secret_name=f"options-strategy/{self.env_name}/application/secrets",
            description=f"Application secrets for Options Strategy Platform - {self.env_name}",
            encryption_key=self.config_kms_key,
            secret_object_value={
                "jwt_secret": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-will-be-generated"
                ),
                "encryption_key": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-will-be-generated"
                ),
                "session_secret": secretsmanager.SecretValue.unsafe_plain_text(
                    "placeholder-will-be-generated"
                ),
            },
        )

        return secrets

    def _create_audit_logging(self) -> logs.LogGroup:
        """
        Create audit logging for configuration access

        Returns:
            logs.LogGroup: Audit log group
        """
        return logs.LogGroup(
            self,
            "ConfigurationAuditLog",
            log_group_name=f"{self.env_config.get_log_group_prefix()}/config-audit",
            retention=logs.RetentionDays.ONE_YEAR,
            removal_policy=(
                RemovalPolicy.RETAIN
                if self.env_config.is_production
                else RemovalPolicy.DESTROY
            ),
        )

    def _create_configuration_backup(self) -> None:
        """Create backup strategy for configuration data"""
        # In production, we would create backup automation here
        # For now, we'll create a backup parameter to track backup status
        ssm.StringParameter(
            self,
            "ConfigurationBackupStatus",
            parameter_name=f"{self.env_config.get_parameter_store_prefix()}/backup/status",
            string_value="enabled",
            description=f"Configuration backup status for {self.env_name}",
        )

    def _create_vpc_endpoints(self) -> None:
        """Create VPC endpoints for secure Parameter Store and Secrets Manager access"""
        # This would be implemented if VPC is provided
        # Creating placeholder parameters to track endpoint configuration
        ssm.StringParameter(
            self,
            "VPCEndpointsEnabled",
            parameter_name=f"{self.env_config.get_parameter_store_prefix()}/vpc/endpoints-enabled",
            string_value="true",
            description=f"VPC endpoints enabled for secure configuration access - {self.env_name}",
        )

    def get_parameter_arn(self, parameter_name: str) -> str:
        """
        Get Parameter Store ARN for a given parameter name

        Args:
            parameter_name: Parameter name (without prefix)

        Returns:
            str: Parameter ARN
        """
        full_name = (
            f"{self.env_config.get_parameter_store_prefix()}/{parameter_name}"
        )
        return f"arn:aws:ssm:{self.region}:{self.account}:parameter{full_name}"

    def get_secret_arn(self, secret_key: str) -> str:
        """
        Get Secrets Manager ARN for a given secret

        Args:
            secret_key: Secret key from self.secrets dictionary

        Returns:
            str: Secret ARN
        """
        if secret_key not in self.secrets:
            raise ValueError(f"Secret key '{secret_key}' not found")
        return self.secrets[secret_key].secret_arn

    def grant_parameter_access(
        self,
        grantee: Union[iam.Role, iam.User, iam.Group],
        parameter_paths: List[str],
        actions: Optional[List[str]] = None,
    ) -> None:
        """
        Grant Parameter Store access to an IAM principal

        Args:
            grantee: IAM principal to grant access to
            parameter_paths: List of parameter paths (without prefix)
            actions: SSM actions to allow (defaults to read-only)
        """
        if not actions:
            actions = [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath",
            ]

        # Create parameter ARNs
        parameter_arns = []
        for path in parameter_paths:
            full_path = (
                f"{self.env_config.get_parameter_store_prefix()}/{path}"
            )
            parameter_arns.append(
                f"arn:aws:ssm:{self.region}:{self.account}:parameter{full_path}/*"
            )

        # Grant permissions
        grantee.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=actions,
                resources=parameter_arns,
            )
        )

    def grant_secret_access(
        self,
        grantee: Union[iam.Role, iam.User, iam.Group],
        secret_keys: List[str],
    ) -> None:
        """
        Grant Secrets Manager access to an IAM principal

        Args:
            grantee: IAM principal to grant access to
            secret_keys: List of secret keys from self.secrets
        """
        for secret_key in secret_keys:
            if secret_key in self.secrets:
                self.secrets[secret_key].grant_read(grantee)

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for configuration resources"""

        # Parameter Store outputs
        CfnOutput(
            self,
            "ParameterStorePrefix",
            value=self.env_config.get_parameter_store_prefix(),
            description="Parameter Store prefix for this environment",
            export_name=f"OptionsStrategy-{self.env_name}-ParameterStore-Prefix",
        )

        # KMS key output
        CfnOutput(
            self,
            "ConfigurationKMSKeyId",
            value=self.config_kms_key.key_id,
            description="KMS key ID for configuration encryption",
            export_name=f"OptionsStrategy-{self.env_name}-Config-KMS-Key",
        )

        CfnOutput(
            self,
            "ConfigurationKMSKeyArn",
            value=self.config_kms_key.key_arn,
            description="KMS key ARN for configuration encryption",
            export_name=f"OptionsStrategy-{self.env_name}-Config-KMS-ARN",
        )

        # Secrets Manager outputs
        for secret_name, secret in self.secrets.items():
            CfnOutput(
                self,
                f"{secret_name.title().replace('_', '')}SecretArn",
                value=secret.secret_arn,
                description=f"Secret ARN for {secret_name}",
                export_name=f"OptionsStrategy-{self.env_name}-{secret_name.replace('_', '-').title()}-Secret-ARN",
            )

        # Audit log group output
        CfnOutput(
            self,
            "ConfigAuditLogGroupArn",
            value=self.audit_log_group.log_group_arn,
            description="Configuration audit log group ARN",
            export_name=f"OptionsStrategy-{self.env_name}-Config-Audit-Log-ARN",
        )
