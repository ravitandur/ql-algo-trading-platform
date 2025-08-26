"""
VPC Construct for Options Strategy Lifecycle Platform

This module provides a reusable VPC construct that encapsulates the
VPC configuration and best practices for the Options Strategy Lifecycle Platform.

The construct creates:
- VPC with configurable CIDR blocks and AZ configuration
- Multi-tier subnet architecture (public, private app, private DB)
- Internet Gateway and NAT Gateways for connectivity
- Proper route table configuration
- DNS and DHCP options for service discovery

Features:
- Multi-environment support with different configurations
- Cost optimization for non-production environments
- Security-first design with isolated database subnets
- Indian market data residency compliance (ap-south-1 region)
"""

from typing import Optional, List
from aws_cdk import (
    aws_ec2 as ec2,
    Tags,
)
from constructs import Construct


class OptionsStrategyVPC(Construct):
    """
    Reusable VPC Construct for Options Strategy Lifecycle Platform
    
    This construct creates a well-architected VPC with:
    - Public subnets for load balancers and bastion hosts
    - Private subnets with NAT Gateway access for application services
    - Isolated subnets for databases and sensitive services
    - Proper DNS configuration for service discovery
    - Multi-AZ deployment for high availability
    
    The VPC is designed to support:
    - Web applications and APIs
    - Containerized microservices
    - Database services (RDS, ElastiCache)
    - Lambda functions
    - Data processing workloads
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        vpc_cidr: str = "10.0.0.0/16",
        max_azs: int = 2,
        enable_nat_gateway: bool = True,
        enable_dns_hostnames: bool = True,
        enable_dns_support: bool = True,
        nat_gateways: Optional[int] = None,
    ) -> None:
        """
        Initialize the VPC Construct
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            vpc_cidr: CIDR block for the VPC
            max_azs: Maximum number of availability zones to use
            enable_nat_gateway: Whether to create NAT gateways
            enable_dns_hostnames: Whether to enable DNS hostnames
            enable_dns_support: Whether to enable DNS support
            nat_gateways: Number of NAT gateways (defaults to max_azs if None)
        """
        super().__init__(scope, construct_id)
        
        self.env_name = env_name
        self.vpc_cidr = vpc_cidr
        self.max_azs = max_azs
        
        # Determine NAT Gateway configuration based on environment
        if nat_gateways is None:
            # Cost optimization: dev uses single NAT gateway, prod uses one per AZ
            nat_gateways = 1 if env_name == "dev" else max_azs
        
        # Create the VPC with multi-tier subnet architecture
        self.vpc = self._create_vpc(
            vpc_cidr=vpc_cidr,
            max_azs=max_azs,
            nat_gateways=nat_gateways,
            enable_nat_gateway=enable_nat_gateway,
            enable_dns_hostnames=enable_dns_hostnames,
            enable_dns_support=enable_dns_support,
        )
        
        # Apply environment-specific tags
        self._apply_vpc_tags()

    def _create_vpc(
        self,
        vpc_cidr: str,
        max_azs: int,
        nat_gateways: int,
        enable_nat_gateway: bool,
        enable_dns_hostnames: bool,
        enable_dns_support: bool,
    ) -> ec2.Vpc:
        """
        Create the VPC with multi-tier subnet configuration
        
        Args:
            vpc_cidr: CIDR block for the VPC
            max_azs: Maximum number of availability zones
            nat_gateways: Number of NAT gateways to create
            enable_nat_gateway: Whether to enable NAT gateways
            enable_dns_hostnames: Whether to enable DNS hostnames
            enable_dns_support: Whether to enable DNS support
            
        Returns:
            ec2.Vpc: The created VPC
        """
        
        # Define subnet configuration for three-tier architecture
        subnet_configuration = [
            # Public subnets for load balancers, bastion hosts, NAT gateways
            ec2.SubnetConfiguration(
                name=f"public-{self.env_name}",
                subnet_type=ec2.SubnetType.PUBLIC,
                cidr_mask=24,  # /24 allows ~250 IPs per subnet
            ),
            # Private subnets with egress for application services
            ec2.SubnetConfiguration(
                name=f"private-app-{self.env_name}",
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                cidr_mask=22,  # /22 allows ~1000 IPs per subnet
            ),
            # Isolated subnets for databases and sensitive services
            ec2.SubnetConfiguration(
                name=f"private-db-{self.env_name}",
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                cidr_mask=24,  # /24 is sufficient for database instances
            ),
        ]
        
        # Create the VPC
        vpc = ec2.Vpc(
            self,
            "VPC",
            vpc_name=f"options-strategy-vpc-{self.env_name}",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=max_azs,
            subnet_configuration=subnet_configuration,
            enable_dns_hostnames=enable_dns_hostnames,
            enable_dns_support=enable_dns_support,
            nat_gateways=nat_gateways if enable_nat_gateway else 0,
            # Create one internet gateway per VPC
            nat_gateway_provider=ec2.NatProvider.gateway(),
        )
        
        return vpc

    def _apply_vpc_tags(self) -> None:
        """Apply environment-specific and compliance tags to the VPC"""
        
        # Standard tags for the VPC
        tags_config = {
            "Name": f"options-strategy-vpc-{self.env_name}",
            "Environment": self.env_name,
            "Project": "OptionsStrategyPlatform",
            "Component": "Networking",
            "DataResidency": "india",
            "Compliance": "indian-market-data",
            "CostCenter": "trading-systems",
            "Owner": "platform-team",
            "ManagedBy": "CDK",
            "Region": "ap-south-1",
        }
        
        # Apply tags to the VPC and all its resources
        for key, value in tags_config.items():
            Tags.of(self.vpc).add(key, value)
        
        # Environment-specific tags
        if self.env_name == "prod":
            Tags.of(self.vpc).add("Criticality", "High")
            Tags.of(self.vpc).add("BackupRequired", "True")
        elif self.env_name == "staging":
            Tags.of(self.vpc).add("Criticality", "Medium")
            Tags.of(self.vpc).add("BackupRequired", "False")
        else:  # dev
            Tags.of(self.vpc).add("Criticality", "Low")
            Tags.of(self.vpc).add("BackupRequired", "False")
            Tags.of(self.vpc).add("AutoShutdown", "True")

    def get_subnet_by_type(self, subnet_type: str) -> List[ec2.ISubnet]:
        """
        Get subnets by type
        
        Args:
            subnet_type: Type of subnet ('public', 'private', 'isolated')
            
        Returns:
            List[ec2.ISubnet]: List of subnets of the specified type
        """
        if subnet_type.lower() == "public":
            return self.vpc.public_subnets
        elif subnet_type.lower() == "private":
            return self.vpc.private_subnets
        elif subnet_type.lower() == "isolated":
            return self.vpc.isolated_subnets
        else:
            raise ValueError(f"Invalid subnet type: {subnet_type}. Use 'public', 'private', or 'isolated'")

    def get_subnet_ids_by_type(self, subnet_type: str) -> List[str]:
        """
        Get subnet IDs by type
        
        Args:
            subnet_type: Type of subnet ('public', 'private', 'isolated')
            
        Returns:
            List[str]: List of subnet IDs of the specified type
        """
        subnets = self.get_subnet_by_type(subnet_type)
        return [subnet.subnet_id for subnet in subnets]

    @property
    def vpc_id(self) -> str:
        """Get the VPC ID"""
        return self.vpc.vpc_id

    @property
    def vpc_cidr_block(self) -> str:
        """Get the VPC CIDR block"""
        return self.vpc_cidr

    @property
    def public_subnets(self) -> List[ec2.ISubnet]:
        """Get public subnets"""
        return self.vpc.public_subnets

    @property
    def private_subnets(self) -> List[ec2.ISubnet]:
        """Get private subnets"""
        return self.vpc.private_subnets

    @property
    def isolated_subnets(self) -> List[ec2.ISubnet]:
        """Get isolated subnets"""
        return self.vpc.isolated_subnets

    @property
    def availability_zones(self) -> List[str]:
        """Get availability zones used by the VPC"""
        return self.vpc.availability_zones

    @property
    def internet_gateway_id(self) -> Optional[str]:
        """Get the Internet Gateway ID if available"""
        # The IGW ID is not directly exposed by CDK VPC construct
        # This would need to be retrieved via CloudFormation outputs if needed
        return None

    def __repr__(self) -> str:
        return f"OptionsStrategyVPC(env_name='{self.env_name}', vpc_cidr='{self.vpc_cidr}', max_azs={self.max_azs})"