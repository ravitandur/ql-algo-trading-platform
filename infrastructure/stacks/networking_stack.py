"""
Networking Stack for Options Strategy Lifecycle Platform

This module defines the networking infrastructure stack including VPC,
subnets, routing, and network-related resources for the Options Strategy
Lifecycle Platform.

The stack creates:
- VPC with configurable CIDR blocks
- Public and private subnets across multiple availability zones
- Internet Gateway and NAT Gateways
- Route tables and routing configuration
- VPC Flow Logs for security monitoring
- DNS and DHCP configuration

Designed for deployment in ap-south-1 (Asia Pacific - Mumbai) region
to comply with Indian market data residency requirements.
"""

from typing import Dict, List, Optional
from aws_cdk import (
    Stack,
    StackProps,
    CfnOutput,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_ssm as ssm,
)
from constructs import Construct
from ..constructs.vpc_construct import OptionsStrategyVPC


class NetworkingStack(Stack):
    """
    Networking Stack for Options Strategy Lifecycle Platform
    
    This stack creates the foundational networking infrastructure including:
    - VPC with public, private application, and private database subnets
    - Internet Gateway and NAT Gateways for outbound connectivity
    - VPC Flow Logs for network traffic monitoring
    - Parameter Store entries for network resource references
    - CloudFormation outputs for cross-stack dependencies
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
        **kwargs
    ) -> None:
        """
        Initialize the Networking Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            vpc_cidr: CIDR block for the VPC
            max_azs: Maximum number of availability zones to use
            enable_nat_gateway: Whether to create NAT gateways
            enable_dns_hostnames: Whether to enable DNS hostnames
            enable_dns_support: Whether to enable DNS support
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.vpc_cidr = vpc_cidr
        self.max_azs = max_azs
        
        # Create the VPC using the reusable construct
        self.vpc_construct = OptionsStrategyVPC(
            self,
            "OptionsStrategyVPC",
            env_name=env_name,
            vpc_cidr=vpc_cidr,
            max_azs=max_azs,
            enable_nat_gateway=enable_nat_gateway,
            enable_dns_hostnames=enable_dns_hostnames,
            enable_dns_support=enable_dns_support,
        )
        
        # Create VPC Flow Logs for security monitoring
        self._create_vpc_flow_logs()
        
        # Create Parameter Store entries for network resources
        self._create_parameter_store_entries()
        
        # Create CloudFormation outputs
        self._create_stack_outputs()

    def _create_vpc_flow_logs(self) -> None:
        """Create VPC Flow Logs for network traffic monitoring"""
        
        # Create IAM role for VPC Flow Logs
        flow_log_role = iam.Role(
            self,
            "VPCFlowLogRole",
            role_name=f"options-strategy-vpc-flowlog-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/VPCFlowLogsDeliveryRolePolicy"
                )
            ],
        )
        
        # Create CloudWatch Log Group for VPC Flow Logs
        flow_log_group = logs.LogGroup(
            self,
            "VPCFlowLogGroup",
            log_group_name=f"/aws/vpc/flowlogs/options-strategy-{self.env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # Create VPC Flow Log
        self.vpc_flow_log = ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                flow_log_group, flow_log_role
            ),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

    def _create_parameter_store_entries(self) -> None:
        """Create Parameter Store entries for network resource references"""
        
        # VPC information
        ssm.StringParameter(
            self,
            "VPCIdParameter",
            parameter_name=f"/options-strategy/{self.env_name}/networking/vpc-id",
            string_value=self.vpc.vpc_id,
            description=f"VPC ID for Options Strategy Platform {self.env_name} environment",
        )
        
        ssm.StringParameter(
            self,
            "VPCCidrParameter",
            parameter_name=f"/options-strategy/{self.env_name}/networking/vpc-cidr",
            string_value=self.vpc_cidr,
            description=f"VPC CIDR block for Options Strategy Platform {self.env_name} environment",
        )
        
        # Subnet information
        ssm.StringParameter(
            self,
            "PublicSubnetIdsParameter",
            parameter_name=f"/options-strategy/{self.env_name}/networking/public-subnet-ids",
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description=f"Public subnet IDs for Options Strategy Platform {self.env_name} environment",
        )
        
        ssm.StringParameter(
            self,
            "PrivateSubnetIdsParameter", 
            parameter_name=f"/options-strategy/{self.env_name}/networking/private-subnet-ids",
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description=f"Private subnet IDs for Options Strategy Platform {self.env_name} environment",
        )
        
        ssm.StringParameter(
            self,
            "IsolatedSubnetIdsParameter",
            parameter_name=f"/options-strategy/{self.env_name}/networking/isolated-subnet-ids", 
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            description=f"Isolated subnet IDs for Options Strategy Platform {self.env_name} environment",
        )
        
        # Availability Zones
        ssm.StringParameter(
            self,
            "AvailabilityZonesParameter",
            parameter_name=f"/options-strategy/{self.env_name}/networking/availability-zones",
            string_value=",".join(self.vpc.availability_zones),
            description=f"Availability zones for Options Strategy Platform {self.env_name} environment",
        )

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack dependencies"""
        
        CfnOutput(
            self,
            "VPCId",
            value=self.vpc.vpc_id,
            description="ID of the Options Strategy Platform VPC",
            export_name=f"OptionsStrategy-{self.env_name}-Networking-VPC-ID",
        )
        
        CfnOutput(
            self,
            "VPCCidr",
            value=self.vpc_cidr,
            description="CIDR block of the Options Strategy Platform VPC", 
            export_name=f"OptionsStrategy-{self.env_name}-Networking-VPC-CIDR",
        )
        
        CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="IDs of the public subnets",
            export_name=f"OptionsStrategy-{self.env_name}-Networking-Public-Subnet-IDs",
        )
        
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="IDs of the private subnets",
            export_name=f"OptionsStrategy-{self.env_name}-Networking-Private-Subnet-IDs",
        )
        
        CfnOutput(
            self,
            "IsolatedSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            description="IDs of the isolated subnets",
            export_name=f"OptionsStrategy-{self.env_name}-Networking-Isolated-Subnet-IDs",
        )
        
        CfnOutput(
            self,
            "AvailabilityZones",
            value=",".join(self.vpc.availability_zones),
            description="Availability zones used by the VPC",
            export_name=f"OptionsStrategy-{self.env_name}-Networking-AZs",
        )

    @property
    def public_subnets(self) -> List[ec2.ISubnet]:
        """Get public subnets from the VPC"""
        return self.vpc.public_subnets
    
    @property
    def private_subnets(self) -> List[ec2.ISubnet]:
        """Get private subnets from the VPC"""
        return self.vpc.private_subnets
    
    @property
    def isolated_subnets(self) -> List[ec2.ISubnet]:
        """Get isolated subnets from the VPC"""
        return self.vpc.isolated_subnets
    
    @property
    def availability_zones(self) -> List[str]:
        """Get availability zones used by the VPC"""
        return self.vpc.availability_zones
    
    @property
    def vpc(self) -> ec2.Vpc:
        """Get VPC from the construct"""
        return self.vpc_construct.vpc