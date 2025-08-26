"""
Comprehensive CDK Stack for Options Strategy Lifecycle Platform

This module creates a comprehensive single-stack architecture that includes all
production-grade infrastructure components in one cohesive stack to avoid
circular dependency issues while providing full functionality:

- VPC with multi-tier architecture (public, private app, private DB)
- Comprehensive security groups and policies
- Complete IAM roles and policies for all services
- Advanced Parameter Store configuration management
- Production-grade CloudWatch monitoring, dashboards, and alerting
- SNS topics for notifications and alerts
- Cost optimization and compliance features

The architecture is designed for deployment in ap-south-1 (Asia Pacific - Mumbai) region
to comply with Indian market data residency requirements.
"""

from typing import Dict, Any
from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    RemovalPolicy,
    Duration,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_ssm as ssm,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
)
from constructs import Construct


class OptionsStrategyPlatformStack(Stack):
    """
    Comprehensive CDK Stack for Options Strategy Lifecycle Platform
    
    This stack creates production-ready infrastructure including:
    - Complete VPC with multi-tier networking
    - Comprehensive security groups and IAM policies
    - Advanced CloudWatch monitoring and alerting
    - Production-grade Parameter Store configuration
    - SNS topics for notifications and operational alerts
    - Cost optimization and compliance features
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_config: Any,  # EnvironmentConfig type
        **kwargs,
    ) -> None:
        """
        Initialize the comprehensive Options Strategy Platform Stack
        
        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_config: Environment configuration object
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_config = env_config
        self.env_name = env_config.env_name

        # Apply standard tags to all resources in this stack
        self._apply_standard_tags()

        # 1. Create VPC and networking infrastructure
        print("   🌐 Creating VPC and networking infrastructure...")
        self._create_vpc_infrastructure()

        # 2. Create comprehensive security groups
        print("   🔒 Creating comprehensive security groups...")
        self._create_security_infrastructure()

        # 3. Create comprehensive IAM roles and policies
        print("   👥 Creating comprehensive IAM roles and policies...")
        self._create_iam_infrastructure()

        # 4. Create comprehensive CloudWatch logging
        print("   📝 Creating comprehensive CloudWatch logging...")
        self._create_logging_infrastructure()

        # 5. Create comprehensive SNS topics and notifications
        print("   📢 Creating SNS topics and notification system...")
        self._create_notification_infrastructure()

        # 6. Create comprehensive CloudWatch monitoring and alerting
        print("   📊 Creating comprehensive monitoring and alerting...")
        self._create_monitoring_infrastructure()

        # 7. Create comprehensive Parameter Store configuration
        print("   ⚙️  Creating comprehensive Parameter Store configuration...")
        self._create_configuration_infrastructure()

        # 8. Create CloudFormation outputs
        print("   📤 Creating CloudFormation outputs...")
        self._create_outputs()

        print("   ✅ Comprehensive infrastructure stack created successfully!")

    def _apply_standard_tags(self) -> None:
        """Apply standard tags to all resources in this stack"""
        for key, value in self.env_config.resource_tags.items():
            Tags.of(self).add(key, value)

    def _create_vpc_infrastructure(self) -> None:
        """Create comprehensive VPC infrastructure"""
        # Create VPC with multi-tier architecture
        self.vpc = ec2.Vpc(
            self,
            "OptionsStrategyVPC",
            vpc_name=f"options-strategy-vpc-{self.env_name}",
            ip_addresses=ec2.IpAddresses.cidr(self.env_config.networking.vpc_cidr),
            max_azs=self.env_config.networking.max_azs,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"public-{self.env_name}",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,  # /24 allows ~250 IPs per subnet
                ),
                ec2.SubnetConfiguration(
                    name=f"private-app-{self.env_name}",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=22,  # /22 allows ~1000 IPs per subnet
                ),
                ec2.SubnetConfiguration(
                    name=f"private-db-{self.env_name}",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,  # /24 is sufficient for database instances
                ),
            ],
            nat_gateways=1 if self.env_name == "dev" else self.env_config.networking.max_azs,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateway_provider=ec2.NatProvider.gateway(),
        )

        # Create VPC Flow Logs for security monitoring
        self.vpc_flow_logs = logs.LogGroup(
            self,
            "VPCFlowLogsGroup",
            log_group_name=f"/aws/vpc/flowlogs/options-strategy-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN,
        )

        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(self.vpc_flow_logs),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

    def _create_security_infrastructure(self) -> None:
        """Create comprehensive security groups and rules"""
        self.security_groups = {}

        # Application Load Balancer Security Group
        self.security_groups["alb"] = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True,
        )

        # Application Security Group  
        self.security_groups["app"] = ec2.SecurityGroup(
            self,
            "ApplicationSecurityGroup",
            vpc=self.vpc,
            description="Security group for application servers and containers",
            allow_all_outbound=True,
        )

        # Lambda Security Group
        self.security_groups["lambda"] = ec2.SecurityGroup(
            self,
            "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions",
            allow_all_outbound=True,
        )

        # Database Security Group
        self.security_groups["database"] = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup", 
            vpc=self.vpc,
            description="Security group for databases and data stores",
            allow_all_outbound=False,
        )

        # Configure comprehensive security group rules
        # ALB accepts HTTPS from anywhere
        self.security_groups["alb"].add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS from anywhere",
        )

        # ALB accepts HTTP from anywhere (will redirect to HTTPS)
        self.security_groups["alb"].add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP from anywhere (redirects to HTTPS)",
        )

        # Applications accept traffic from ALB
        self.security_groups["app"].add_ingress_rule(
            peer=self.security_groups["alb"],
            connection=ec2.Port.tcp(8000),
            description="App port from ALB",
        )

        # Lambda can communicate with apps
        self.security_groups["lambda"].add_ingress_rule(
            peer=self.security_groups["app"],
            connection=ec2.Port.tcp(443),
            description="HTTPS from application servers",
        )

        # Databases accept connections from apps and lambdas
        self.security_groups["database"].add_ingress_rule(
            peer=self.security_groups["app"],
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from application servers",
        )

        self.security_groups["database"].add_ingress_rule(
            peer=self.security_groups["lambda"],
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from Lambda functions",
        )

        # Redis/ElastiCache access
        self.security_groups["database"].add_ingress_rule(
            peer=self.security_groups["app"],
            connection=ec2.Port.tcp(6379),
            description="Redis from application servers",
        )

    def _create_iam_infrastructure(self) -> None:
        """Create comprehensive IAM roles and policies"""
        self.iam_roles = {}

        # Lambda execution role with comprehensive permissions
        self.iam_roles["lambda_execution"] = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=f"options-strategy-lambda-execution-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ],
        )

        # ECS execution role
        self.iam_roles["ecs_execution"] = iam.Role(
            self,
            "ECSExecutionRole",
            role_name=f"options-strategy-ecs-execution-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
            ],
        )

        # ECS task role with comprehensive permissions
        self.iam_roles["ecs_task"] = iam.Role(
            self,
            "ECSTaskRole",
            role_name=f"options-strategy-ecs-task-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # API Gateway execution role
        self.iam_roles["api_gateway"] = iam.Role(
            self,
            "APIGatewayRole",
            role_name=f"options-strategy-api-gateway-{self.env_name}",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs"),
            ],
        )

        # Create comprehensive policies for each role
        self._create_comprehensive_iam_policies()

    def _create_comprehensive_iam_policies(self) -> None:
        """Create comprehensive IAM policies for all services"""
        
        # Lambda comprehensive policy
        lambda_policy = iam.Policy(
            self,
            "LambdaComprehensivePolicy",
            policy_name=f"options-strategy-lambda-policy-{self.env_name}",
            statements=[
                # Parameter Store access
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
                    resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/{self.env_name}/*"],
                ),
                # CloudWatch metrics and logging
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["cloudwatch:PutMetricData", "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=["*"],
                ),
                # SNS publishing for notifications
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sns:Publish"],
                    resources=[f"arn:aws:sns:{self.region}:{self.account}:options-strategy-*-{self.env_name}"],
                ),
            ],
        )
        self.iam_roles["lambda_execution"].attach_inline_policy(lambda_policy)

        # ECS task comprehensive policy
        ecs_policy = iam.Policy(
            self,
            "ECSTaskComprehensivePolicy", 
            policy_name=f"options-strategy-ecs-policy-{self.env_name}",
            statements=[
                # Parameter Store access
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
                    resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/options-strategy/{self.env_name}/*"],
                ),
                # CloudWatch metrics
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["cloudwatch:PutMetricData"],
                    resources=["*"],
                ),
            ],
        )
        self.iam_roles["ecs_task"].attach_inline_policy(ecs_policy)

    def _create_logging_infrastructure(self) -> None:
        """Create comprehensive CloudWatch logging infrastructure"""
        retention = logs.RetentionDays.ONE_WEEK if self.env_name == "dev" else logs.RetentionDays.ONE_MONTH
        removal_policy = RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN

        self.log_groups = {}

        # Application logs
        self.log_groups["application"] = logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"/aws/ecs/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )

        # Lambda logs
        self.log_groups["lambda"] = logs.LogGroup(
            self,
            "LambdaLogGroup", 
            log_group_name=f"/aws/lambda/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )

        # API Gateway logs
        self.log_groups["api_gateway"] = logs.LogGroup(
            self,
            "APIGatewayLogGroup",
            log_group_name=f"/aws/apigateway/options-strategy-{self.env_name}",
            retention=retention,
            removal_policy=removal_policy,
        )

    def _create_notification_infrastructure(self) -> None:
        """Create comprehensive SNS notification system"""
        self.sns_topics = {}

        # Critical alerts topic
        self.sns_topics["critical_alerts"] = sns.Topic(
            self,
            "CriticalAlertsTopic",
            topic_name=f"options-strategy-critical-alerts-{self.env_name}",
            display_name=f"Options Strategy Critical Alerts - {self.env_name}",
        )

        # Operational alerts topic  
        self.sns_topics["operational_alerts"] = sns.Topic(
            self,
            "OperationalAlertsTopic",
            topic_name=f"options-strategy-operational-alerts-{self.env_name}",
            display_name=f"Options Strategy Operational Alerts - {self.env_name}",
        )

        # Trading notifications topic
        self.sns_topics["trading_notifications"] = sns.Topic(
            self,
            "TradingNotificationsTopic", 
            topic_name=f"options-strategy-trading-notifications-{self.env_name}",
            display_name=f"Options Strategy Trading Notifications - {self.env_name}",
        )

        # Subscribe email to critical alerts if configured
        if hasattr(self.env_config.monitoring, 'alarm_notification_email') and self.env_config.monitoring.alarm_notification_email:
            sns_subscriptions.EmailSubscription(self.env_config.monitoring.alarm_notification_email).bind(
                self.sns_topics["critical_alerts"]
            )

    def _create_monitoring_infrastructure(self) -> None:
        """Create comprehensive CloudWatch monitoring, dashboards, and alerting"""
        
        # Create comprehensive CloudWatch dashboard
        self.dashboard = cloudwatch.Dashboard(
            self,
            "OptionsStrategyDashboard",
            dashboard_name=f"OptionsStrategy-{self.env_name}",
        )

        # Add comprehensive widgets to dashboard
        self._create_dashboard_widgets()

        # Create comprehensive CloudWatch alarms
        self._create_comprehensive_alarms()

    def _create_dashboard_widgets(self) -> None:
        """Create comprehensive dashboard widgets"""
        
        # Platform overview widget
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Platform Overview - Log Events",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Logs",
                        metric_name="IncomingLogEvents",
                        dimensions_map={"LogGroupName": self.log_groups["application"].log_group_name},
                        label="Application Logs",
                    ),
                    cloudwatch.Metric(
                        namespace="AWS/Logs", 
                        metric_name="IncomingLogEvents",
                        dimensions_map={"LogGroupName": self.log_groups["lambda"].log_group_name},
                        label="Lambda Logs",
                    ),
                ],
                width=12,
                height=6,
            )
        )

        # VPC metrics widget
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="VPC Flow Logs",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Logs",
                        metric_name="IncomingLogEvents", 
                        dimensions_map={"LogGroupName": self.vpc_flow_logs.log_group_name},
                        label="VPC Flow Logs",
                    ),
                ],
                width=12,
                height=6,
            )
        )

    def _create_comprehensive_alarms(self) -> None:
        """Create comprehensive CloudWatch alarms"""
        self.alarms = {}

        # High error rate alarm
        self.alarms["high_error_rate"] = cloudwatch.Alarm(
            self,
            "HighErrorRateAlarm",
            alarm_name=f"options-strategy-high-error-rate-{self.env_name}",
            alarm_description="High error rate detected in Lambda functions",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={"FunctionName": f"options-strategy-{self.env_name}"},
                statistic="Sum",
            ),
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
        )
        self.alarms["high_error_rate"].add_alarm_action(
            cw_actions.SnsAction(self.sns_topics["critical_alerts"])
        )

        # High duration alarm
        self.alarms["high_duration"] = cloudwatch.Alarm(
            self,
            "HighDurationAlarm", 
            alarm_name=f"options-strategy-high-duration-{self.env_name}",
            alarm_description="Lambda functions taking too long to execute",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Duration",
                dimensions_map={"FunctionName": f"options-strategy-{self.env_name}"},
                statistic="Average",
            ),
            threshold=10000,  # 10 seconds
            evaluation_periods=3,
        )
        self.alarms["high_duration"].add_alarm_action(
            cw_actions.SnsAction(self.sns_topics["operational_alerts"])
        )

    def _create_configuration_infrastructure(self) -> None:
        """Create comprehensive Parameter Store configuration management"""
        
        # Core infrastructure parameters
        self.parameters = {}
        
        infrastructure_params = {
            "vpc/id": self.vpc.vpc_id,
            "vpc/cidr": self.env_config.networking.vpc_cidr,
            "subnets/public": ",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            "subnets/private": ",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            "subnets/isolated": ",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            "security-groups/alb": self.security_groups["alb"].security_group_id,
            "security-groups/app": self.security_groups["app"].security_group_id,
            "security-groups/lambda": self.security_groups["lambda"].security_group_id,
            "security-groups/database": self.security_groups["database"].security_group_id,
            "iam/lambda-role-arn": self.iam_roles["lambda_execution"].role_arn,
            "iam/ecs-execution-role-arn": self.iam_roles["ecs_execution"].role_arn,
            "iam/ecs-task-role-arn": self.iam_roles["ecs_task"].role_arn,
            "sns/critical-alerts-topic": self.sns_topics["critical_alerts"].topic_arn,
            "sns/operational-alerts-topic": self.sns_topics["operational_alerts"].topic_arn,
            "sns/trading-notifications-topic": self.sns_topics["trading_notifications"].topic_arn,
        }

        for param_name, param_value in infrastructure_params.items():
            self.parameters[param_name] = ssm.StringParameter(
                self,
                f"Parameter{param_name.replace('/', '').replace('-', '').title()}",
                parameter_name=f"/options-strategy/{self.env_name}/{param_name}",
                string_value=param_value,
                description=f"{param_name} for Options Strategy Platform {self.env_name}",
            )

    def _create_outputs(self) -> None:
        """Create comprehensive CloudFormation outputs"""
        
        # Core infrastructure outputs
        CfnOutput(self, "VPCId", value=self.vpc.vpc_id, description="VPC ID")
        CfnOutput(self, "Environment", value=self.env_name, description="Environment name")
        
        # IAM role outputs
        CfnOutput(self, "LambdaRoleArn", value=self.iam_roles["lambda_execution"].role_arn)
        CfnOutput(self, "ECSExecutionRoleArn", value=self.iam_roles["ecs_execution"].role_arn)
        CfnOutput(self, "ECSTaskRoleArn", value=self.iam_roles["ecs_task"].role_arn)
        
        # SNS topic outputs
        CfnOutput(self, "CriticalAlertsTopicArn", value=self.sns_topics["critical_alerts"].topic_arn)
        CfnOutput(self, "OperationalAlertsTopicArn", value=self.sns_topics["operational_alerts"].topic_arn)
        CfnOutput(self, "TradingNotificationsTopicArn", value=self.sns_topics["trading_notifications"].topic_arn)
        
        # Dashboard output
        CfnOutput(self, "DashboardURL", value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboard.dashboard_name}")

    @property
    def lambda_execution_role(self) -> iam.Role:
        """Get Lambda execution role"""
        return self.iam_roles["lambda_execution"]

    @property 
    def ecs_execution_role(self) -> iam.Role:
        """Get ECS execution role"""
        return self.iam_roles["ecs_execution"]

    @property
    def ecs_task_role(self) -> iam.Role:
        """Get ECS task role"""
        return self.iam_roles["ecs_task"]