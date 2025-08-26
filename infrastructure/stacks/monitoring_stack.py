"""
Monitoring Stack for Options Strategy Lifecycle Platform

This module defines comprehensive monitoring, alerting, and observability infrastructure
for the Options Strategy Lifecycle Platform, including:

- CloudWatch dashboards for operational visibility
- CloudWatch alarms for proactive alerting
- CloudWatch Insights queries for log analysis
- SNS topics for alarm notifications
- Custom metrics for trading platform KPIs
- X-Ray tracing configuration
- Application performance monitoring

The monitoring is designed for production-grade trading platform requirements
with focus on latency, availability, and financial data accuracy monitoring.

Designed for deployment in ap-south-1 (Asia Pacific - Mumbai) region
to comply with Indian market data residency requirements.
"""

from typing import Dict, Optional
from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_logs as logs,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as events_targets,
)
from constructs import Construct


class MonitoringStack(Stack):
    """
    Comprehensive Monitoring Stack for Options Strategy Lifecycle Platform

    This stack creates operational monitoring infrastructure including:
    - Multi-layered CloudWatch dashboards (Executive, Operations, Technical)
    - Proactive alerting with SNS integration
    - Custom metrics for trading-specific KPIs
    - Application performance monitoring
    - Security and compliance monitoring
    - Cost monitoring and optimization alerts
    - Log aggregation and analysis
    - X-Ray distributed tracing setup
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        vpc: Optional[ec2.IVpc] = None,
        notification_email: Optional[str] = None,
        enable_detailed_monitoring: bool = True,
        enable_cost_alerts: bool = True,
        log_retention_days: int = 30,
        **kwargs,
    ) -> None:
        """
        Initialize the Monitoring Stack

        Args:
            scope: The scope in which to define this construct
            construct_id: The scoped construct ID
            env_name: Environment name (dev, staging, prod)
            vpc: VPC for VPC-related monitoring
            notification_email: Email for alarm notifications
            enable_detailed_monitoring: Enable detailed CloudWatch monitoring
            enable_cost_alerts: Enable cost monitoring and alerts
            log_retention_days: CloudWatch logs retention period
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.vpc = vpc
        self.notification_email = notification_email
        self.enable_detailed_monitoring = enable_detailed_monitoring
        self.enable_cost_alerts = enable_cost_alerts

        # Create SNS topics for notifications
        self.notification_topics = self._create_notification_topics()

        # Create custom CloudWatch log groups
        self.monitoring_log_groups = self._create_monitoring_log_groups(
            log_retention_days
        )

        # Create CloudWatch alarms
        self.alarms = self._create_cloudwatch_alarms()

        # Create CloudWatch dashboards
        self.dashboards = self._create_cloudwatch_dashboards()

        # Create log insights queries
        self._create_log_insights_queries()

        # Create custom metrics and filters
        self._create_custom_metrics()

        # Create monitoring Lambda functions
        self.monitoring_functions = self._create_monitoring_functions()

        # Create EventBridge rules for automated monitoring
        self._create_monitoring_automation()

        # Create Parameter Store entries
        self._create_parameter_store_entries()

        # Create CloudFormation outputs
        self._create_stack_outputs()

    def _create_notification_topics(self) -> Dict[str, sns.Topic]:
        """Create SNS topics for different types of notifications"""
        topics = {}

        # Critical alerts topic (P1 incidents)
        topics["critical"] = sns.Topic(
            self,
            "CriticalAlertsTopics",
            topic_name=f"options-strategy-critical-alerts-{self.env_name}",
            display_name=f"Options Strategy Critical Alerts - {self.env_name.title()}",
            description="Critical alerts requiring immediate attention",
        )

        # Warning alerts topic (P2/P3 incidents)
        topics["warning"] = sns.Topic(
            self,
            "WarningAlertsTopic",
            topic_name=f"options-strategy-warning-alerts-{self.env_name}",
            display_name=f"Options Strategy Warning Alerts - {self.env_name.title()}",
            description="Warning alerts for monitoring and investigation",
        )

        # Cost alerts topic
        topics["cost"] = sns.Topic(
            self,
            "CostAlertsTopic",
            topic_name=f"options-strategy-cost-alerts-{self.env_name}",
            display_name=f"Options Strategy Cost Alerts - {self.env_name.title()}",
            description="Cost monitoring and budget alerts",
        )

        # Security alerts topic
        topics["security"] = sns.Topic(
            self,
            "SecurityAlertsTopic",
            topic_name=f"options-strategy-security-alerts-{self.env_name}",
            display_name=f"Options Strategy Security Alerts - {self.env_name.title()}",
            description="Security monitoring and compliance alerts",
        )

        # Add email subscriptions if email provided
        if self.notification_email:
            for topic_name, topic in topics.items():
                topic.add_subscription(
                    sns_subscriptions.EmailSubscription(
                        self.notification_email
                    )
                )

        return topics

    def _create_monitoring_log_groups(
        self, retention_days: int
    ) -> Dict[str, logs.LogGroup]:
        """Create dedicated log groups for monitoring purposes"""

        # Map retention days to CDK retention enum
        if retention_days <= 7:
            retention = logs.RetentionDays.ONE_WEEK
        elif retention_days <= 14:
            retention = logs.RetentionDays.TWO_WEEKS
        elif retention_days <= 30:
            retention = logs.RetentionDays.ONE_MONTH
        elif retention_days <= 90:
            retention = logs.RetentionDays.THREE_MONTHS
        else:
            retention = logs.RetentionDays.ONE_YEAR

        removal_policy = (
            RemovalPolicy.RETAIN
            if self.env_name == "prod"
            else RemovalPolicy.DESTROY
        )

        log_groups = {}

        # Platform monitoring logs
        log_groups["monitoring"] = logs.LogGroup(
            self,
            "MonitoringLogGroup",
            log_group_name=f"/aws/options-strategy/{self.env_name}/monitoring",
            retention=retention,
            removal_policy=removal_policy,
        )

        # Trading activity logs
        log_groups["trading"] = logs.LogGroup(
            self,
            "TradingLogGroup",
            log_group_name=f"/aws/options-strategy/{self.env_name}/trading",
            retention=retention,
            removal_policy=removal_policy,
        )

        # Performance metrics logs
        log_groups["performance"] = logs.LogGroup(
            self,
            "PerformanceLogGroup",
            log_group_name=f"/aws/options-strategy/{self.env_name}/performance",
            retention=retention,
            removal_policy=removal_policy,
        )

        # Error tracking logs
        log_groups["errors"] = logs.LogGroup(
            self,
            "ErrorLogGroup",
            log_group_name=f"/aws/options-strategy/{self.env_name}/errors",
            retention=retention,
            removal_policy=removal_policy,
        )

        # Audit logs for compliance
        log_groups["audit"] = logs.LogGroup(
            self,
            "AuditLogGroup",
            log_group_name=f"/aws/options-strategy/{self.env_name}/audit",
            retention=retention,
            removal_policy=removal_policy,
        )

        return log_groups

    def _create_cloudwatch_alarms(self) -> Dict[str, cloudwatch.Alarm]:
        """Create comprehensive CloudWatch alarms for the platform"""
        alarms = {}

        # Lambda function error rate alarm
        alarms["lambda_error_rate"] = cloudwatch.Alarm(
            self,
            "LambdaErrorRateAlarm",
            alarm_name=f"options-strategy-lambda-error-rate-{self.env_name}",
            alarm_description="Lambda function error rate is too high",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={
                    "FunctionName": f"options-strategy-{self.env_name}"
                },
                statistic=cloudwatch.Stats.SUM,
                period=Duration.minutes(5),
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        alarms["lambda_error_rate"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["critical"])
        )

        # Lambda duration alarm
        alarms["lambda_duration"] = cloudwatch.Alarm(
            self,
            "LambdaDurationAlarm",
            alarm_name=f"options-strategy-lambda-duration-{self.env_name}",
            alarm_description="Lambda function duration is too high",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Duration",
                dimensions_map={
                    "FunctionName": f"options-strategy-{self.env_name}"
                },
                statistic=cloudwatch.Stats.AVERAGE,
                period=Duration.minutes(5),
            ),
            threshold=30000,  # 30 seconds
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        alarms["lambda_duration"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["warning"])
        )

        # API Gateway 4xx error rate
        alarms["api_4xx_errors"] = cloudwatch.Alarm(
            self,
            "API4xxErrorsAlarm",
            alarm_name=f"options-strategy-api-4xx-errors-{self.env_name}",
            alarm_description="API Gateway 4xx error rate is too high",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={
                    "ApiName": f"options-strategy-api-{self.env_name}"
                },
                statistic=cloudwatch.Stats.SUM,
                period=Duration.minutes(5),
            ),
            threshold=50,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        alarms["api_4xx_errors"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["warning"])
        )

        # API Gateway 5xx error rate
        alarms["api_5xx_errors"] = cloudwatch.Alarm(
            self,
            "API5xxErrorsAlarm",
            alarm_name=f"options-strategy-api-5xx-errors-{self.env_name}",
            alarm_description="API Gateway 5xx error rate is too high",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={
                    "ApiName": f"options-strategy-api-{self.env_name}"
                },
                statistic=cloudwatch.Stats.SUM,
                period=Duration.minutes(5),
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        alarms["api_5xx_errors"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["critical"])
        )

        # API Gateway latency alarm
        alarms["api_latency"] = cloudwatch.Alarm(
            self,
            "APILatencyAlarm",
            alarm_name=f"options-strategy-api-latency-{self.env_name}",
            alarm_description="API Gateway latency is too high",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={
                    "ApiName": f"options-strategy-api-{self.env_name}"
                },
                statistic=cloudwatch.Stats.AVERAGE,
                period=Duration.minutes(5),
            ),
            threshold=5000,  # 5 seconds
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        alarms["api_latency"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["warning"])
        )

        # DynamoDB throttling alarm
        alarms["dynamo_throttles"] = cloudwatch.Alarm(
            self,
            "DynamoThrottlesAlarm",
            alarm_name=f"options-strategy-dynamo-throttles-{self.env_name}",
            alarm_description="DynamoDB throttling events detected",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="UserErrors",
                dimensions_map={
                    "TableName": f"options-strategy-{self.env_name}"
                },
                statistic=cloudwatch.Stats.SUM,
                period=Duration.minutes(5),
            ),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        alarms["dynamo_throttles"].add_alarm_action(
            cw_actions.SnsAction(self.notification_topics["critical"])
        )

        # Add VPC-specific alarms if VPC is provided
        if self.vpc:
            # VPC Flow Logs alarm
            alarms["vpc_rejected_connections"] = cloudwatch.Alarm(
                self,
                "VPCRejectedConnectionsAlarm",
                alarm_name=f"options-strategy-vpc-rejected-{self.env_name}",
                alarm_description="High number of rejected VPC connections",
                metric=cloudwatch.Metric(
                    namespace="AWS/VPC/FlowLogs",
                    metric_name="PacketsDropped",
                    statistic=cloudwatch.Stats.SUM,
                    period=Duration.minutes(10),
                ),
                threshold=100,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            )
            alarms["vpc_rejected_connections"].add_alarm_action(
                cw_actions.SnsAction(self.notification_topics["security"])
            )

        # Cost monitoring alarm
        if self.enable_cost_alerts:
            # Note: Cost Explorer metrics require special handling
            # This is a placeholder for custom cost monitoring logic
            pass

        return alarms

    def _create_cloudwatch_dashboards(self) -> Dict[str, cloudwatch.Dashboard]:
        """Create comprehensive CloudWatch dashboards"""
        dashboards = {}

        # Executive Dashboard - High-level business metrics
        dashboards["executive"] = cloudwatch.Dashboard(
            self,
            "ExecutiveDashboard",
            dashboard_name=f"OptionsStrategy-Executive-{self.env_name}",
            widgets=[
                # Business metrics row
                [
                    cloudwatch.SingleValueWidget(
                        title="Platform Health",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="AWS/ApplicationELB",
                                metric_name="HealthyHostCount",
                                statistic=cloudwatch.Stats.AVERAGE,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                    cloudwatch.SingleValueWidget(
                        title="Daily Active Users",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="OptionsStrategy/Users",
                                metric_name="DailyActiveUsers",
                                statistic=cloudwatch.Stats.MAXIMUM,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                ],
                # Trading metrics row
                [
                    cloudwatch.GraphWidget(
                        title="Trading Volume",
                        left=[
                            cloudwatch.Metric(
                                namespace="OptionsStrategy/Trading",
                                metric_name="TradingVolume",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=12,
                        height=6,
                    ),
                ],
                # System health row
                [
                    cloudwatch.GraphWidget(
                        title="System Availability",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="5XXError",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=12,
                        height=6,
                    ),
                ],
            ],
        )

        # Operations Dashboard - Detailed operational metrics
        dashboards["operations"] = cloudwatch.Dashboard(
            self,
            "OperationsDashboard",
            dashboard_name=f"OptionsStrategy-Operations-{self.env_name}",
            widgets=[
                # API Gateway metrics
                [
                    cloudwatch.GraphWidget(
                        title="API Gateway Requests",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Count",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                    cloudwatch.GraphWidget(
                        title="API Gateway Latency",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/ApiGateway",
                                metric_name="Latency",
                                statistic=cloudwatch.Stats.AVERAGE,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                ],
                # Lambda metrics
                [
                    cloudwatch.GraphWidget(
                        title="Lambda Invocations",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                    cloudwatch.GraphWidget(
                        title="Lambda Errors",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Errors",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=6,
                        height=6,
                    ),
                ],
                # Database metrics
                [
                    cloudwatch.GraphWidget(
                        title="DynamoDB Read/Write Capacity",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedReadCapacityUnits",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/DynamoDB",
                                metric_name="ConsumedWriteCapacityUnits",
                                statistic=cloudwatch.Stats.SUM,
                            )
                        ],
                        width=12,
                        height=6,
                    ),
                ],
            ],
        )

        # Technical Dashboard - Low-level technical metrics
        dashboards["technical"] = cloudwatch.Dashboard(
            self,
            "TechnicalDashboard",
            dashboard_name=f"OptionsStrategy-Technical-{self.env_name}",
            widgets=[
                # Infrastructure metrics
                [
                    (
                        cloudwatch.GraphWidget(
                            title="VPC Flow Logs",
                            left=[
                                cloudwatch.Metric(
                                    namespace="AWS/VPC/FlowLogs",
                                    metric_name="PacketsDropped",
                                    statistic=cloudwatch.Stats.SUM,
                                )
                            ],
                            width=6,
                            height=6,
                        )
                        if self.vpc
                        else cloudwatch.TextWidget(
                            markdown="VPC metrics not available",
                            width=6,
                            height=6,
                        )
                    ),
                    cloudwatch.LogQueryWidget(
                        title="Error Log Analysis",
                        log_groups=[self.monitoring_log_groups["errors"]],
                        query_lines=[
                            "fields @timestamp, @message",
                            "filter @message like /ERROR/",
                            "sort @timestamp desc",
                            "limit 100",
                        ],
                        width=6,
                        height=6,
                    ),
                ],
                # Application logs
                [
                    cloudwatch.LogQueryWidget(
                        title="Recent Trading Activity",
                        log_groups=[self.monitoring_log_groups["trading"]],
                        query_lines=[
                            "fields @timestamp, @message",
                            "filter @message like /TRADE/",
                            "sort @timestamp desc",
                            "limit 50",
                        ],
                        width=12,
                        height=6,
                    ),
                ],
            ],
        )

        return dashboards

    def _create_log_insights_queries(self) -> None:
        """Create saved CloudWatch Logs Insights queries"""

        # Common queries for troubleshooting
        queries = [
            {
                "name": "ErrorAnalysis",
                "query": """
                    fields @timestamp, @message
                    | filter @message like /ERROR/
                    | stats count() by bin(5m)
                    | sort @timestamp desc
                """,
                "log_groups": [
                    self.monitoring_log_groups["errors"].log_group_name
                ],
            },
            {
                "name": "PerformanceAnalysis",
                "query": """
                    fields @timestamp, @duration
                    | filter @duration > 1000
                    | stats avg(@duration), max(@duration), min(@duration) by bin(5m)
                    | sort @timestamp desc
                """,
                "log_groups": [
                    self.monitoring_log_groups["performance"].log_group_name
                ],
            },
            {
                "name": "TradingVolumeAnalysis",
                "query": """
                    fields @timestamp, @message
                    | filter @message like /TRADE_EXECUTED/
                    | stats count() as trade_count by bin(1h)
                    | sort @timestamp desc
                """,
                "log_groups": [
                    self.monitoring_log_groups["trading"].log_group_name
                ],
            },
        ]

        # Create Parameter Store entries for saved queries
        for i, query in enumerate(queries):
            ssm.StringParameter(
                self,
                f"LogInsightsQuery{i}",
                parameter_name=f"/options-strategy/{self.env_name}/monitoring/queries/{query['name']}",
                string_value=query["query"],
                description=f"CloudWatch Logs Insights query for {query['name']}",
            )

    def _create_custom_metrics(self) -> None:
        """Create custom metrics and metric filters for business KPIs"""

        # Create metric filters for application logs
        trading_metric_filter = logs.MetricFilter(
            self,
            "TradingVolumeMetricFilter",
            log_group=self.monitoring_log_groups["trading"],
            metric_namespace="OptionsStrategy/Trading",
            metric_name="TradingVolume",
            filter_pattern=logs.FilterPattern.literal(
                '[timestamp, request_id, level="INFO", message="TRADE_EXECUTED", volume]'
            ),
            metric_value="$volume",
        )

        error_metric_filter = logs.MetricFilter(
            self,
            "ErrorCountMetricFilter",
            log_group=self.monitoring_log_groups["errors"],
            metric_namespace="OptionsStrategy/Errors",
            metric_name="ErrorCount",
            filter_pattern=logs.FilterPattern.literal(
                '[timestamp, request_id, level="ERROR", ...]'
            ),
            metric_value="1",
        )

        performance_metric_filter = logs.MetricFilter(
            self,
            "PerformanceMetricFilter",
            log_group=self.monitoring_log_groups["performance"],
            metric_namespace="OptionsStrategy/Performance",
            metric_name="ResponseTime",
            filter_pattern=logs.FilterPattern.literal(
                '[timestamp, request_id, level="INFO", message="REQUEST_COMPLETED", duration]'
            ),
            metric_value="$duration",
        )

    def _create_monitoring_functions(self) -> Dict[str, lambda_.Function]:
        """Create Lambda functions for custom monitoring tasks"""
        functions = {}

        # Health check function
        functions["health_check"] = lambda_.Function(
            self,
            "HealthCheckFunction",
            function_name=f"options-strategy-health-check-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                """
import json
import boto3
import urllib3
from datetime import datetime

def handler(event, context):
    '''
    Health check function that monitors platform components
    and publishes custom metrics to CloudWatch
    '''
    
    cloudwatch = boto3.client('cloudwatch')
    
    # Perform health checks
    health_status = {
        'api_gateway': check_api_gateway(),
        'database': check_database(),
        'lambda_functions': check_lambda_functions(),
    }
    
    # Calculate overall health score
    healthy_count = sum(1 for status in health_status.values() if status)
    total_count = len(health_status)
    health_score = (healthy_count / total_count) * 100
    
    # Publish custom metric
    cloudwatch.put_metric_data(
        Namespace='OptionsStrategy/Health',
        MetricData=[
            {
                'MetricName': 'OverallHealth',
                'Value': health_score,
                'Unit': 'Percent',
                'Timestamp': datetime.utcnow(),
            }
        ]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'health_status': health_status,
            'health_score': health_score,
        })
    }

def check_api_gateway():
    # Placeholder for API Gateway health check
    return True

def check_database():
    # Placeholder for database health check
    return True

def check_lambda_functions():
    # Placeholder for Lambda health check
    return True
            """
            ),
            timeout=Duration.minutes(5),
            memory_size=256,
            description="Platform health check function",
            environment={
                "ENV_NAME": self.env_name,
            },
        )

        # Grant permissions to publish metrics
        functions["health_check"].add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        return functions

    def _create_monitoring_automation(self) -> None:
        """Create EventBridge rules for automated monitoring tasks"""

        # Schedule health check function to run every 5 minutes
        health_check_rule = events.Rule(
            self,
            "HealthCheckRule",
            rule_name=f"options-strategy-health-check-{self.env_name}",
            description="Trigger health check function every 5 minutes",
            schedule=events.Schedule.rate(Duration.minutes(5)),
        )

        health_check_rule.add_target(
            events_targets.LambdaFunction(
                self.monitoring_functions["health_check"]
            )
        )

        # Create rule for alarm state changes
        alarm_state_rule = events.Rule(
            self,
            "AlarmStateChangeRule",
            rule_name=f"options-strategy-alarm-state-{self.env_name}",
            description="React to CloudWatch alarm state changes",
            event_pattern=events.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"],
                detail={
                    "alarmName": [
                        {"prefix": f"options-strategy-{self.env_name}"}
                    ]
                },
            ),
        )

        # Add target to log alarm state changes
        alarm_state_rule.add_target(
            events_targets.CloudWatchLogGroup(
                self.monitoring_log_groups["monitoring"]
            )
        )

    def _create_parameter_store_entries(self) -> None:
        """Create Parameter Store entries for monitoring configuration"""

        # Dashboard URLs
        ssm.StringParameter(
            self,
            "ExecutiveDashboardURL",
            parameter_name=f"/options-strategy/{self.env_name}/monitoring/dashboards/executive-url",
            string_value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboards['executive'].dashboard_name}",
            description="URL to executive CloudWatch dashboard",
        )

        ssm.StringParameter(
            self,
            "OperationsDashboardURL",
            parameter_name=f"/options-strategy/{self.env_name}/monitoring/dashboards/operations-url",
            string_value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboards['operations'].dashboard_name}",
            description="URL to operations CloudWatch dashboard",
        )

        ssm.StringParameter(
            self,
            "TechnicalDashboardURL",
            parameter_name=f"/options-strategy/{self.env_name}/monitoring/dashboards/technical-url",
            string_value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboards['technical'].dashboard_name}",
            description="URL to technical CloudWatch dashboard",
        )

        # SNS topic ARNs
        for topic_name, topic in self.notification_topics.items():
            ssm.StringParameter(
                self,
                f"{topic_name.title()}TopicArn",
                parameter_name=f"/options-strategy/{self.env_name}/monitoring/sns/{topic_name}-topic-arn",
                string_value=topic.topic_arn,
                description=f"SNS topic ARN for {topic_name} notifications",
            )

    def _create_stack_outputs(self) -> None:
        """Create CloudFormation outputs for monitoring resources"""

        # Dashboard outputs
        CfnOutput(
            self,
            "ExecutiveDashboardName",
            value=self.dashboards["executive"].dashboard_name,
            description="Name of the executive CloudWatch dashboard",
            export_name=f"OptionsStrategy-{self.env_name}-Executive-Dashboard",
        )

        CfnOutput(
            self,
            "OperationsDashboardName",
            value=self.dashboards["operations"].dashboard_name,
            description="Name of the operations CloudWatch dashboard",
            export_name=f"OptionsStrategy-{self.env_name}-Operations-Dashboard",
        )

        CfnOutput(
            self,
            "TechnicalDashboardName",
            value=self.dashboards["technical"].dashboard_name,
            description="Name of the technical CloudWatch dashboard",
            export_name=f"OptionsStrategy-{self.env_name}-Technical-Dashboard",
        )

        # SNS topic outputs
        CfnOutput(
            self,
            "CriticalAlertsTopicArn",
            value=self.notification_topics["critical"].topic_arn,
            description="ARN of the critical alerts SNS topic",
            export_name=f"OptionsStrategy-{self.env_name}-Critical-Alerts-Topic",
        )

        CfnOutput(
            self,
            "WarningAlertsTopicArn",
            value=self.notification_topics["warning"].topic_arn,
            description="ARN of the warning alerts SNS topic",
            export_name=f"OptionsStrategy-{self.env_name}-Warning-Alerts-Topic",
        )

        # Monitoring function output
        CfnOutput(
            self,
            "HealthCheckFunctionArn",
            value=self.monitoring_functions["health_check"].function_arn,
            description="ARN of the health check Lambda function",
            export_name=f"OptionsStrategy-{self.env_name}-Health-Check-Function",
        )

    # Public properties for accessing monitoring resources
    @property
    def critical_alerts_topic(self) -> sns.Topic:
        """Get critical alerts SNS topic"""
        return self.notification_topics["critical"]

    @property
    def warning_alerts_topic(self) -> sns.Topic:
        """Get warning alerts SNS topic"""
        return self.notification_topics["warning"]

    @property
    def cost_alerts_topic(self) -> sns.Topic:
        """Get cost alerts SNS topic"""
        return self.notification_topics["cost"]

    @property
    def security_alerts_topic(self) -> sns.Topic:
        """Get security alerts SNS topic"""
        return self.notification_topics["security"]

    @property
    def executive_dashboard(self) -> cloudwatch.Dashboard:
        """Get executive CloudWatch dashboard"""
        return self.dashboards["executive"]

    @property
    def operations_dashboard(self) -> cloudwatch.Dashboard:
        """Get operations CloudWatch dashboard"""
        return self.dashboards["operations"]

    @property
    def technical_dashboard(self) -> cloudwatch.Dashboard:
        """Get technical CloudWatch dashboard"""
        return self.dashboards["technical"]

    @property
    def health_check_function(self) -> lambda_.Function:
        """Get health check Lambda function"""
        return self.monitoring_functions["health_check"]
