"""
Security Stack for Options Strategy Lifecycle Platform

This module defines the security infrastructure including security groups,
NACLs, and security-related configurations for the Options Strategy
Lifecycle Platform.

The stack creates:
- Security groups for different service tiers (ALB, app, database, cache)
- Network ACLs for additional network-level security
- Security group rules following principle of least privilege
- Parameter Store entries for security group references
- CloudFormation outputs for cross-stack dependencies

Security Architecture:
- Layered security with both security groups and NACLs
- Principle of least privilege for all access rules
- Environment-specific security configurations
- Compliance with Indian market data security requirements
"""

from typing import Dict, List, Optional
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ssm as ssm,
)
from constructs import Construct


class SecurityStack(Stack):
    """
    Security Stack for Options Strategy Lifecycle Platform

    This stack creates security groups and network ACLs for the platform:
    - Application Load Balancer security group
    - Application services security group
    - Database services security group
    - Cache services security group
    - Management/bastion security group
    - Network ACLs for additional protection
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        env_name: str = "dev",
        enable_strict_nacls: bool = False,
        allowed_cidr_blocks: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Security Stack

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            vpc: The VPC to create security groups in
            env_name: Environment name (dev, staging, prod)
            enable_strict_nacls: Whether to enable strict NACLs
            allowed_cidr_blocks: Additional CIDR blocks to allow access from
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.env_name = env_name
        self.allowed_cidr_blocks = allowed_cidr_blocks or []

        # Create security groups for different service tiers
        self.security_groups = self._create_security_groups()

        # Create Network ACLs if enabled
        if enable_strict_nacls:
            self.network_acls = self._create_network_acls()

        # Create Parameter Store entries
        self._create_parameter_store_entries()

        # Create CloudFormation outputs
        self._create_stack_outputs()

    def _create_security_groups(self) -> Dict[str, ec2.SecurityGroup]:
        """
        Create security groups for different service layers

        Returns:
            Dict[str, ec2.SecurityGroup]: Dictionary of created security groups
        """
        security_groups = {}

        # Application Load Balancer Security Group
        security_groups["alb"] = self._create_alb_security_group()

        # Application Services Security Group
        security_groups["app"] = self._create_app_security_group(
            security_groups["alb"]
        )

        # Database Services Security Group
        security_groups["db"] = self._create_database_security_group(
            security_groups["app"]
        )

        # Cache Services Security Group
        security_groups["cache"] = self._create_cache_security_group(
            security_groups["app"]
        )

        # Management/Bastion Security Group
        security_groups["management"] = (
            self._create_management_security_group()
        )

        # Internal Services Security Group (for service-to-service communication)
        security_groups["internal"] = self._create_internal_security_group()

        return security_groups

    def _create_alb_security_group(self) -> ec2.SecurityGroup:
        """Create security group for Application Load Balancer"""

        alb_sg = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            security_group_name=f"options-strategy-alb-sg-{self.env_name}",
            allow_all_outbound=False,  # Explicit outbound rules
        )

        # Inbound rules - Allow HTTP and HTTPS from internet
        alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS traffic from internet",
        )

        alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP traffic from internet (redirect to HTTPS)",
        )

        # Allow additional CIDR blocks if specified
        for cidr in self.allowed_cidr_blocks:
            alb_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(cidr),
                connection=ec2.Port.tcp(443),
                description=f"HTTPS traffic from {cidr}",
            )

        return alb_sg

    def _create_app_security_group(
        self, alb_sg: ec2.SecurityGroup
    ) -> ec2.SecurityGroup:
        """Create security group for application services"""

        app_sg = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=self.vpc,
            description="Security group for application services",
            security_group_name=f"options-strategy-app-sg-{self.env_name}",
            allow_all_outbound=False,  # Explicit outbound rules
        )

        # Inbound rules - Allow traffic from ALB
        app_sg.add_ingress_rule(
            peer=alb_sg,
            connection=ec2.Port.tcp(8080),
            description="HTTP traffic from ALB to application",
        )

        app_sg.add_ingress_rule(
            peer=alb_sg,
            connection=ec2.Port.tcp(8443),
            description="HTTPS traffic from ALB to application",
        )

        # Allow health check from ALB
        app_sg.add_ingress_rule(
            peer=alb_sg,
            connection=ec2.Port.tcp(8081),
            description="Health check from ALB",
        )

        # Allow inter-app communication
        app_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.all_tcp(),
            description="Inter-application communication",
        )

        # Outbound rules - Allow HTTPS for external API calls
        app_sg.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS for external API calls",
        )

        # Allow DNS resolution
        app_sg.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(53),
            description="DNS TCP queries",
        )

        app_sg.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.udp(53),
            description="DNS UDP queries",
        )

        return app_sg

    def _create_database_security_group(
        self, app_sg: ec2.SecurityGroup
    ) -> ec2.SecurityGroup:
        """Create security group for database services"""

        db_sg = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for database services",
            security_group_name=f"options-strategy-db-sg-{self.env_name}",
            allow_all_outbound=False,  # Explicit outbound rules
        )

        # Inbound rules - Allow database connections from app tier
        db_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL access from application",
        )

        db_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.tcp(6379),
            description="Redis access from application",
        )

        db_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.tcp(3306),
            description="MySQL access from application (if needed)",
        )

        # Allow database replication between instances
        db_sg.add_ingress_rule(
            peer=db_sg,
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL replication",
        )

        # No outbound rules needed for databases in isolated subnets

        return db_sg

    def _create_cache_security_group(
        self, app_sg: ec2.SecurityGroup
    ) -> ec2.SecurityGroup:
        """Create security group for caching services"""

        cache_sg = ec2.SecurityGroup(
            self,
            "CacheSecurityGroup",
            vpc=self.vpc,
            description="Security group for caching services",
            security_group_name=f"options-strategy-cache-sg-{self.env_name}",
            allow_all_outbound=False,  # Explicit outbound rules
        )

        # Inbound rules - Allow cache connections from app tier
        cache_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.tcp(11211),
            description="Memcached access from application",
        )

        cache_sg.add_ingress_rule(
            peer=app_sg,
            connection=ec2.Port.tcp(6379),
            description="Redis access from application",
        )

        # Allow cluster communication for Redis/ElastiCache
        cache_sg.add_ingress_rule(
            peer=cache_sg,
            connection=ec2.Port.tcp_range(6379, 6380),
            description="Redis cluster communication",
        )

        return cache_sg

    def _create_management_security_group(self) -> ec2.SecurityGroup:
        """Create security group for management/bastion services"""

        mgmt_sg = ec2.SecurityGroup(
            self,
            "ManagementSecurityGroup",
            vpc=self.vpc,
            description="Security group for management and bastion services",
            security_group_name=f"options-strategy-mgmt-sg-{self.env_name}",
        )

        # Inbound rules - Allow SSH from specific CIDR blocks
        for cidr in self.allowed_cidr_blocks:
            mgmt_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(cidr),
                connection=ec2.Port.tcp(22),
                description=f"SSH access from {cidr}",
            )

        # If no specific CIDR blocks, allow from office/VPN ranges (example)
        if not self.allowed_cidr_blocks:
            # This should be replaced with actual office/VPN CIDR blocks
            mgmt_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4("203.0.113.0/24"),  # Example office network
                connection=ec2.Port.tcp(22),
                description="SSH access from office network",
            )

        return mgmt_sg

    def _create_internal_security_group(self) -> ec2.SecurityGroup:
        """Create security group for internal service communication"""

        internal_sg = ec2.SecurityGroup(
            self,
            "InternalSecurityGroup",
            vpc=self.vpc,
            description="Security group for internal service-to-service communication",
            security_group_name=f"options-strategy-internal-sg-{self.env_name}",
        )

        # Allow all communication within this security group
        internal_sg.add_ingress_rule(
            peer=internal_sg,
            connection=ec2.Port.all_traffic(),
            description="Internal service communication",
        )

        return internal_sg

    def _create_network_acls(self) -> Dict[str, ec2.NetworkAcl]:
        """Create Network ACLs for additional security"""
        network_acls = {}

        # Public subnet NACL
        network_acls["public"] = self._create_public_nacl()

        # Private subnet NACL
        network_acls["private"] = self._create_private_nacl()

        # Database subnet NACL
        network_acls["database"] = self._create_database_nacl()

        return network_acls

    def _create_public_nacl(self) -> ec2.NetworkAcl:
        """Create NACL for public subnets"""

        public_nacl = ec2.NetworkAcl(
            self,
            "PublicNetworkAcl",
            vpc=self.vpc,
            network_acl_name=f"options-strategy-public-nacl-{self.env_name}",
        )

        # Allow inbound HTTP/HTTPS
        public_nacl.add_entry(
            "AllowInboundHTTP",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=100,
            traffic=ec2.AclTraffic.tcp_port(80),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        public_nacl.add_entry(
            "AllowInboundHTTPS",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=110,
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow return traffic
        public_nacl.add_entry(
            "AllowInboundEphemeral",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=200,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow all outbound traffic
        public_nacl.add_entry(
            "AllowAllOutbound",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        return public_nacl

    def _create_private_nacl(self) -> ec2.NetworkAcl:
        """Create NACL for private subnets"""

        private_nacl = ec2.NetworkAcl(
            self,
            "PrivateNetworkAcl",
            vpc=self.vpc,
            network_acl_name=f"options-strategy-private-nacl-{self.env_name}",
        )

        # Allow inbound from VPC CIDR
        private_nacl.add_entry(
            "AllowInboundFromVPC",
            cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow return traffic
        private_nacl.add_entry(
            "AllowInboundEphemeral",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=200,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow all outbound traffic
        private_nacl.add_entry(
            "AllowAllOutbound",
            cidr=ec2.AclCidr.any_ipv4(),
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        return private_nacl

    def _create_database_nacl(self) -> ec2.NetworkAcl:
        """Create NACL for database subnets"""

        db_nacl = ec2.NetworkAcl(
            self,
            "DatabaseNetworkAcl",
            vpc=self.vpc,
            network_acl_name=f"options-strategy-db-nacl-{self.env_name}",
        )

        # Allow inbound database traffic from VPC only
        db_nacl.add_entry(
            "AllowInboundDBFromVPC",
            cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
            rule_number=100,
            traffic=ec2.AclTraffic.tcp_port_range(3306, 5432),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow Redis traffic
        db_nacl.add_entry(
            "AllowInboundRedisFromVPC",
            cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
            rule_number=110,
            traffic=ec2.AclTraffic.tcp_port(6379),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        # Allow outbound to VPC only
        db_nacl.add_entry(
            "AllowOutboundToVPC",
            cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
        )

        return db_nacl

    def _create_parameter_store_entries(self) -> None:
        """Create Parameter Store entries for security group references"""

        for name, sg in self.security_groups.items():
            ssm.StringParameter(
                self,
                f"{name.title()}SecurityGroupParameter",
                parameter_name=f"/options-strategy/{self.env_name}/security/{name}-security-group-id",
                string_value=sg.security_group_id,
                description=f"Security Group ID for {name} services in {self.env_name} environment",
            )

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for cross-stack dependencies"""

        for name, sg in self.security_groups.items():
            CfnOutput(
                self,
                f"{name.title()}SecurityGroupId",
                value=sg.security_group_id,
                description=f"Security Group ID for {name} services",
                export_name=f"OptionsStrategy-{self.env_name}-Security-{name.title()}-SG-ID",
            )

    def get_security_group(self, name: str) -> ec2.SecurityGroup:
        """
        Get security group by name

        Args:
            name: Name of the security group

        Returns:
            ec2.SecurityGroup: The requested security group

        Raises:
            KeyError: If security group name is not found
        """
        if name not in self.security_groups:
            raise KeyError(
                f"Security group '{name}' not found. Available: {list(self.security_groups.keys())}"
            )

        return self.security_groups[name]

    def add_ingress_rule_to_group(
        self,
        group_name: str,
        peer: ec2.IPeer,
        connection: ec2.Port,
        description: str,
    ) -> None:
        """
        Add ingress rule to a security group

        Args:
            group_name: Name of the security group
            peer: The peer to allow access from
            connection: The connection/port to allow
            description: Description of the rule
        """
        sg = self.get_security_group(group_name)
        sg.add_ingress_rule(
            peer=peer, connection=connection, description=description
        )
