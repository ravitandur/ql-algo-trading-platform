"""
Environment Configuration for Options Strategy Lifecycle Platform

This module provides environment-specific configuration settings for the
Options Strategy Lifecycle Platform, including AWS resources, networking,
security, and operational parameters for different deployment environments.

The configuration is designed for deployment in ap-south-1 (Asia Pacific - Mumbai)
region to comply with Indian market data residency requirements.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Supported deployment environments"""
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass
class NetworkingConfig:
    """Networking configuration for environment"""
    vpc_cidr: str
    max_azs: int
    enable_nat_gateway: bool
    enable_dns_hostnames: bool = True
    enable_dns_support: bool = True
    enable_flow_logs: bool = True


@dataclass
class SecurityConfig:
    """Security configuration for environment"""
    enable_waf: bool
    enable_shield: bool
    enable_strict_nacls: bool
    enable_vpc_endpoints: bool
    enable_encryption_at_rest: bool = True
    enable_encryption_in_transit: bool = True
    kms_key_rotation: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_retention_days: int
    enable_detailed_monitoring: bool
    enable_xray_tracing: bool
    enable_enhanced_monitoring: bool
    alarm_notification_email: Optional[str] = None
    enable_cost_alerts: bool = True


@dataclass
class ResourceConfig:
    """Resource sizing and scaling configuration"""
    lambda_memory_size: int
    lambda_timeout: int
    ecs_cpu: int
    ecs_memory: int
    rds_instance_class: str
    rds_allocated_storage: int
    elasticache_node_type: str


@dataclass
class ComplianceConfig:
    """Compliance and regulatory settings"""
    data_residency_region: str
    enable_audit_logging: bool
    backup_retention_days: int
    enable_cross_region_backup: bool
    enable_point_in_time_recovery: bool = True
    enable_deletion_protection: bool = False


@dataclass
class CostOptimizationConfig:
    """Cost optimization settings"""
    enable_spot_instances: bool
    enable_scheduled_scaling: bool
    enable_lifecycle_policies: bool
    enable_resource_right_sizing: bool
    backup_lifecycle_transition_days: int = 30


@dataclass
class EnvironmentConfig:
    """Complete environment configuration"""
    env_name: str
    aws_account: Optional[str]
    aws_region: str
    
    # Configuration sections
    networking: NetworkingConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    resources: ResourceConfig
    compliance: ComplianceConfig
    cost_optimization: CostOptimizationConfig
    
    # Tags applied to all resources
    resource_tags: Dict[str, str] = field(default_factory=dict)
    
    # Feature flags
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Custom parameters for Parameter Store
    custom_parameters: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization setup"""
        # Set default resource tags
        if not self.resource_tags:
            self.resource_tags = {
                "Project": "OptionsStrategyPlatform",
                "Environment": self.env_name,
                "Owner": "platform-team",
                "CostCenter": "trading-systems",
                "DataResidency": "india",
                "ManagedBy": "CDK",
                "Region": self.aws_region,
            }
        
        # Set default feature flags
        if not self.feature_flags:
            self.feature_flags = {
                "enable_api_caching": self.env_name in ["staging", "prod"],
                "enable_multi_az": self.env_name == "prod",
                "enable_auto_scaling": self.env_name in ["staging", "prod"],
                "enable_blue_green_deployment": self.env_name == "prod",
                "enable_canary_deployment": self.env_name == "prod",
                "enable_circuit_breaker": True,
                "enable_rate_limiting": True,
            }

    @property
    def is_production(self) -> bool:
        """Check if this is a production environment"""
        return self.env_name == "prod"

    @property
    def is_development(self) -> bool:
        """Check if this is a development environment"""
        return self.env_name == "dev"

    @property
    def stack_name(self) -> str:
        """Get standardized stack name"""
        return f"OptionsStrategyPlatform-{self.env_name.title()}"

    @property
    def resource_prefix(self) -> str:
        """Get standardized resource prefix"""
        return f"options-strategy-{self.env_name}"

    def get_parameter_store_prefix(self) -> str:
        """Get Parameter Store path prefix"""
        return f"/options-strategy/{self.env_name}"

    def get_log_group_prefix(self) -> str:
        """Get CloudWatch log group prefix"""
        return f"/aws/options-strategy/{self.env_name}"


def _get_dev_config() -> EnvironmentConfig:
    """Get development environment configuration"""
    return EnvironmentConfig(
        env_name="dev",
        aws_account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        aws_region="ap-south-1",
        networking=NetworkingConfig(
            vpc_cidr="10.0.0.0/16",
            max_azs=2,
            enable_nat_gateway=True,  # Single NAT for cost optimization
        ),
        security=SecurityConfig(
            enable_waf=False,
            enable_shield=False,
            enable_strict_nacls=False,
            enable_vpc_endpoints=False,
        ),
        monitoring=MonitoringConfig(
            log_retention_days=7,
            enable_detailed_monitoring=False,
            enable_xray_tracing=True,
            enable_enhanced_monitoring=False,
            alarm_notification_email=os.environ.get("DEV_NOTIFICATION_EMAIL"),
        ),
        resources=ResourceConfig(
            lambda_memory_size=512,
            lambda_timeout=30,
            ecs_cpu=256,
            ecs_memory=512,
            rds_instance_class="db.t3.micro",
            rds_allocated_storage=20,
            elasticache_node_type="cache.t3.micro",
        ),
        compliance=ComplianceConfig(
            data_residency_region="ap-south-1",
            enable_audit_logging=True,
            backup_retention_days=7,
            enable_cross_region_backup=False,
            enable_deletion_protection=False,
        ),
        cost_optimization=CostOptimizationConfig(
            enable_spot_instances=True,
            enable_scheduled_scaling=False,
            enable_lifecycle_policies=True,
            enable_resource_right_sizing=False,
        ),
        custom_parameters={
            "debug_mode": "true",
            "log_level": "DEBUG",
            "enable_test_data": "true",
        },
    )


def _get_staging_config() -> EnvironmentConfig:
    """Get staging environment configuration"""
    return EnvironmentConfig(
        env_name="staging",
        aws_account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        aws_region="ap-south-1",
        networking=NetworkingConfig(
            vpc_cidr="10.1.0.0/16",
            max_azs=2,
            enable_nat_gateway=True,
        ),
        security=SecurityConfig(
            enable_waf=True,
            enable_shield=False,
            enable_strict_nacls=True,
            enable_vpc_endpoints=True,
        ),
        monitoring=MonitoringConfig(
            log_retention_days=30,
            enable_detailed_monitoring=True,
            enable_xray_tracing=True,
            enable_enhanced_monitoring=True,
            alarm_notification_email=os.environ.get("STAGING_NOTIFICATION_EMAIL"),
        ),
        resources=ResourceConfig(
            lambda_memory_size=1024,
            lambda_timeout=60,
            ecs_cpu=512,
            ecs_memory=1024,
            rds_instance_class="db.t3.small",
            rds_allocated_storage=50,
            elasticache_node_type="cache.t3.small",
        ),
        compliance=ComplianceConfig(
            data_residency_region="ap-south-1",
            enable_audit_logging=True,
            backup_retention_days=30,
            enable_cross_region_backup=True,
            enable_deletion_protection=True,
        ),
        cost_optimization=CostOptimizationConfig(
            enable_spot_instances=False,
            enable_scheduled_scaling=True,
            enable_lifecycle_policies=True,
            enable_resource_right_sizing=True,
        ),
        custom_parameters={
            "debug_mode": "false",
            "log_level": "INFO",
            "enable_test_data": "false",
            "cache_ttl": "3600",
        },
    )


def _get_prod_config() -> EnvironmentConfig:
    """Get production environment configuration"""
    return EnvironmentConfig(
        env_name="prod",
        aws_account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        aws_region="ap-south-1",
        networking=NetworkingConfig(
            vpc_cidr="10.2.0.0/16",
            max_azs=3,  # High availability
            enable_nat_gateway=True,
        ),
        security=SecurityConfig(
            enable_waf=True,
            enable_shield=True,
            enable_strict_nacls=True,
            enable_vpc_endpoints=True,
        ),
        monitoring=MonitoringConfig(
            log_retention_days=90,
            enable_detailed_monitoring=True,
            enable_xray_tracing=True,
            enable_enhanced_monitoring=True,
            alarm_notification_email=os.environ.get("PROD_NOTIFICATION_EMAIL"),
        ),
        resources=ResourceConfig(
            lambda_memory_size=2048,
            lambda_timeout=300,
            ecs_cpu=2048,
            ecs_memory=4096,
            rds_instance_class="db.r5.large",
            rds_allocated_storage=200,
            elasticache_node_type="cache.r5.large",
        ),
        compliance=ComplianceConfig(
            data_residency_region="ap-south-1",
            enable_audit_logging=True,
            backup_retention_days=90,
            enable_cross_region_backup=True,
            enable_deletion_protection=True,
        ),
        cost_optimization=CostOptimizationConfig(
            enable_spot_instances=False,
            enable_scheduled_scaling=True,
            enable_lifecycle_policies=True,
            enable_resource_right_sizing=True,
        ),
        custom_parameters={
            "debug_mode": "false",
            "log_level": "WARN",
            "enable_test_data": "false",
            "cache_ttl": "7200",
            "max_retry_attempts": "3",
            "circuit_breaker_threshold": "50",
        },
    )


# Environment configuration registry
_ENVIRONMENT_CONFIGS = {
    Environment.DEV.value: _get_dev_config,
    Environment.STAGING.value: _get_staging_config,
    Environment.PROD.value: _get_prod_config,
}


def get_environment_config(env_name: Optional[str] = None) -> EnvironmentConfig:
    """
    Get configuration for specified environment
    
    Args:
        env_name: Environment name (dev, staging, prod). 
                 If None, reads from CDK_ENVIRONMENT environment variable,
                 defaults to 'dev'
    
    Returns:
        EnvironmentConfig: Configuration for the specified environment
        
    Raises:
        ValueError: If environment name is not supported
    """
    if env_name is None:
        env_name = os.environ.get("CDK_ENVIRONMENT", "dev")
    
    if env_name not in _ENVIRONMENT_CONFIGS:
        supported_envs = list(_ENVIRONMENT_CONFIGS.keys())
        raise ValueError(
            f"Unsupported environment: {env_name}. "
            f"Supported environments: {supported_envs}"
        )
    
    return _ENVIRONMENT_CONFIGS[env_name]()


def get_all_environments() -> List[str]:
    """Get list of all supported environments"""
    return list(_ENVIRONMENT_CONFIGS.keys())


def validate_environment_config(config: EnvironmentConfig) -> List[str]:
    """
    Validate environment configuration and return any issues
    
    Args:
        config: Environment configuration to validate
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate AWS region for Indian market compliance
    if config.aws_region != "ap-south-1":
        errors.append(
            f"AWS region must be ap-south-1 for Indian market compliance, "
            f"got: {config.aws_region}"
        )
    
    # Validate VPC CIDR
    if not config.networking.vpc_cidr.endswith('/16'):
        errors.append(
            f"VPC CIDR should use /16 subnet for proper IP allocation, "
            f"got: {config.networking.vpc_cidr}"
        )
    
    # Validate production settings
    if config.is_production:
        if config.networking.max_azs < 3:
            errors.append("Production environment should use at least 3 AZs for HA")
        
        if not config.security.enable_waf:
            errors.append("Production environment should enable WAF")
        
        if not config.compliance.enable_deletion_protection:
            errors.append("Production environment should enable deletion protection")
        
        if config.monitoring.log_retention_days < 90:
            errors.append("Production environment should retain logs for at least 90 days")
    
    # Validate resource sizing
    if config.env_name == "prod" and config.resources.lambda_memory_size < 1024:
        errors.append("Production Lambda functions should have at least 1024MB memory")
    
    return errors